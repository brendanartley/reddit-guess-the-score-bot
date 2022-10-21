import requests
import json
import praw
from datetime import datetime, timedelta
import sys

"""
Script to make the initial guess the score comment where people make their guesses.
"""

OUR_TEAM_ID = '23'

def get_reddit_instance():
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
	return reddit

def get_comment_body(OUR_TEAM_ID, opponent_id):

	# Get opponent team names
	with open('./data/team_names.json') as f:
		r = json.loads(f.read())
		names = r[OUR_TEAM_ID] + r[opponent_id]

	# NOTE: This looks funny, but the body must be like this to correctly format on Reddit
	# Each line has two spaces at the end for line breaks as well
	body = '''# Pre-Game Guess The Score
***
**Reply to this comment** before puck drop to enter. Edited comments will be disqualified, and only one guess per person!  
&nbsp;  
*Format:* <Winner> <Winner's score>-<Loser's score>  
&nbsp;  
*Example:* Canucks 4-2  
&nbsp;  
*Accepted Names:* {}
'''.format(", ".join(names))
	return body

def get_opponent_id():
	# Check if our team has a game today
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}".format(OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API error - get_opponent_id")
		return None

	# Check there is a game today
	if r['totalGames'] == 0:
		return None

	# Access the other teams id
	if str(r['dates'][0]['games'][0]['teams']['home']['team']['id']) == OUR_TEAM_ID:
		opponent_id = r['dates'][0]['games'][0]['teams']['away']['team']['id']
	else:
		opponent_id = r['dates'][0]['games'][0]['teams']['home']['team']['id']

	return str(opponent_id)


def check_gts_comment_made_today():
	"""
	Check is comment GTS comment has already been made today. True -> "comment already made"
	"""

	with open('./data/last_gts_data.json', 'r') as f:
		last_gts_data = json.loads(f.read())
		last_comment = last_gts_data["last_gamethread_date"]

	today = (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d')
	if today == last_comment:
		return True
	return False

def check_gts_scored_today():
	"""
	Checks if GTS scores have been updated yet today. True == "already scored"
	"""
	with open('./data/last_gts_scored.json', 'r') as f:
		last_gts_data = json.loads(f.read())
		last_scored = last_gts_data["last_gts_scored_date"]

	today = (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d')
	if today == last_scored:
		return True
	return False

def get_game_thread(reddit):

	submission_date = None
	submission_id = None
	user = reddit.redditor("HockeyMod")

	for submission in user.submissions.new(limit=100):
		if submission.subreddit == 'canucks' and submission.link_flair_text == "GAME THREAD":
			submission_date = (datetime.fromtimestamp(submission.created_utc) - timedelta(hours=7)).strftime('%Y-%m-%d')
			submission_id = submission.id
			break

	if submission_date == None or submission_date != (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d'):
		submission_date = None
		print("No Game Thread Yet")

	return submission_date, submission_id

def make_comment(reddit, body, submission_id, submission_date):
	try:
		#TODO: add 'sticky=True' into the reply to sticky the comment
		comment = reddit.submission(submission_id).reply(body=body)
		with open('./data/last_gts_data.json', 'w') as f:
			data = {"last_gamethread_id": submission_id, "last_gamethread_date": submission_date, "last_gts_commend_id": comment.id}
			json.dump(data, f)
		print(" -- GTS Comment Successful -- ")

	except Exception as e:
		print(e)

def check_game_ended():
	"""
	Checks if the game has ended yet.
	'3' = 'Live'
	'7' = 'Final'
	'1' = 'Scheduled'
	"""

	today = (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d')
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?date={}&teamid={}".format(today, OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API error - check_game_ended")
		return False
	game_status = r['dates'][0]['games'][0]['status']['statusCode']
	if game_status == '7':
		return True
	return False

def get_guesses():
	#TODO: Fetch all the guesses from the first comment
	pass

def update_score():
	#TODO: Update the index page where all the scores are stored
	pass


def main():
	already_commented_today = check_gts_comment_made_today()
	already_calculated_score = check_gts_scored_today()
	opponent_id = get_opponent_id()

	if already_commented_today == True and already_calculated_score == True and opponent_id == None:
		return

	reddit = get_reddit_instance()
	submission_date, submission_id = get_game_thread(reddit)
	game_ended = check_game_ended()

	print(already_commented_today, opponent_id, submission_date, submission_id)

	# Checks made comment already, there is a game, and there is a gamethread
	if not submission_date:
		print("No Gamethread found")
		return

	# Make GTS Comment if not already
	if already_commented_today == False:
		submission_id = "y9arf7"
		body = get_comment_body(OUR_TEAM_ID, opponent_id)
		make_comment(reddit, body, submission_id, submission_date)
		return

	# Update scores if not already
	if already_commented_today == True and game_ended == True and already_calculated_score == False:
		pass


if __name__ == '__main__':
	main()
	pass