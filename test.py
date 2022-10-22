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

# Get HockeyMod (Game Bot)
# user = reddit.redditor("HockeyMod")
user = reddit.redditor("Hopeful_Swordfish382")
SUBMISSION_LIMIT=10
for submission in user.submissions.new(limit=SUBMISSION_LIMIT):
	print(submission.id, submission.title)

user = reddit.redditor("Hopeful_Swordfish382")
SUBMISSION_LIMIT=5
for comment in user.comments.new(limit=SUBMISSION_LIMIT):
	print(comment.id, comment.body[:10], comment.replies)

comment = reddit.comment(id="it2ste4")
comment.refresh()
for reply in comment.replies:
	print(reply.author, reply.body)

SUBMISSION_LIMIT=100
for sr in reddit.subreddit("canucks").hot(limit=SUBMISSION_LIMIT):
	print(sr.id, sr.title)


post = reddit.submission(id='y8z46n')

# it2ste4 - TESTING GUESS THE SCORE

# 3 = 'Live'
# 7 = 'Final'
# 1 = 'Scheduled'

# if __name__ == '__main__':
# 	main()
# 	pass