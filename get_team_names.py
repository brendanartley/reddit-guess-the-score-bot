import json
import requests
import sys
import os

"""
Script to get the teams names from the NHL API, and write them to a JSON file.
"""

def main():
	# Call NHL API
	r = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
	if not r.ok:
		sys.exit()

	# Parse team names
	team_names = {}
	for team in r.json()['teams']:
		arr = []
		for key in ['abbreviation', 'teamName', 'name']:
			arr.append(team[key].replace('\u00e9', 'e')) # 'Montréal Canadians' -> 'Montreal Canadiens'
		team_names[team['id']] = arr

	# Create directory if it does not exist
	data_path = "data"
	if not os.path.exists(data_path):
		os.makedirs(data_path)

	# Writing to file
	with open('./data/team_names.json', "w") as f:
		json.dump(team_names, f)
	
if __name__ == '__main__':
	main()