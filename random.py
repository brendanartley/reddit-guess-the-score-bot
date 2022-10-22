import requests
import json
import praw
import time
from datetime import datetime, timedelta

# Get Tokens
with open('./keyconfig.json') as keyconf:
	key_dict = json.loads(keyconf.read())

client_id = key_dict['client-id']
client_token = key_dict['client-token']
username = key_dict['username']
password = key_dict['password']

# Initialize PRAW objects
reddit = praw.Reddit(
	client_id=client_id,
	client_secret=client_token,
	user_agent="Hopeful_Swordfish382/0.1 by YourUsername",
	username=username,
	password=password
)

# Get most recent posts (submissions)
user = reddit.redditor("HockeyMod")
SUBMISSION_LIMIT=100
for submission in user.submissions.new(limit=SUBMISSION_LIMIT):
	if submission.subreddit == 'canucks' and submission.title.startswith("Post Game Thread:"):
		print(submission.id, submission.title)


# Get the most recent comments
user = reddit.redditor("Hopeful_Swordfish382")
SUBMISSION_LIMIT=5
for comment in user.comments.new(limit=SUBMISSION_LIMIT):
	if comment.body.startswith('# Pre-Game'):
		print(comment.id, comment.body[:10], comment.replies)

# Sometimes all the replies do not show up, .refresh() updates this
comment = reddit.comment(id="it2ste4")
comment.refresh()

# Iterate comment replies
for reply in comment.replies:
	print(reply.author, reply.body)