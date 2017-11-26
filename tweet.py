import os
from twitter import *
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

MY_TWITTER_CREDS = os.path.expanduser('~/.twitter_oauth')
if not os.path.exists(MY_TWITTER_CREDS):
    oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET, MY_TWITTER_CREDS)

oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)

twitter = Twitter(
    auth=OAuth(oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET))


def send_tweet(status):
    print("Tweet Sent:" + status)
    twitter.statuses.update(status=status)
