import os
import re

from allauth.socialaccount.models import SocialApp
from django.db.utils import ProgrammingError, OperationalError
import tweepy

# The regex used to identify quoted replies and tweets containing media
QUOTED_TWEET_REGEX = re.compile(r'(?P<t_co>\shttps:\/\/t.co\/)(?P<nonce>[a-zA-Z0-9]{0,15})', flags=re.M)

"""
An app must be created on Twitter before interacting with the API.

- See https://developer.twitter.com/en/docs/basics/getting-started
- See http://docs.tweepy.org/en/latest/getting_started.html
"""
try:
    TWITTER_SOCIAL_APP_OBJECT = SocialApp.objects.filter(provider='twitter').first()

    if TWITTER_SOCIAL_APP_OBJECT:
        CONSUMER_API_KEY = TWITTER_SOCIAL_APP_OBJECT.client_id
        CONSUMER_API_SECRET_KEY = TWITTER_SOCIAL_APP_OBJECT.secret
    else:
        CONSUMER_API_KEY = None
        CONSUMER_API_SECRET_KEY = None

except (SocialApp.DoesNotExist, ProgrammingError, OperationalError):
    TWITTER_SOCIAL_APP_OBJECT = None
    CONSUMER_API_KEY = os.environ.get("CONSUMER_API_KEY", None)
    CONSUMER_API_SECRET_KEY = os.environ.get("CONSUMER_API_SECRET_KEY", None)

AUTH = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET_KEY)
