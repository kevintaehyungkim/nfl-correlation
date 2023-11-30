import nfl_data_py as nfl

import sys
import math
import pprint

import numpy as np
import pandas as pd

from collections import defaultdict
from termcolor import colored, cprint



# relevant columns
columns = ['passer_player_name', 'receiver_player_name', 'posteam', 'defteam', 'season', 'week', 'play_type', 
           'yards_after_catch', 'complete_pass', 'qb_hit', 'sack','passing_yards']


# load NFL pbp data
pbp_raw = nfl.import_pbp_data([2023], columns)
pbp_records = pbp_raw.to_dict('records')


# util functions
def nested_dict():
    return defaultdict(nested_dict)



'''
nested key structure
--------------------
-> team 
 -> game
  -> 'pass' OR 'rec'
   -> player
    -> yards
'''
TEAM_GAME_YARDS = nested_dict()




nfl_stats = ["receiving_yds", "passing_yds"]




def corr_score(qb, rec): 

	'''
	https://www.datasciencecentral.com/choosing-the-correct-type-of-regression-analysis/#:~:text=Linear%20models%20are%20the%20most,first%20type%20you%20should%20consider.
	'''

	qb_recs, qb_yards = 0, 0 
	rec_recs, rec_yards = 0, 0

	growth_recs = {}
	growth_yards = {}

	for line in pbp_records:

		if line['play_type'] == 'pass' and line['complete_pass'] == 1.0:

			team, game = str(line['posteam']), str(line['nflverse_game_id'])
			passer, receiver = line['passer_player_name'], line['receiver_player_name']
			yards =  int(line['passing_yards'])

			if passer == qb:

				if game not in growth_recs:
					growth_recs[game] = {qb: [0], rec: [0]}
					growth_yards[game] = {qb: [0], rec: [0]}


				qb_game_recs = growth_recs[game][qb]
				qb_game_yards = growth_yards[game][qb]

				qb_curr_recs = qb_game_recs[-1]
				qb_curr_yards = qb_game_yards[-1]

				qb_game_recs.append(qb_curr_recs+1)
				qb_game_yards.append(qb_curr_yards+yards)

				growth_recs[game][qb] = qb_game_recs
				growth_yards[game][qb] = qb_game_yards


				curr_recs, curr_yards = growth_recs[game][rec][-1], growth_yards[game][rec][-1]

				if receiver == rec: 
					growth_recs[game][rec].append(curr_recs+1)
					growth_yards[game][rec].append(curr_yards+yards)

				else: 
					growth_recs[game][rec].append(curr_recs)
					growth_yards[game][rec].append(curr_yards)


	print(growth_recs)



	# qb_recs, qb_yards = 0, 0 
	# rec_recs, rec_yards = 0, 0

	# # for game in growth_yards:


	# qb_yards_end = []
	# rc_yards_end = []

	# qb_recs_sum = []
	# rc_recs_sum = []

	# # qb_recs_1std = []
	# # rc_recs_1std = []


	# for game in growth_yards:

	# 	qb_yards = growth_yards[game][qb]
	# 	rc_yards = growth_yards[game][rec]

	# 	qb_recs = growth_recs[game][qb]
	# 	rc_recs = growth_recs[game][rec]

	# 	# for qb_yard in qb_yards:

	# 	qb_yards_end.append(growth_yards[game][qb][-1])
	# 	rc_yards_end.append(growth_yards[game][rec][-1])

	# 	qb_recs_sum.append(qb_recs[-1])
	# 	rc_recs_sum.append(rc_recs[-1])


	# qb_yards_mean = round(np.mean(qb_yards_end), 1)
	# qb_yards_std = round(np.std(qb_yards_end), 1)

	# rc_yards_mean = round(np.mean(rc_yards_end), 1)
	# rc_yards_std = round(np.std(rc_yards_end), 1)


	# qb_recs_mean = round(np.mean(qb_recs_sum), 1)
	# qb_recs_std = round(np.std(qb_recs_sum), 1)

	# rc_recs_mean = round(np.mean(rc_recs_sum), 1)
	# rc_recs_std = round(np.std(rc_recs_sum), 1)













corr_score(sys.argv[1], sys.argv[2])




