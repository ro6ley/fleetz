from datetime import datetime, timedelta
import re

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.timezone import make_aware
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView

from allauth.socialaccount.models import SocialAccount, SocialToken
from background_task.models import Task
from tweepy.error import TweepError

from fleetz.forms import ProfileForm
from fleetz.models import FleetzUser, delete_tweet
from fleetz.core import TWEET_URL_REGEX


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


class ProfileFormView(LoginRequiredMixin, FormView):
    form_class = ProfileForm
    template_name = "fleetz/profile_form.html"
    success_url = "/profile/"


class DisconnectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if user_id := kwargs['user_id']:
            User.objects.get(id=user_id).delete()
            return HttpResponseRedirect('https://twitter.com/settings/applications/17228896')

        messages.error(self.request, 'Something went wrong. Try again.', extra_tags='danger')
        return HttpResponseRedirect(reverse('user_profile'))


class ScheduleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if request.POST.get('tweetUrl') and request.POST.get('twitterUsername'):

            if match := re.search(TWEET_URL_REGEX, request.POST['tweetUrl']):
                tweet_details = match.groupdict()

                if tweet_details['username'] == request.POST['twitterUsername']:
                    schedule_tweet(self.request, tweet_details['tweet_id'])

                elif tweet_details['username'] != request.POST['twitterUsername']:
                    messages.error(self.request, 'That is not your tweet.', extra_tags='danger')

            else:
                messages.error(self.request, 'Invalid tweet URL.', extra_tags='danger')
        else:
            messages.error(self.request, 'Something went wrong. Please try again.', extra_tags='danger')

        return HttpResponseRedirect(reverse('user_profile'))


class UnscheduleTweetView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if tweet_id := kwargs.get('tweet_id'):
            task = Task.objects.get(verbose_name=str(tweet_id))
            if task:
                task.delete()
                messages.success(self.request, 'Tweet removed from deletion schedule.')
            else:
                messages.error(self.request, 'Tweet not found.', extra_tags='danger')

        return HttpResponseRedirect(reverse('user_profile'))


class HomeView(TemplateView):
    """ This is the landing page of the application
    """
    template_name = "fleetz/home.html"


def schedule_tweet(request, tweet_id):
    """ This function takes in a single tweet id and schedules it's deletion.
    """
    try:
        tweet_task = Task.objects.get(verbose_name=tweet_id)
        messages.warning(request, 'Tweet is already scheduled for deletion.')

    except Task.DoesNotExist:
        fleetz_user = FleetzUser.objects.get(user=request.user)

        try:
            tweet = fleetz_user.api_object.get_status(tweet_id)

            deletion_time = tweet.created_at + timedelta(hours=fleetz_user.hours, minutes=fleetz_user.minutes)
            delete_tweet(request.user.id, tweet.id, schedule=make_aware(deletion_time), creator=request.user, verbose_name=tweet.id)

            messages.success(request, 'Tweet scheduled for deletion successfully.')

        except TweepError as e:
            msg = 'We ran into an error scheduling that tweet. Please check and try again'
            if e.response.status_code == 404:
                msg = 'Tweet not found. Please check and try again'

            messages.error(request, msg, extra_tags='danger')
