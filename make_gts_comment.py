import requests
import json
import praw
import time

"""
Script to make the initial guess the score comment where people make their guesses.
"""

OUR_TEAM_ID = '23'

def get_instance():
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

def check_opponent():
	# TODO: Get the opponent ID from NHL API, or from script checking schedule
	# check who the opponent is today
	pass

def main():

	reddit = get_instance()
	body = get_comment_body(OUR_TEAM_ID, '1')

	# reddit.submission('y8mm6d').reply(body=body)


if __name__ == '__main__':
	main()
	pass