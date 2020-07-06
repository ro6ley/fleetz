from datetime import datetime, timedelta
import logging
import os
import re

from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from background_task import background
from background_task.models import Task
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.dispatch import receiver
from django.utils.timezone import make_aware
import tweepy

from .core import AUTH, QUOTED_TWEET_REGEX


logger = logging.getLogger('fleetz')


class FleetzUser(models.Model):
    """ This model houses and handles a users Fleetz info.

    triggers: comma separated list of values to be used to delete tweets
    hours, minutes: time in hours or minutes to wait before deleting the tweet, based on the time it was posted
    tweets: comma separated list of tweets to be deleted.

    """
    user = models.OneToOneField(User, related_name='user_account', null=False, 
                                blank=False, on_delete=models.CASCADE, editable=False)
    hours = models.IntegerField(default=24, null=False, blank=False)
    minutes = models.IntegerField(default=24, null=False, blank=False)
    triggers = ArrayField(models.CharField(max_length=1, default="*"), size=5, default=['*','*'])

    @property
    def social_account(self):
        return SocialAccount.objects.get(user=self.user)

    @property
    def social_token(self):
        return SocialToken.objects.get(account=self.social_account)

    @property
    def api_object(self):
        # Configure user auth credentials
        ACCESS_TOKEN = self.social_token.token
        ACCESS_TOKEN_SECRET = self.social_token.token_secret
        AUTH.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        return tweepy.API(AUTH)

    @property
    def fetch_scheduled_tweets(self):
        """ This method returns the list of tweet objects scheduled for deletion
        from Twitter using Tweepy.
        """
        tweet_ids = [int(t.verbose_name) for t in Task.objects.filter(creator_object_id=self.user.id)]

        if tweet_ids:
            tweets_objs = self.api_object.statuses_lookup(tweet_ids)
            tweets = [t._json for t in tweets_objs]

            for t in tweets:
                created_at = datetime.strptime(t['created_at'], "%a %b %d %H:%M:%S %z %Y")
                task = Task.objects.filter(verbose_name=t['id']).first()
                t['created_at'] = created_at.isoformat()
                t['deleted_at'] = task.run_at.isoformat()

            return tweets

    def fetch_and_schedule_tweets(self):
        """ This function fetches a user's recent tweets and schedules their deletion

        Parameters
        ----------
        user_id : int, required
            the id of the Django user object

        TODO: is 25 tweets in the last hour enough or overkill?
        """
        def _filter_tweets(tweet):
            """ Use Regex to extract text from quoted replies, then proceed with the filtering
            """
            if str(tweet.id) not in scheduled_tweets and tweet.created_at >= since and tweet.text[:2] != 'RT':
                tweet.text = re.sub(QUOTED_TWEET_REGEX, '', tweet.text)
                return tweet

        scheduled_tweets = [t.verbose_name for t in Task.objects.filter(creator_object_id=self.user.id)]
        count = 0

        logger.info(f"Fetching tweets for user_id: {self.social_account.extra_data['screen_name']}")

        tweets = tweepy.Cursor(self.api_object.user_timeline).items(25)
        since = datetime.now() - timedelta(hours=settings.CRON_JOBS_INTERVALS_IN_HOURS)
        filtered_tweets = filter(_filter_tweets, tweets)

        for tweet in filtered_tweets:
            if any(trigger == tweet.text[-1] for trigger in self.triggers):
                # schedule tweets for deletion
                deletion_time = tweet.created_at + timedelta(hours=self.hours, minutes=self.minutes)
                delete_tweet(self.user.id, tweet.id, schedule=make_aware(deletion_time), creator=self.user, verbose_name=tweet.id)
                count += 1

        logger.info(f"Scheduled {count} of {self.social_account.extra_data['screen_name']}'s tweets for deletion'")


@background
def delete_tweet(user_id, tweet_id):
    """ This function deletes a single tweet. It runs as a background task.

    Parameters
    ----------
    user_id : int, required
        the user id of the tweet owner
    tweet_id : int, required
        the id of the tweet to be deleted
    """
    fleetz_user = FleetzUser.objects.get(user_id=user_id)
    fleetz_user.api_object.destroy_status(tweet_id)


@receiver(user_signed_up)
def handle_user_signed_up(sender, **kwargs):
    """ Create a new FleetzUser model for each user when they sign up.
    """
    if user := kwargs['user']:
        FleetzUser.objects.create(user=user)
