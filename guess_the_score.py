import requests
import json
import praw
from datetime import datetime, timedelta
import os
import sys

"""
Script that performs all the guess the score functionality. Needs to be ran ONCE a day AFTER the game day thread has been posted.
"""

def get_reddit_instance():
	"""
	Generates a PRAW Reddit class to interact with reddit

    Returns
    ---------
        reddit (Reddit): PRAW reddit class
		username (str): username of the bot account
	"""
	# Fetch secret tokens
	with open('./data/keyconfig.json') as keyconf:
		key_dict = json.loads(keyconf.read())
	client_id = key_dict['client-id']
	client_token = key_dict['client-token']
	username = key_dict['username']
	password = key_dict['password']

	# Initialize PRAW objects
	reddit = praw.Reddit(
		client_id=client_id,
		client_secret=client_token,
		user_agent="{}/0.1 by YourUsername".format(username),
		username=username,
		password=password
	)
	return reddit, username

def check_game_today(OUR_TEAM_ID):
	"""
	Checks if there is a game today and returns opponent id according to NHL API.
	If there is no game return False.

	Args
    ---------
        OUR_TEAM_ID (str): Our team id

	Returns
    ---------
        OPPONENT_ID (str | boolean): returns opponent id as string, or False if there is no game today
	"""
	# Checks if our team has a game today
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}".format(OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API Error: {}".format(r.status_code))
		return False
	
	# Check there is a game today
	if r['totalGames'] == 0:
		return False
	else:
		if str(r['dates'][0]['games'][0]['teams']['home']['team']['id']) == OUR_TEAM_ID:
			OPPONENT_ID = r['dates'][0]['games'][0]['teams']['away']['team']['id']
		else:
			OPPONENT_ID = r['dates'][0]['games'][0]['teams']['home']['team']['id']
		return str(OPPONENT_ID)

def get_game_thread(reddit):
	"""
	Finds the most recent game thread in the subreddit. HockeyMod posts game thread at 10am every game day (supposedly).
	
	Args
    ---------
        reddit (Reddit): PRAW reddit class

	Returns
    ---------
        submission_id (str | boolean): returns todays game thread identifier as string
	"""

	submission_id = None
	user = reddit.redditor("HockeyMod")
	for submission in user.submissions.new(limit=100):
		if submission.subreddit == 'canucks' and submission.link_flair_text == "GAME THREAD" and submission.title.startswith('Game Thread'):
			submission_id = submission.id
			break

	if submission_id == None:
		print("-- No Game Thread Found --")
		sys.exit()
	else:
		print("-- Game Thread Found -- id = \'{}\'".format(submission_id))

	return submission_id

def get_last_game_info(OUR_TEAM_ID):
	"""
	Gets the start time, and the score of the last game from our team.

	Args
    ---------
        OUR_TEAM_ID (str): Our team id

	Returns
    ---------
		last_game_start_time (datetime.datetime): time of puck drop in the last game
		last_game_score (tuple(int, int)): score of last game in the format (ourteam, opponent)
		LAST_GAME_OPPONENT_ID (str): the team id of our last opponent
	"""
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}&season=20222023".format(OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API error - check_game_ended")
		return False

	# Getting last game date
	today = datetime.today().date().strftime('%Y-%m-%d')
	for i in range(len(r['dates'])):
		if r['dates'][i]['date'] == today:
			break
	last_game_date = r['dates'][i-1]['date']

	# Getting last game start time and score
	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}&expand=schedule.linescore&date={}".format(OUR_TEAM_ID, last_game_date))
	if r.ok:
		r = r.json()
	else:
		print("NHL API error - check_game_ended")
		return False

	# Exact game start time
	s = r['dates'][0]['games'][0]['linescore']['periods'][0]['startTime']
	s = s.replace("T"," ").replace("Z", "")
	last_game_start_time = datetime.strptime(s, '%Y-%m-%d %H:%M:%S') - timedelta(hours=7) # UTC - PST

	# Getting game final score
	last_game_score = [0,0]
	if r['dates'][0]['games'][0]['teams']['home']['team']['id'] == int(OUR_TEAM_ID):
		last_game_score[0] = r['dates'][0]['games'][0]['teams']['home']['score']
		last_game_score[1] = r['dates'][0]['games'][0]['teams']['away']['score']
		LAST_GAME_OPPONENT_ID = r['dates'][0]['games'][0]['teams']['away']['team']['id']
	else:
		last_game_score[0] = r['dates'][0]['games'][0]['teams']['away']['score']
		last_game_score[1] = r['dates'][0]['games'][0]['teams']['home']['score']
		LAST_GAME_OPPONENT_ID = r['dates'][0]['games'][0]['teams']['home']['team']['id']

	return last_game_start_time, tuple(last_game_score), str(LAST_GAME_OPPONENT_ID)

def get_guesses(reddit, OUR_TEAM_ID, LAST_GAME_OPPONENT_ID, last_game_start_time, username):
	"""
	Collects all the valid guesses from the GTS comment.
	
	Args
    ---------
        reddit (Reddit): PRAW reddit class
        OUR_TEAM_ID (str): Our team id
        LAST_GAME_OPPONENT_ID (str): Opponents team id
		last_game_start_time (datetime.datetime): time of puck drop in last game
		username (str): username of the bot account

	Returns
    ---------
        guesses (arr[arr[str, tuple(int, int)]]): array of all guesses and their users that are in correct format
	"""

	# Get team names
	with open('./data/team_names.json', 'r') as f:
		r = json.loads(f.read())
		our_team_names = set([x.lower() for x in r[OUR_TEAM_ID]])
		opponent_team_names = set([x.lower() for x in r[LAST_GAME_OPPONENT_ID]])

	# Getting Last GTS comment
	user = reddit.redditor(username)
	SUBMISSION_LIMIT=50
	for comment in user.comments.new(limit=SUBMISSION_LIMIT):
		if comment.subreddit == 'canucks':
			break

	# comment = reddit.comment(id="it2ste4") # TESTING
	comment.refresh()
	guesses = []

	for reply in comment.replies:
		if reply.edited == True:
			print("Edited - ", reply.author.name, reply.body)
			continue

		# Skip if comment happened after puck drop
		if datetime.fromtimestamp(reply.created_utc) > last_game_start_time:
			print("After Puckdrop - ", reply.author.name, reply.body)
			continue

		# Guess preprocessing
		try:
			guess = reply.body.strip().split(" ", 1)
			team = guess[0].lower()
			score = tuple([int(x) for x in guess[1].replace(" ",'').split("-")])
			if len(score) != 2:
				continue
		except:
			print("Incorrect Format - ", reply.author.name, reply.body)
			continue
		
		# Add guess to array
		if team in our_team_names:
			guesses.append([reply.author.name, score])
		elif team in opponent_team_names:
			guesses.append([reply.author.name, score[::-1]])
		else:
			print("Wrong Team Format - ", reply.author.name, reply.body)
	return guesses


def update_scoreboard(reddit, guesses, game_score):
	"""
	Update GTS scoreboard (locally and on reddit wiki page).

	Args
    ---------
        reddit (Reddit): PRAW reddit class
        guesses (arr[arr[str, tuple(int, int)]]): array of all guesses and their users
		game_score (tuple(int, int)): score of last game in the format (ourteam, opponent)

	Returns
    ---------
        N/A
	"""
	# -- Update locally --
	# Creates File if not there
	if not os.path.exists('./data/gts_scores.json'):
		with open('./data/gts_scores.json', 'w') as f:
			json.dump({}, f)

	# Updates local scores file
	with open('./data/gts_scores.json', 'r+') as f:
		scores = json.loads(f.read())
		f.seek(0) # write at start of file

		for user, guess in guesses:
			if user not in scores:
				scores[user] = 0
			if guess == game_score:
				scores[user] += 1

		# Sort scores
		scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
		json.dump(scores, f)

	# -- Update Reddit Scoreboard --
	scoreboard = '|Username|Correct Guesses|\n:--|:--|\n'

	for user, score in scores.items():
		scoreboard += '|{}|{}|\n'.format(user, score)
	scoreboard = scoreboard.rstrip()

	reddit.subreddit('prawtestenv').wiki['index'].edit(content=scoreboard, reason="scoreboard_update")
	print("-- Updated Scoreboard --")

def get_last_gts_winners(guesses, game_score):
	"""
	Gets the winners from last games guess the score.

	Args
    ---------
        guesses (arr[arr[str, tuple(int, int)]]): array of all guesses and their users
        game_score (tuple(int, int)): score of last game in the format (ourteam, opponent)

	Returns
    ---------
        winners (arr[str]): array of all the users who had correct guesses
	"""
	winners = []
	for user, guess in guesses:
		if guess == game_score:
			winners.append(user)

	print("-- Got Last Game Winners --")
	return winners	

def get_comment_body(OUR_TEAM_ID, OPPONENT_ID, guesses, winners):
	"""
	Given our team id and the opponents id, returns the guess the score body text.

	Args
    ---------
		OUR_TEAM_ID (str): our team id
		OPPONENT_ID (str): opponent team id
        guesses (arr[arr[str, tuple(int, int)]]): array of all guesses and their users
		winners (arr[str]): array of all the users who had correct guesses

	Returns
    ---------
        body (str): Markdown for the reddit GTS comment
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
*Accepted Team Names:* {}  
&nbsp;  
***
Out of {} guesses last game. Congratulations to...\n  
'''.format(", ".join(team_names), len(guesses))

	if len(winners) == 0:
		body += "**Nobody!**"
	else:
		for user in winners:
			body += "/u/" + user + '  \n'

	return body

def make_comment(reddit, body, submission_id):
	"""
	Makes GTS comment in game thread.


	Args
    ---------
		reddit (Reddit): PRAW reddit class
		winners (arr[str]): array of all the users who had correct guesses in last game

	Returns
    ---------
        submission_id (str): todays game thread identifier as string
	"""
	try:
		comment = reddit.submission(submission_id).reply(body=body)
		try:
			comment.mod.distinguish(sticky=True) # only excecutes if account has moderator access
		except:
			print("-- Need mod access to sticky comment --")
		print(" -- GTS Comment Successful -- ")

	except Exception as e:
		print(e)
		print("-- GTS Comment Failed -- ")

def main():

	# Get IDs for game today if it exists
	OUR_TEAM_ID = '23'
	TODAY_OPPONENT_ID = check_game_today(OUR_TEAM_ID)

	# Stops execution if there is no game today
	if TODAY_OPPONENT_ID == False:
		print("-- No Game Today --")
		return
	else:
		print("-- Game Day -- OPPONENT_ID=\'{}\'".format(TODAY_OPPONENT_ID))

	# Get PRAW instance and id of game thread
	reddit, username = get_reddit_instance()
	gt_submission_id = get_game_thread(reddit)

	# Gets last games guesses
	last_game_start_time, last_game_score, LAST_GAME_OPPONENT_ID = get_last_game_info(OUR_TEAM_ID)
	#LAST_GAME_OPPONENT_ID = '999' # If you miss a game, you have to enter the team_id manually

	guesses = get_guesses(reddit, OUR_TEAM_ID, LAST_GAME_OPPONENT_ID, last_game_start_time, username)

	# Update scoreboard and get winners from last game
	update_scoreboard(reddit, guesses, last_game_score)
	winners = get_last_gts_winners(guesses, last_game_score)

	# Make today's guess the score post
	body = get_comment_body(OUR_TEAM_ID, TODAY_OPPONENT_ID, guesses, winners)
	make_comment(reddit, body, gt_submission_id)

if __name__ == '__main__':
	main()