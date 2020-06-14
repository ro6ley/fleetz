from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView

from allauth.socialaccount.models import SocialAccount, SocialToken
from background_task.models import Task

from .forms import ProfileForm
from .models import FleetzUser


class ProfileView(LoginRequiredMixin, FormView):
    """ This view allows a user to manage their profile, triggers and
    disconnect their Twitter account.
    """
    template_name = "fleetz/profile.html"
    form_class = ProfileForm
    success_url = "/profile/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_fleetz_details = FleetzUser.objects.get(user=self.request.user)
        user_social_account = user_fleetz_details.social_account
        user_social_token = user_fleetz_details.social_token
        context['form'] = ProfileForm(instance=user_fleetz_details)
        context['tweets'] = user_fleetz_details.fetch_scheduled_tweets

        context['user_extra_data'] = {
            'twitter_username': user_social_account.extra_data['screen_name'],
            'twitter_name': user_social_account.extra_data['name'],
            'bio': user_social_account.extra_data['description'],
            'profile_picture_url': user_social_account.extra_data['profile_image_url_https'],
            'profile_background_image_url': user_social_account.extra_data['profile_background_image_url_https'],
            'user_token': user_social_token.token,
            'user_token_secret': user_social_token.token_secret,
            'triggers': '|'.join(user_fleetz_details.triggers),
            'hours': user_fleetz_details.hours,
            'minutes': user_fleetz_details.minutes,
        }

        return context

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        fleetz_obj = FleetzUser.objects.get(user=self.request.user)
        if cleaned_data.get('hours') is not None:
            fleetz_obj.hours = form.cleaned_data['hours']
        if cleaned_data.get('minutes') is not None:
            fleetz_obj.minutes = form.cleaned_data['minutes']
        if cleaned_data.get('triggers'):
            fleetz_obj.triggers = form.cleaned_data['triggers']

        fleetz_obj.save()
        # messages: https://docs.djangoproject.com/en/2.2/ref/contrib/messages/#using-messages-in-views-and-templates
        messages.success(self.request, 'Details updated successfully.')

        return super().form_valid(form)


class ProfileFormView(FormView):
    form_class = ProfileForm
    template_name = "fleetz/profile_form.html"
    success_url = "/profile/"


class DisconnectView(View):
    def get(self, request, *args, **kwargs):
        if user_id := kwargs['user_id']:
            User.objects.get(id=user_id).delete()
            return HttpResponseRedirect('https://twitter.com/settings/applications/17228896')

        messages.error(self.request, 'Something went wrong. Try again.')
        return HttpResponseRedirect(reverse('user_profile'))


class UnscheduleTweetView(View):
    def get(self, request, *args, **kwargs):
        if tweet_id := kwargs.get('tweet_id'):
            task = Task.objects.get(verbose_name=str(tweet_id))
            if task:
                task.delete()
                messages.success(self.request, 'Tweet removed from deletion schedule.')
            else:
                messages.error(self.request, 'Tweet not found.')
        return HttpResponseRedirect(reverse('user_profile'))


class HomeView(TemplateView):
    """ This is the landing page of the application
    """
    template_name = "fleetz/home.html"
