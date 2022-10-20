import requests
import json
import praw
import time

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
user = reddit.redditor("HockeyMod")
subreddit = reddit.subreddit('test')

SUBMISSION_LIMIT=5
# Access 
for submission in user.submissions.new(limit=SUBMISSION_LIMIT):
	time_since_post = (time.time() - submission.created_utc)/60
	
	# Check submission made in 'canucks' subreddit
	# TODO: uncomment for realworld filters
	# if submission.subreddit == 'canucks' and time_since_post < 65:
	
	print(submission.title, submission.subreddit, submission.id)
	print("Mins since post: {:.2f}".format(time_since_post))

# if __name__ == '__main__':
# 	main()
# 	pass