import requests
import json
import praw
from datetime import datetime, timedelta

"""
Script that writes a comment to collect score guesses.

Frequency
- Once Daily
"""

def get_reddit_instance():
	"""
	Returns a PRAW reddit instance for the application to interact with reddit
	"""
	# Fetch secret tokens
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

def get_comment_body(OUR_TEAM_ID, OPPONENT_ID):
	"""
	Given our team id and the opponents id, returns the guess the score body text.
	"""

	with open('./data/team_names.json') as f:
		r = json.loads(f.read())
		team_names = r[OUR_TEAM_ID] + r[OPPONENT_ID]

	# NOTE: The indents look funny, but they must be like this for the body to format correctly on Reddit
	# Each line ends with two spaces for line breaks
	body = '''# Pre-Game Guess The Score
***
[View Scoreboard](https://www.reddit.com/r/prawtestenv/wiki/index/)  
&nbsp;  
**Reply to this comment** before puck drop to enter. Edited comments will be disqualified, and only one guess per person!  
&nbsp;  
*Format:* <Winner> <Winner's score>-<Loser's score>  
&nbsp;  
*Example:* Canucks 4-2  
&nbsp;  
*Accepted Names:* {}
'''.format(", ".join(team_names))
	return body

def check_game_today(OUR_TEAM_ID):
	"""
	Checks if there is a game today. If yes, returns opponent_id, otherwise False
	"""
	# Checks if our team has a game today
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}".format(OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API Error: {}".format(r.status_code))
		return False, False
	
	# Check there is a game today
	if r['totalGames'] == 0:
		return False, False
	else:
		if str(r['dates'][0]['games'][0]['teams']['home']['team']['id']) == OUR_TEAM_ID:
			OPPONENT_ID = r['dates'][0]['games'][0]['teams']['away']['team']['id']
		else:
			OPPONENT_ID = r['dates'][0]['games'][0]['teams']['home']['team']['id']
		return str(OPPONENT_ID)

def get_game_thread(reddit):

	submission_date = None
	submission_id = None
	user = reddit.redditor("HockeyMod")

	for submission in user.submissions.new(limit=100):
		if submission.subreddit == 'canucks' and submission.link_flair_text == "GAME THREAD" and submission.title.startswith('Game Thread'):
			submission_date = (datetime.fromtimestamp(submission.created_utc) - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
			print(submission.title, submission_date)
			submission_id = submission.id
			break

	if submission_date == None or submission_date != (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d'):
		submission_date = None
		print("-- No Game Thread Found --")

	return submission_date, submission_id

def make_comment(reddit, body, submission_id, submission_date):
	try:
		#TODO: add 'sticky=True' into the reply to sticky the comment
		comment = reddit.submission(submission_id).reply(body=body)
		try:
			comment.mod.distinguish(sticky=True)
		except:
			print("-- Need mod access to sticky comment --")

		with open('./data/gts_data.json', 'w') as f:
			data = {"last_game_thread_id": submission_id, "last_game_thread_date": submission_date, "last_gts_comment_id": comment.id}
			json.dump(data, f)
		print(" -- GTS Comment Successful -- ")

	except Exception as e:
		print(e)

def main():

	OPPONENT_ID = check_game_today()
	# OPPONENT_ID = '30' # FOR TESTING
	OUR_TEAM_ID = '23'

	if OPPONENT_ID == False:
		print("-- No Game Today --")
		return
	else:
		print("-- Game Day --")

	reddit = get_reddit_instance()
	submission_date, submission_id = get_game_thread(reddit)

	if not submission_date:
		print("-- No Game Thread found --")
		return

	# submission_id = "ya2maq" # FOR TESTING
	body = get_comment_body(OUR_TEAM_ID, OPPONENT_ID)
	make_comment(reddit, body, submission_id, submission_date)

if __name__ == '__main__':
	main()