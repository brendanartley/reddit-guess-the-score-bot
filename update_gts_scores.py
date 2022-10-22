import requests
import json
import praw
from datetime import datetime, timedelta
import os

"""
Script to update the GTS scoreboard, and comment on post game thread congratulating winners.

Frequency:
- Once daily at 11:00pm?
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

def get_post_game_thread(reddit):

	submission_date = None
	submission_id = None
	user = reddit.redditor("HockeyMod")

	for submission in user.submissions.new(limit=100):
		if submission.subreddit == 'canucks' and submission.link_flair_text == "GAME THREAD" and submission.title.startswith('Post Game Thread'):
			print(submission.title)
			submission_date = (datetime.fromtimestamp(submission.created_utc) - timedelta(hours=7)).strftime('%Y-%m-%d')
			submission_id = submission.id
			break

	if submission_date == None or submission_date != (datetime.utcnow() - timedelta(hours=7)).strftime('%Y-%m-%d'):
		submission_date = None
		print("-- No Post Game Thread Found --")

	return submission_date, submission_id

def check_game_ended(OUR_TEAM_ID):
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

def get_guesses(reddit, OUR_TEAM_ID, OPPONENT_ID):
	"""
	Collects all the valid guesses from the GTS comment.
	"""

	# Get comment_id
	with open('./data/gts_data.json', 'r') as f:
		gts_data = json.loads(f.read())
		gts_comment_id = gts_data["last_gts_comment_id"]

	# Get team names
	with open('./data/team_names.json', 'r') as f:
		r = json.loads(f.read())
		our_team_names = set([x.lower() for x in r[OUR_TEAM_ID]])
		opponent_team_names = set([x.lower() for x in r[OPPONENT_ID]])

	comment = reddit.comment(id="it2ste4")
	comment.refresh()
	guesses = []

	for reply in comment.replies:
		if reply.edited == True:
			continue
		
		#TODO: Check comment happened before puck drop
		# if reply.created_utc < GAMESTART:
		# 	continue

		# Guess preprocessing
		try:
			guess = reply.body.strip().split(" ", 1)
			team = guess[0].lower()
			score = tuple([int(x) for x in guess[1].replace(" ",'').split("-")])
			if len(score) != 2:
				continue
		except:
			continue
		
		# Add guess to array
		if team in our_team_names:
			guesses.append([reply.author.name, score])
		elif team in opponent_team_names:
			guesses.append([reply.author.name, score[::-1]])

	return guesses

def get_game_score(OUR_TEAM_ID, OPPONENT_ID):

	r = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?teamId={}&date=2022-10-20".format(OUR_TEAM_ID))
	if r.ok:
		r = r.json()
	else:
		print("NHL API error - check_game_ended")
		return False

	score = [0,0]
	if r['dates'][0]['games'][0]['teams']['home']['team']['id'] == int(OUR_TEAM_ID):
		score[0] = r['dates'][0]['games'][0]['teams']['home']['score']
		score[1] = r['dates'][0]['games'][0]['teams']['away']['score']
	else:
		score[0] = r['dates'][0]['games'][0]['teams']['away']['score']
		score[1] = r['dates'][0]['games'][0]['teams']['home']['score']

	return tuple(score)

def update_scoreboard(reddit, guesses, game_score):
	"""
	Update GTS scoreboard (locally and on reddit wiki page).
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

def pgt_winners(submission_id):
	#TODO:
	# -- Congratulations Post on Game Thread --
	pass

def main():

	# OPPONENT_ID = check_game_today()
	OPPONENT_ID = '30' # FOR TESTING
	OUR_TEAM_ID = '23'

	if OPPONENT_ID == False:
		print("-- No Game Today --")
		return

	reddit = get_reddit_instance()

	gt_submission_date, gt_submission_id = get_game_thread(reddit)
	pgt_submission_date, pgt_submission_id = get_post_game_thread(reddit)

	# submission_id = 'ya2maq' # FOR TESTING

	guesses = get_guesses(reddit, gt_submission_id, OUR_TEAM_ID, OPPONENT_ID)
	game_score = get_game_score(OUR_TEAM_ID, OPPONENT_ID)
	update_scoreboard(reddit, guesses, game_score)

if __name__ == '__main__':
	main()
	pass