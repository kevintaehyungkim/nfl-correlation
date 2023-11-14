
import nfl_data_py as nfl

import math
import pprint

import numpy as np
import pandas as pd

from collections import defaultdict
from termcolor import colored, cprint

'''
reqs
----
pip install nfl_data_py
pip install termcolor
'''


MIN_YARD_AVG = 10
MIN_REC_AVG = 1


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



'''
process each play and create map of team yards (pass or rec) per game
'''
for line in pbp_records:

	if line['play_type'] == 'pass' and line['complete_pass'] == 1.0:

		team = str(line['posteam'])
		game = str(line['nflverse_game_id'])
		passer = line['passer_player_name']
		receiver = line['receiver_player_name']
		yards = line['passing_yards']

		if not TEAM_GAME_YARDS[team][game]['pass']:
			TEAM_GAME_YARDS[team][game]['pass'] = nested_dict()

		if not TEAM_GAME_YARDS[team][game]['rec']:
			TEAM_GAME_YARDS[team][game]['rec'] = nested_dict()

		# rec yards + receptions
		if TEAM_GAME_YARDS[team][game]['rec'][receiver]:
			TEAM_GAME_YARDS[team][game]['rec'][receiver][0] += int(yards)
			TEAM_GAME_YARDS[team][game]['rec'][receiver][1] += 1
		else:
			TEAM_GAME_YARDS[team][game]['rec'][receiver] = [int(yards), 1]

		# pass yards + completions
		if TEAM_GAME_YARDS[team][game]['pass'][passer]:
			TEAM_GAME_YARDS[team][game]['pass'][passer][0] += int(yards)
			TEAM_GAME_YARDS[team][game]['pass'][passer][1] += 1
		else:
			TEAM_GAME_YARDS[team][game]['pass'][passer] = [int(yards), 1]



'''
team game log
'''
def game_log(team):
	print('\n')
	print(colored('[TEAM - ' + team + ']', 'yellow'))
	
	game_log = TEAM_GAME_YARDS[team] 
	
	for game in game_log:
		print('\n')
		print(colored(game, 'blue'))

		print('[P] ' + str(dict(game_log[game]['pass'])))
		print('[R] ' + str(dict(game_log[game]['rec'])))

	print('\n')




# UTIL FUNCTIONS #

def above_count(player_yards, val):
	count = 0
	for y in player_yards:
		if y >= val:
			count += 1
	return count


def yard_share(rec_yards, pass_yards):
	return round(rec_yards/pass_yards, 4)


def print_header(category, color):
	print(colored(category, color))


def statline(stat, val):
	return colored(' ' + stat + ' ', 'white') + colored(str(val), 'yellow')


def subline(stat, col):
	return colored(' ' + stat, col)


def val_str(num):
	if num >= 0:
		return colored(str(num), 'green')
	return colored(str(num), 'red')


def num_str(num):
	return colored(str(num), 'yellow')

def pad_str(str, num):
	if len(str) >= num:
		return str

	return str + ' '*(num-len(str))


'''
-----
TO-DO
-----
- find rough calculations on how one player performing above or beyond mean affects other receivers
- mean reception and num receptions in between games + avg reception yard
- find line ranges where lines are ideal to take based on avg. reception yard and stdev
- take into account correlation performances when losing/low yards + winning/high yards
- adjust any formula scales needed to return ratios more closely matching sportsbooks
'''
def correlation_all():

	team_data = []
	for team in TEAM_GAME_YARDS.keys():

		game_log = TEAM_GAME_YARDS[team] 

		qb_yards = []
		qb_key = ''
		
		r_yards = defaultdict(list)
		r_receptions = defaultdict(list)
		r_data = defaultdict()

		for game in game_log.keys():

			qb_list = list(game_log[game]['pass'].keys())

			if len(qb_list) > 1: 
				continue

			qb_key = qb_list[0]
			pass_yards = game_log[game]['pass'][qb_key][0]
			pass_completions = game_log[game]['pass'][qb_key][1]

			qb_yards.append(pass_yards)

			for receiver in game_log[game]['rec']:
				rec_data = game_log[game]['rec'][receiver]

				r_yards[receiver].append(rec_data[0])
				r_receptions[receiver].append(rec_data[1])

		qb_yards_mean = round(np.mean(qb_yards), 2)
		qb_yards_std = round(np.std(qb_yards), 2)

		for receiver in r_yards.keys():

			yards_mean = round(np.mean(r_yards[receiver]), 2)
			yards_std = round(np.std(r_yards[receiver]), 2)
			num_games = len(r_yards[receiver])

			# filter for most consistently best-performing receivers
			min_yards = 45
			min_games = 4
			max_stdev = 0.65

			if yards_mean > min_yards and yards_std < max_stdev*yards_mean and num_games > min_games:

				# correlation score per game
				corr_games = []

				rec_game_yards = r_yards[receiver]
				num_games = len(rec_game_yards)

				for i in range(num_games):
					qb_diff = round(qb_yards[i]-qb_yards_mean)
					rec_diff = round(rec_game_yards[i]-yards_mean)

					qb_diff_norm = round(qb_diff/qb_yards_mean, 4)
					rec_diff_norm = round(rec_diff/yards_mean, 4)

					qb_diff_norm_str = val_str(qb_diff_norm)
					rec_diff_norm_str = val_str(rec_diff_norm)

					diff_low = min(abs(qb_diff_norm), abs(rec_diff_norm))
					diff_dist = abs(rec_diff_norm - qb_diff_norm)

					print('[QB] ' + colored(str(qb_yards[i]), 'yellow') + ' yards -> ratio (mean diff/pass yards): ' + qb_diff_norm_str)
					print('[RC] ' + colored(str(rec_game_yards[i]), 'yellow') + ' yards -> ratio (mean diff/rec yards): ' + rec_diff_norm_str)
					print('----------------')

					low_scl = (0.75+diff_low)**2
					print('low_scl: ' + str(round(low_scl, 4)))

					corr = 100
					
					if qb_diff_norm*rec_diff_norm >= 0: 
						dist_scl = 2/(2+diff_dist)
						mean_diff_adj = low_scl*dist_scl
						corr *= mean_diff_adj
						corr *= 1.25

						print('dist_scl: ' + str(round(dist_scl,4)))

					else: 
						dist_scl = (2+diff_dist)/2
						mean_diff_adj = low_scl*dist_scl
						corr *= mean_diff_adj
						corr *= -1.15

						print('dist_scl: ' + str(round(dist_scl,4)))

					print('----------------')
					print('diff adj: ' + str(round(mean_diff_adj,4)))

					# adjust corr according to rec/pass yards and rec yards
					pass_adj = math.log(abs(249.99-qb_yards[i]), 100)
					rec_adj = math.log(1+abs(rec_game_yards[i]), 49.99)
					adj = 0.01 + (pass_adj / rec_adj)

					corr *= adj
					corr_games.append(round(corr, 2))

					print('yard adj: ' + str(round(adj,4)))
					print('----------------')
					print('corr: ' + colored(str(round(corr,4)), 'yellow'))
					print('\n')


				corr_mean = np.mean(corr_games)

				corr_score, pos_corr_count = 0, 0

				streak_bonus = 1.1
				streak_dir, streak_count = 0, 0
				max_streak = 0

				for corr in corr_games: 

					if corr >= 0: 
						if streak_dir >= 0:
							streak_count += 1
						else:
							streak_count = 0
							streak_dir = 0

						pos_corr_count += 1
						corr_score += math.log(corr, 1.5)
					
					else: 

						if streak_dir < 0:
							streak_count += 1
						else:
							streak_count = 0
							streak_dir = 0

						corr_score -= math.log(abs(corr), 1.5)


					max_streak = max(max_streak, streak_count)

				raw_corr_score = round(corr_score/num_games, 4)

				print(colored('corr log: ', 'magenta') + str(corr_games))
				print(colored('raw_corr_score: ', 'magenta') + str(raw_corr_score))

				# streak + positive correlation scaling
				streak_fact = streak_bonus ** max_streak
				pos_corr_fact = (num_games+pos_corr_count)/(2*num_games)

				# stdev scaling
				std_scl = yards_mean/(yards_mean+(1.5*yards_std))
				std_scl = std_scl**2

				# yard amt scaling
				yard_mean_scl = math.log(yards_mean, 10)

				# yard share scaling
				yard_share_scl = yard_share(yards_mean, qb_yards_mean)/0.3

				perf_score = 10*yard_share_scl

				corr_score = round(4*(raw_corr_score * streak_fact * pos_corr_fact * std_scl * yard_mean_scl) + 2*perf_score, 2)

				print(colored('adj_corr_score: ', 'magenta') + str(corr_score))
				print('\n')



				team_data.append([yards_mean, yards_std, qb_yards_mean, qb_yards_std, num_games, team, qb_key, receiver, corr_score, corr_games, r_yards[receiver], qb_yards])


	sort_key = lambda x: (-1*x[8], x[0]/x[1], -1*x[2])
	sorted_team_data = sorted(team_data, key=sort_key)

	for d in sorted_team_data:
		print('\n')
		print(colored('=============================================', 'white'))
		print(colored('[' + d[5] + '] ', 'white') + colored(d[6], 'yellow') + ' + ' + colored(d[7], 'yellow') + colored(' | Correlation: ', 'white') + colored(str(d[8]), 'magenta'))
		print(colored('=============================================', 'white'))
		# print(colored(' Avg Yard Share: ', 'white') + colored(str(round((d[0]/d[2])*100, 2)) + ' %', 'magenta'))
		
		# Yards
		# print(colored('             ', 'white'))
		print(colored('> Yards - ' + colored(str(round((d[0]/d[2])*100, 2)) + ' %', 'white') + '', 'white'))
		print(colored(' ----------------', 'white'))

		print(colored('  ', 'white') + colored(d[6], 'yellow') + ' | mean: ' + num_str(d[2]) + ' stdev: ' + num_str(d[3]) + ' (' +str(d[4]) +' games)')
		# print('mean: ' + num_str(d[2]) + ' stdev: ' + num_str(d[3]) + ' (' +str(d[4]) +' games)')


		print(colored('  ', 'white') + colored(d[7], 'yellow') + ' | mean: ' + num_str(d[0]) + ' stdev: ' + num_str(d[1]) + ' (' +str(d[4]) +' games)')
		# print(colored(' ', 'white') + ' ' + colored(str(d[9]), 'cyan'))

		# Correlation
		print(colored('             ', 'white'))
		print(colored('> Correlation', 'white'))
		print(colored(' ------------', 'white'))

		rc_yards, rc_yards_mean = d[10], d[0]
		qb_yards, qb_yards_mean = d[11], d[2]

		for i in range(len(rc_yards)):

			qb_diff = qb_yards[i]-qb_yards_mean

			qb_diff_str = colored('  [QB] ' + colored(str(qb_yards[i]), 'yellow') + colored(' | ', 'white'), 'white')
			rec_diff_str = colored(' [REC] ' + colored(str(rc_yards[i]), 'yellow') + colored(' | ', 'white'), 'white')
			padding = ''

			if qb_diff >= 0: 
				qb_diff_val = '+' + str(round(qb_diff, 2))
				qb_diff_str += colored(qb_diff_val, 'green')

				padding = ' '*(18 - len(' [REC] ') - len(qb_diff_val))

			else:
				qb_diff_val = str(round(qb_diff, 2))
				qb_diff_str += colored(qb_diff_val, 'red')

				padding =  ' '*(18 - len(' [REC] ') - len(qb_diff_val))


			rec_diff =  rc_yards[i]-rc_yards_mean
			if rec_diff >= 0: 
				rec_diff_str += colored('+' + str(round(rec_diff, 2)), 'green')
			else:
				rec_diff_str += colored(str(round(rec_diff, 2)), 'red')


			print(qb_diff_str + padding + rec_diff_str)

		print(colored('             ', 'white'))
		print(colored('> Correlation Log', 'white'))
		print(' ----------------')
		print(colored(' ', 'white') + colored(str(d[9]), 'white'))

	print('\n')

	return sorted_team_data





def team_data(team, qb):
	game_log = TEAM_GAME_YARDS[team] 

	receivers = set()
	qb_yards = []
	player_yards = defaultdict(list)
	player_receptions = defaultdict(list)

	player_yard_dist = defaultdict(list)
	player_rec_dist = defaultdict(list)

	for game in game_log.keys():

		if qb not in game_log[game]['pass']:
			continue

		pass_yards = game_log[game]['pass'][qb][0]
		pass_completions = game_log[game]['pass'][qb][1]

		qb_yards.append(pass_yards)

		for receiver in game_log[game]['rec']:
			receivers.add(receiver)
			rec_data = game_log[game]['rec'][receiver]

			player_yards[receiver].append(rec_data[0])
			player_receptions[receiver].append(rec_data[1])

			# print(rec_data[0])
			# print(game_log[game]['pass']['B.Young'][0])

			rec_yards = rec_data[0]


			player_yard_dist[receiver].append(rec_data[0]/pass_yards)
			player_rec_dist[receiver].append(rec_data[1]/pass_completions)


	qb_yards_mean = np.mean(qb_yards)
	print('\n')

	for rcvxd in sorted(player_yards.items(), key=lambda kv: np.mean(kv[1]), reverse=True):

		rcv = rcvxd[0]

		mean_yard_dist = np.mean(player_yard_dist[rcv])
		mean_rec_dist = np.mean(player_rec_dist[rcv])


		yard_dist_std = np.std(player_yard_dist[rcv])
		rec_dist_std = np.std(player_rec_dist[rcv])

		mean_yards = np.mean(player_yards[rcv])
		yards_var = np.std(player_yards[rcv])
		
		mean_recs = np.mean(player_receptions[rcv])
		recs_var = np.std(player_receptions[rcv])

		if mean_yards > MIN_YARD_AVG and mean_recs > MIN_REC_AVG:

			rcv_yard_share = colored ('  Avg Distr: ', 'white') + colored(str(round(mean_yard_dist*100, 2)), 'yellow') + colored(' % ', 'yellow')
			# rcv_yard_share += colored(' stdev: ' + colored(str(round(yard_dist_std*100, 2)), 'yellow'), 'white') + colored(' % ', 'yellow')

			rcv_rec_share = colored ('  Avg Distr: ', 'white') + colored(str(round(mean_rec_dist*100, 2)), 'yellow') + colored(' % ', 'yellow')
			# rcv_rec_share += colored(' stdev: ' + colored(str(round(rec_dist_std*100, 2)), 'yellow'), 'white') + colored(' % ', 'yellow')

			print('\n')
			print(colored('[' + team + '] ' + rcv, 'blue'))


			# Receiving Yards
			print(colored('  ---------------', 'white'))
			print_header('  Receiving Yards', 'white')
			print(colored('  ---------------', 'white'))
			print(statline(' Mean:', round(mean_yards, 2)) + ' stdev: ' + colored(str(round(yards_var, 3)), 'yellow') + colored(' ', 'yellow'))
			print(rcv_yard_share)

			vals = [25, 40, 50, 60, 75, 100]
			range_str = colored('  ', 'white')

			for val in vals:
				count = above_count(player_yards[rcv], val)
				target_str = colored('[' + str(val) + '+] ', 'white')
				hit_rate_str = colored(str(count) + '/' + str(len(player_yards[rcv])), 'cyan')
				range_str += target_str + hit_rate_str + ' '
			print(range_str)
		

			# Receptions
			print('  ----------')
			print_header('  Receptions', 'white')
			print('  ----------')

			rcv_rec_statline = statline(' Mean:', round(mean_recs, 2)) + statline('stdev', round(recs_var, 3))
			print(rcv_rec_statline)
			print(rcv_rec_share)


			# Correlation
			print(colored('  -----------', 'white'))
			print(colored('  Correlation', 'white'))
			print(colored('  -----------', 'white'))


			for i in range(len(rcvxd[1])):

				qb_diff = qb_yards[i]-qb_yards_mean
				if qb_diff >= 0: 
					qb_diff = colored('+' + str(round(qb_diff, 2)), 'green')
				else:
					qb_diff = colored(str(round(qb_diff, 2)), 'red')

				rec_diff =  rcvxd[1][i]-mean_yards
				if rec_diff >= 0: 
					rec_diff = colored('+' + str(round(rec_diff, 2)), 'green')
				else:
					rec_diff = colored(str(round(rec_diff, 2)), 'red')


				print('  [QB] ' + qb_diff + ' [REC] ' + str(rec_diff) )



# OUTPUT #

# team_data('DEN', 'R.Wilson')
# team_data('CIN', 'J.Burrow')

correlation_all()

# team_data('BUF', 'J.Allen')

