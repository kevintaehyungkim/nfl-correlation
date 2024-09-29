
import math
import pprint
import json

import numpy as np
import pandas as pd

import requests
from datetime import date


from collections import defaultdict
from termcolor import colored, cprint


def nested_dict():
	return defaultdict(nested_dict)

def format_str(s1, s2, space):
	space_str = ' ' * (space-len(s1))
	return s1 + space_str + s2

def format_name(input_str):
	# Split the input string into first and last names
	input_split = input_str.split(' ')
	first_name, last_name = input_split[0], input_split[1]
	
	# Capitalize the first letter of the first name
	first_initial = first_name[0].upper()
	
	# Format the output as "FirstInitial.LastName"
	formatted_name = f"{first_initial}.{last_name}"
	
	return formatted_name

# Function to load JSON data from a file
def load_json(filename):
	try:
		with open(filename, 'r') as file:
			data = json.load(file)
		return data
	except FileNotFoundError:
		print(f"Error: The file {filename} was not found.")
		return None
	except json.JSONDecodeError:
		print("Error: The file could not be decoded. Please check the file format.")
		return None



ud_nfl = defaultdict()
nfl_stats = {'receiving_yds', 'rushing_yds', 'passing_yds'}


def extract_ud_nfl():
	for line in lines:

		if line['over_under']['appearance_stat'] and line['over_under']['appearance_stat']['stat'] in nfl_stats and line['status'] == 'active' and '+' not in line['over_under']["title"]:

			stat = line['over_under']['appearance_stat']['stat']
			val = line['stat_value']
			title = line['over_under']['title'].split(' ')
			player = title[0][0] + '.' + title[1]

			# print(player)

			if player in ud_nfl.keys():
				ud_nfl[player][stat] = val
			else:
				ud_nfl[player] = {stat: val}
				# ud_nfl[player][stat] = val

	today = date.today()
	curr_date = str(today.strftime("%m-%d-%y"))
	file_name = curr_date + '.txt'

	output = open(file_name, "w")

	for k, v in ud_nfl.items():
		output.writelines(f'{k} {v}\n')
		  
	return ud_nfl




filename = 'game_stats_2024.json'
TEAM_GAME_YARDS = dict(load_json(filename))

PLAYER_STATS = nested_dict()

for team in TEAM_GAME_YARDS.keys():
	for game in TEAM_GAME_YARDS[team]:

		opp = game.split('v')[1]

		for key in TEAM_GAME_YARDS[team][game]:
			for player in TEAM_GAME_YARDS[team][game][key]:

				game_stats = TEAM_GAME_YARDS[team][game][key][player]
				player_formatted = format_name(player)

				if player_formatted in PLAYER_STATS:

					PLAYER_STATS[player_formatted][key].append((game_stats, opp))

				else: 
					PLAYER_STATS[player_formatted] = nested_dict()
					PLAYER_STATS[player_formatted]['pass'] = []
					PLAYER_STATS[player_formatted]['rec'] = []
					PLAYER_STATS[player_formatted]['rush'] = []
					PLAYER_STATS[player_formatted]['team'] = str(team)

					PLAYER_STATS[player_formatted][key] = [[game_stats, opp]]

# print(PLAYER_STATS)


# retrieve UD lines 
r = requests.get("https://api.underdogfantasy.com/beta/v3/over_under_lines")
lines = []

try:
	lines = r.json()["over_under_lines"]
except: 
	"no underdog lines"


ud_conversion = {'receiving_yds': 'rec', 'rushing_yds': 'rush', 'passing_yds': 'pass'}
ud_projections = extract_ud_nfl()


# print(ud_projections)

for player in PLAYER_STATS:     
	if player in ud_projections:
		
		ud_stat = list(ud_projections[player].keys())[0]
		ud_val = ud_projections[player][ud_stat]

		stat_key = ud_conversion[ud_stat]

		# print(PLAYER_STATS[player][stat_key])
		team = PLAYER_STATS[player]['team']

		print('\n')
		ud_line = str('[' + team + ']' + ' ' + player + ' ' + ud_stat + ' ' +  ud_val)
		print(colored(ud_line, 'yellow'))

		for game_stat in PLAYER_STATS[player][stat_key]:
			game_str = format_str(str(game_stat[0]), 'vs. ' + game_stat[1], 10)
			print(game_str)

		# print(PLAYER_STATS[player][stat_key])