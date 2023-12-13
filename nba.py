
'''
line - 12.5 

last 3 avg -> 14.66

last 13 avg -> 14.2

12.4 + 0.67 + 0.67 + 1.848 - 2*0.4854 + 0 

-> 14.6172
'''
import math
import requests
import time

import pandas as pd

from collections import defaultdict
from datetime import date


from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.static import players

from termcolor import colored, cprint

from plotly.subplots import make_subplots

import plotly.graph_objects as go
import plotly.io as pio


nba_stats = ["Pts + Rebs + Asts", "Points + Assists", "Points + Rebounds", "Points", "Rebounds", "Assists"]


def extract_ud_nba():

	ud_nba = defaultdict()
	
	res = requests.get("https://api.underdogfantasy.com/beta/v3/over_under_lines")
	lines = res.json()["over_under_lines"]

	for line in lines:

		if line['over_under']['appearance_stat'] and line['over_under']['appearance_stat']['display_stat'] in nba_stats and line['status'] == 'active':

			stat = line['over_under']['appearance_stat']['display_stat']
			val = line['stat_value']
			title = line['over_under']['title'].split(' ' + stat)
			player = title[0]

			if player in ud_nba.keys():
				ud_nba[player][stat] = float(val)
			else:
				ud_nba[player] = {stat: float(val)}


	today = date.today()
	curr_date = 'nba-' + str(today.strftime("%m-%d-%y"))
	file_name = curr_date + '.txt'

	output = open(file_name, "w")

	for k, v in ud_nba.items():
		output.writelines(f'{k} {v}\n')

	return ud_nba




def find_ud_lines():

	ud_nba = extract_ud_nba()

	# filter for nba players and stats 
	ud_players = list(ud_nba.keys())
	nba_players = players.get_players()

	for player_name in ud_players:

		player_lines = ud_nba[player_name]

		try:

			# print(nba_players)

			player_info = next((x for x in nba_players if x.get("is_active") == True and x.get("full_name") == player_name), None)

			# print(player_info)

			player_id = player_info.get("id")
			player_team = player_info.get("team")

			ud_nba[player_name]['*player_id'] = player_id
			ud_nba[player_name]['*player_team'] = player_team

		except:

			del ud_nba[player_name]
			continue



	for ud_player in ud_nba.keys():

		# print(ud_player)

		try:

			# print('=============================================')

			player_id = ud_nba[ud_player]['*player_id']
			# player_team = ud_nba[ud_player]['*player_team']


			game_log_pd = pd.concat(playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames())
			game_log = game_log_pd.to_dict('records')

			last_21_games = game_log[0:21]
			games_21 = defaultdict(list)

			for i in range(len(last_21_games)):

				game = last_21_games[i]

				# if 'PR' not in last_21_game_data: last_21_game_data['PR'] =
				# DREB/OREB

				games_21['Points'].append(game['PTS'])
				games_21['Assists'].append(game['AST'])
				games_21['Rebounds'].append(game['REB'])
				# games_21['FGM'].append(game['FGM'])
				# games_21['FGA'].append(game['FGA'])


				# x_vals = []

				# for i in range(21):
				# 	x_vals.append(i)


				# fig.add_trace(go.Scatter(
				#     x= x_vals, y=games_21['Points'],
				#     line_color='rgba(108,189,191,0.1)',
				# 	mode='lines',
				#     line = dict(shape = 'linear', color = 'orange', width= 1),
				#     # marker=dict(symbol="diamond", size=4)
				# 	), 
				# 	row=1, col=1
				# )

				# fig.show()


			ud_lines = ud_nba[ud_player]

			for ud_stat in ud_lines:

				# if 

				# ud_stat = 'Points'
				# ud_val = 5.5

				ud_val = ud_lines[ud_stat]

				# print(ud_val)

				if ud_stat[0] != '*':


					# print(ud_stat, )
					stats = ud_stats(ud_stat)

					proj = 0
					avg = 0 
					std8 = 0

					hits = 0

					line_dir = ''
					recent = []

					for s in stats:

						stat_proj, last_8, mean_3, mean_13, med_13, stdev_8 = calculate_projection(games_21, s)

						proj += stat_proj
						avg += mean_13
						std8 += stdev_8

						recent.append([s, last_8])

					if len(recent) >= 2:

						total = []

						for i in range(len(recent[0][1])):

							curr = 0 

							for j in range(len(recent)):

								curr += recent[j][1][i]

							total.append(curr)

						recent.append(['Total', total])

					print(ud_player, ud_stat, proj)

					if abs(proj-ud_val) > min_threshold(ud_val): 

						cond_met = False

						if proj > ud_val:
							line_dir = 'OVER'

							###
							min_line = proj-std8
							if min_line < 0: 
								min_line = 0

							min_line2 = int(line+0.25) + 0.5


							if ud_val <= min_line2:
								line_dir += '***'
							####


							# if avg - ud_val > 0.55 and mean_3 - ud_val > 0.5:
							if min_line2 > 0.5 and std8 > 0.6*math.log(proj, 1.5):

								for r in recent[-1][1]:
									if r >= ud_val:
										hits += 1

								if hits >= 5: 

									cond_met = True

						else:
							line_dir = 'UNDER'

							###
							max_line = proj+std8

							max_line1 = int(max_line+0.25)

							if max_line - max_line1 >= 0.5 and max_line - max_line1 <= 0.75:
								max_line2 = max_line1 + 0.5
							elif max_line - max_line1 >= 0.25 and max_line - max_line1 <= 0.5:
								max_line2 = max_line1 + 0.5
							else: 
								max_line2 = max_line1


							# if line > 0.5 and stdev_8 < math.log(raw_proj, 2):

							if ud_val >= max_line2 and max_line2 > 0.5 and stdev_8 < math.log(proj, 2):
								line_dir += '***'
							####

							if ud_val - avg > 0.55 and ud_val - mean_3 > 0.5:

								for r in recent[-1][1]:
									if r <= ud_val:
										hits += 1

								if hits >= 5: 

									cond_met = True

						if cond_met:

							line_str = colored(str(ud_val) + ' ' + line_dir, 'yellow')

							print('=============================================')
							print(ud_player, ud_stat, line_str)
							print('=============================================')

							print('raw proj: ' + str(round(proj, 2)), ' hit_8: ' + str(hits) + '/8')
							print('mean_8: ' + str(np.mean(recent[-1][1])) + ' | stdev_8: ' + str(round(std8, 2)))
							print('mean_13: ' + str(round(avg, 2)))
							print('')

							for r in recent:
								print(r[0] + ': ' + str(r[1]))

							print('')

		
		except:

			continue



				# # over
				# if avg_3 - ud_val >= 0.5:

				# 	adj = 0

				# 	for s in stat_8:

				# 		if s >= base:
				# 			hits += 1

				# 		diff = min(0, s - ud_val)

				# 		if diff >= 1:

				# 			diff_scaled = math.log(diff, 2)
				# 			adj += diff_scaled
						
				# 		elif diff < 0:

				# 			diff_scaled = math.log(abs(diff))
				# 			adj -= 1.5*diff_scaled


				# 	proj = round(base + adj, 2)

					# if proj - ud_val > 0.5:
					# 	print('')
					# 	print(ud_player, ud_stat, ud_val, 'OVER')
					# 	print('avg_3: ' + str(avg_3) + ' avg_8: ' + str(avg_8))
					# 	print('proj: ' + str(proj))
					# 	print('hit_8: ' + str(hits) + '/8')
					# 	print('log: ' + str(stat_8))


			return

		time.sleep(0.15)

	return





def min_threshold(line_val):

	return math.log(line_val)




def ud_stats(stat_str):

	ud_to_stat = {'Pts': 'Points', 'Rebs': 'Rebounds', 'Asts': 'Assists'}

	if ' + ' not in stat_str:

		return [stat_str]

	res = []
	stats_arr = stat_str.split(' + ')

	for stat in stats_arr:

		if stat in ud_to_stat:

			res.append(ud_to_stat[stat])
		else:

			res.append(stat)

	return res



import numpy as np




def calculate_projection(game_data, stat):

	stat_all = game_data[stat]
	stat_8 = stat_all[0:8]
	stat_3 = stat_all[0:3]

	med_13 = np.median(stat_all)
	avg_13 = np.mean(stat_all[0:13])
	avg_8 = round(sum(stat_8)/8, 4)
	avg_3 = round(sum(stat_3)/3, 4)

	stdev_8 = np.std(stat_8)

	base_13 = (med_13 + avg_13)/2

	adj = 0

	for s in stat_8:

		diff = min(0, s - avg_8)

		if diff >= 1:

			diff_scaled = math.log(diff, 2)
			adj += diff_scaled
		
		elif diff < 0:

			diff_scaled = math.log(abs(diff), 2)
			adj -= 1.1*diff_scaled

	raw_proj = base_13 + (adj/8)

	return raw_proj, stat_8, avg_3, avg_13, med_13, stdev_8





def calculate_projection_stat(stat_all, stat):

	stat_13 = stat_all[0:13]
	stat_8 = stat_all[0:8]
	stat_3 = stat_all[0:3]

	med_13 = np.median(stat_all[0:13])
	avg_13 = np.mean(stat_all[0:13])
	avg_8 = round(sum(stat_8)/8, 4)
	avg_3 = round(sum(stat_3)/3, 4)

	stdev_8 = np.std(stat_8)

	base_13 = (med_13 + avg_13)/2

	adj = 0

	for s in stat_8:

		diff = min(0, s - avg_8)

		if diff >= 1:

			diff_scaled = math.log(diff, 2.5)
			adj += diff_scaled
		
		elif diff < 0:

			diff_scaled = math.log(abs(diff))
			adj -= 1.25*diff_scaled

	raw_proj = base_13 + (adj/8)

	return raw_proj, stat_8, avg_3, avg_13, med_13, stdev_8




def test_res(raw_proj, line, actual, over=True):

	if over:

		res = 'proj: ' + str(round(raw_proj,2)) + ' over: ' + str(round(line, 4)) + ' actual: ' + str(actual)

		if actual >= line: 

			return colored(res, 'green')

		else:

			return colored(res, 'red')

	else:

		res = 'proj: ' + str(round(raw_proj,2)) + ' under: ' + str(round(line, 4)) + ' actual: ' + str(actual)

		if actual <= line: 

			return colored(res, 'green')

		else:

			return colored(res, 'red')





test_names = ['Fred VanVleet','Jalen Green','Jabari Smith Jr.','Alperen Sengun','Dillon Brooks','Jimmy Butler','Kyle Lowry','Caleb Martin','Duncan Robinson','Terry Rozier','Miles Bridges','Gordon Hayward','Brandon Miller','Tyrese Haliburton','Myles Turner','Buddy Hield','Bruce Brown','Obi Toppin','Cade Cunningham','Bojan Bogdanovic','Killian Hayes','Isaiah Stewart','Donovan Mitchell','Darius Garland','Jarrett Allen','Max Strus','Paolo Banchero','Franz Wagner','Goga Bitadze','Kyle Kuzma','Jordan Poole','Tyus Jones','Deni Avdija','Daniel Gafford','Joel Embiid','Tyrese Maxey','Nikola Jokic','Jamal Murray','Michael Porter Jr.','Aaron Gordon','Kentavious Caldwell-Pope','Trae Young','Dejounte Murray','Clint Capela', 'Anthony Davis','LeBron James']


'''
test over hit rate - line below raw proj - stdev_8

Raw Proj - stdev8 
=================
Points: 1105/1290 | 0.8566
Rebounds: 1038/1290 | 0.8047
Assists: 976/1290 | 0.7566


Median 8 - stdev8
=================
Points: 1077/1290 | 0.8349
Rebounds: 1054/1290 | 0.8171
Assists: 1007/1290 | 0.7806


stdev > 0.75 * math.log(raw_proj, 1.618)
++++++++++++++
Points: 1513/1776 | 0.8519
Rebounds: 740/880 | 0.8409
Assists: 874/1100 | 0.7945

Points: 1446/1699 | 0.8511
Rebounds: 535/647 | 0.8269
Assists: 372/457 | 0.814



log base 2

Points: 1699/1992 | 0.8529
Rebounds: 1252/1551 | 0.8072
Assists: 898/1169 | 0.7682


log base 1.5

Points: 1201/1393 | 0.8622
Rebounds: 201/230 | 0.8739
Assists: 122/145 | 0.8414


0.75 log base 1.5

Points: 1201/1393 | 0.8622
Rebounds: 201/230 | 0.8739
Assists: 122/145 | 0.8414

0.6 * ()

Points: 1513/1770 | 0.8548
Rebounds: 652/795 | 0.8201
Assists: 430/544 | 0.7904


0.5 log base 1.5

Points: 1643/1927 | 0.8526
Rebounds: 1054/1301 | 0.8101
Assists: 714/912 | 0.7829

'''

# {'Fred VanVleet': defaultdict(None, {'*player_id': 1627832}), 'Jalen Green': defaultdict(None, {'*player_id': 1630224}), 'Jabari Smith Jr.': defaultdict(None, {'*player_id': 1631095}), 'Alperen Sengun': defaultdict(None, {'*player_id': 1630578}), 'Dillon Brooks': defaultdict(None, {'*player_id': 1628415}), 'Jimmy Butler': defaultdict(None, {'*player_id': 202710}), 'Kyle Lowry': defaultdict(None, {'*player_id': 200768}), 'Caleb Martin': defaultdict(None, {'*player_id': 1628997}), 'Duncan Robinson': defaultdict(None, {'*player_id': 1629130}), 'Terry Rozier': defaultdict(None, {'*player_id': 1626179}), 'Miles Bridges': defaultdict(None, {'*player_id': 1628970}), 'Gordon Hayward': defaultdict(None, {'*player_id': 202330}), 'Brandon Miller': defaultdict(None, {'*player_id': 1641706}), 'Tyrese Haliburton': defaultdict(None, {'*player_id': 1630169}), 'Myles Turner': defaultdict(None, {'*player_id': 1626167}), 'Buddy Hield': defaultdict(None, {'*player_id': 1627741}), 'Bruce Brown': defaultdict(None, {'*player_id': 1628971}), 'Obi Toppin': defaultdict(None, {'*player_id': 1630167}), 'Cade Cunningham': defaultdict(None, {'*player_id': 1630595}), 'Bojan Bogdanovic': defaultdict(None, {'*player_id': 202711}), 'Killian Hayes': defaultdict(None, {'*player_id': 1630165}), 'Isaiah Stewart': defaultdict(None, {'*player_id': 1630191}), 'Donovan Mitchell': defaultdict(None, {'*player_id': 1628378}), 'Darius Garland': defaultdict(None, {'*player_id': 1629636}), 'Jarrett Allen': defaultdict(None, {'*player_id': 1628386}), 'Max Strus': defaultdict(None, {'*player_id': 1629622}), 'Paolo Banchero': defaultdict(None, {'*player_id': 1631094}), 'Franz Wagner': defaultdict(None, {'*player_id': 1630532}), 'Goga Bitadze': defaultdict(None, {'*player_id': 1629048}), 'Kyle Kuzma': defaultdict(None, {'*player_id': 1628398}), 'Jordan Poole': defaultdict(None, {'*player_id': 1629673}), 'Tyus Jones': defaultdict(None, {'*player_id': 1626145}), 'Deni Avdija': defaultdict(None, {'*player_id': 1630166}), 'Daniel Gafford': defaultdict(None, {'*player_id': 1629655}), 'Joel Embiid': defaultdict(None, {'*player_id': 203954}), 'Tyrese Maxey': defaultdict(None, {'*player_id': 1630178}), 'Nikola Jokic': defaultdict(None, {'*player_id': 203999}), 'Jamal Murray': defaultdict(None, {'*player_id': 1627750}), 'Michael Porter Jr.': defaultdict(None, {'*player_id': 1629008}), 'Aaron Gordon': defaultdict(None, {'*player_id': 203932}), 'Kentavious Caldwell-Pope': defaultdict(None, {'*player_id': 203484}), 'Trae Young': defaultdict(None, {'*player_id': 1629027}), 'Dejounte Murray': defaultdict(None, {'*player_id': 1627749}), 'Clint Capela': defaultdict(None, {'*player_id': 203991})}


def test_1():


	test_names = ['Fred VanVleet','Jalen Green','Jabari Smith Jr.','Alperen Sengun','Dillon Brooks','Jimmy Butler','Kyle Lowry','Caleb Martin','Duncan Robinson','Terry Rozier','Miles Bridges','Gordon Hayward','Brandon Miller','Tyrese Haliburton','Myles Turner','Buddy Hield','Bruce Brown','Obi Toppin','Cade Cunningham','Bojan Bogdanovic','Killian Hayes','Isaiah Stewart','Donovan Mitchell','Darius Garland','Jarrett Allen','Max Strus','Paolo Banchero','Franz Wagner','Goga Bitadze','Kyle Kuzma','Jordan Poole','Tyus Jones','Deni Avdija','Daniel Gafford','Joel Embiid','Tyrese Maxey','Nikola Jokic','Jamal Murray','Michael Porter Jr.','Aaron Gordon','Kentavious Caldwell-Pope','Trae Young','Dejounte Murray','Clint Capela']

	test_player_ids = defaultdict()
	res = { 'Points': [0, 0], 'Assists': [0, 0], 'Rebounds': [0, 0] }
	nba_players = players.get_players()


	for player_name in test_names:

		test_player_ids[player_name] = defaultdict()

		# player_lines = ud_nba[player_name]


		try:

			player_info = next((x for x in nba_players if x.get("is_active") == True and x.get("full_name") == player_name), None)

			player_id = player_info.get("id")

			test_player_ids[player_name]['*player_id'] = player_id

			res[player_name] = defaultdict()

		except:

			# del ud_nba[player_name]
			continue


	for ud_player in test_player_ids.keys():

		print('\n')
		print(ud_player)
		print('='*len(ud_player))

		# try:

		player_id = test_player_ids[ud_player]['*player_id']

		game_log_pd = pd.concat(playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames())

		# if not game_log_pd: 

		# 	time.sleep(0.1)
		# 	game_log_pd = pd.concat(playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames())


		game_log = game_log_pd.to_dict('records')

		last_50_games = game_log[0:100]
		games_50 = defaultdict(list)

		for i in range(len(last_50_games)):

			game = last_50_games[i]

			# if 'PR' not in last_21_game_data: last_21_game_data['PR'] = 
			# DREB/OREB

			games_50['Points'].append(game['PTS'])
			games_50['Assists'].append(game['AST'])
			games_50['Rebounds'].append(game['REB'])
			# games_50['FGM'].append(game['FGM'])
			# games_50['FGA'].append(game['FGA'])


		test_stats = ['Points', 'Rebounds', 'Assists']


		for stat in test_stats:

			try:

				print(stat)
				print('-'*len(stat))

				hit = 0
				total = 0

				if len(games_50[stat]) >= 75:

					for i in range(0, 50):

						game_stat_21 = games_50[stat][i:]

						raw_proj, last_8, mean_3, mean_13, med_13, stdev_8 = calculate_projection_stat(game_stat_21, stat)

						# over

						line = raw_proj - stdev_8

						# line = np.median(last_8)-stdev_8



						if line < 0: 

							line = 0

						line = int(line+0.25) + 0.5
						next_val = games_50[stat][i+1]

						if line > 0.5 and stdev_8 > 0.6*math.log(raw_proj, 1.5):

							if int(next_val + 0.5) >= line and line >= 0.5: 

								hit += 1 

							total += 1

							print(test_res(raw_proj, line, next_val))


					# res[ud_player][stat] = round(hit/total, 4)

					print('> hits/total: ' + str(hit) + '/' + str(total))
					print('> win rate: ' + str(winrate(hit, total)) + ' (' + str(winrate(hit, total)) + ' %)')
					print('')


					prev_hit = res[stat][0] 
					prev_total = res[stat][1]

					res[stat][0] = prev_hit + hit
					res[stat][1] = prev_total + total
			except:

				continue

		# time.sleep(0.05)


		# except:

		# 	continue

	# print(res)

		print('Points: ' + str(res['Points'][0]) + '/' + str(res['Points'][1]) + ' | ' + str(winrate(res['Points'][0], res['Points'][1])))
		print('Rebounds: ' + str(res['Rebounds'][0]) + '/' + str(res['Rebounds'][1]) + ' | ' + str(winrate(res['Rebounds'][0], res['Rebounds'][1])))
		print('Assists: ' + str(res['Assists'][0]) + '/' + str(res['Assists'][1]) + ' | ' + str(winrate(res['Assists'][0], res['Assists'][1])))


	# print(player_arr_str)

				

def winrate(hit,total): 

	if total == 0:

		return 0

	return round(hit / total, 4)



'''
test under hit rate - line below raw proj - stdev_8

Raw Proj + stdev8 
=================
Points: 983/1290 | 0.762
Rebounds: 1038/1290 | 0.8047
Assists: 1039/1290 | 0.8054



'''

# {'Fred VanVleet': defaultdict(None, {'*player_id': 1627832}), 'Jalen Green': defaultdict(None, {'*player_id': 1630224}), 'Jabari Smith Jr.': defaultdict(None, {'*player_id': 1631095}), 'Alperen Sengun': defaultdict(None, {'*player_id': 1630578}), 'Dillon Brooks': defaultdict(None, {'*player_id': 1628415}), 'Jimmy Butler': defaultdict(None, {'*player_id': 202710}), 'Kyle Lowry': defaultdict(None, {'*player_id': 200768}), 'Caleb Martin': defaultdict(None, {'*player_id': 1628997}), 'Duncan Robinson': defaultdict(None, {'*player_id': 1629130}), 'Terry Rozier': defaultdict(None, {'*player_id': 1626179}), 'Miles Bridges': defaultdict(None, {'*player_id': 1628970}), 'Gordon Hayward': defaultdict(None, {'*player_id': 202330}), 'Brandon Miller': defaultdict(None, {'*player_id': 1641706}), 'Tyrese Haliburton': defaultdict(None, {'*player_id': 1630169}), 'Myles Turner': defaultdict(None, {'*player_id': 1626167}), 'Buddy Hield': defaultdict(None, {'*player_id': 1627741}), 'Bruce Brown': defaultdict(None, {'*player_id': 1628971}), 'Obi Toppin': defaultdict(None, {'*player_id': 1630167}), 'Cade Cunningham': defaultdict(None, {'*player_id': 1630595}), 'Bojan Bogdanovic': defaultdict(None, {'*player_id': 202711}), 'Killian Hayes': defaultdict(None, {'*player_id': 1630165}), 'Isaiah Stewart': defaultdict(None, {'*player_id': 1630191}), 'Donovan Mitchell': defaultdict(None, {'*player_id': 1628378}), 'Darius Garland': defaultdict(None, {'*player_id': 1629636}), 'Jarrett Allen': defaultdict(None, {'*player_id': 1628386}), 'Max Strus': defaultdict(None, {'*player_id': 1629622}), 'Paolo Banchero': defaultdict(None, {'*player_id': 1631094}), 'Franz Wagner': defaultdict(None, {'*player_id': 1630532}), 'Goga Bitadze': defaultdict(None, {'*player_id': 1629048}), 'Kyle Kuzma': defaultdict(None, {'*player_id': 1628398}), 'Jordan Poole': defaultdict(None, {'*player_id': 1629673}), 'Tyus Jones': defaultdict(None, {'*player_id': 1626145}), 'Deni Avdija': defaultdict(None, {'*player_id': 1630166}), 'Daniel Gafford': defaultdict(None, {'*player_id': 1629655}), 'Joel Embiid': defaultdict(None, {'*player_id': 203954}), 'Tyrese Maxey': defaultdict(None, {'*player_id': 1630178}), 'Nikola Jokic': defaultdict(None, {'*player_id': 203999}), 'Jamal Murray': defaultdict(None, {'*player_id': 1627750}), 'Michael Porter Jr.': defaultdict(None, {'*player_id': 1629008}), 'Aaron Gordon': defaultdict(None, {'*player_id': 203932}), 'Kentavious Caldwell-Pope': defaultdict(None, {'*player_id': 203484}), 'Trae Young': defaultdict(None, {'*player_id': 1629027}), 'Dejounte Murray': defaultdict(None, {'*player_id': 1627749}), 'Clint Capela': defaultdict(None, {'*player_id': 203991})}


def test_2():


	test_names = ['Fred VanVleet','Jalen Green','Jabari Smith Jr.','Alperen Sengun','Dillon Brooks','Jimmy Butler','Kyle Lowry','Caleb Martin','Duncan Robinson','Terry Rozier','Miles Bridges','Gordon Hayward','Brandon Miller','Tyrese Haliburton','Myles Turner','Buddy Hield','Bruce Brown','Obi Toppin','Cade Cunningham','Bojan Bogdanovic','Killian Hayes','Isaiah Stewart','Donovan Mitchell','Darius Garland','Jarrett Allen','Max Strus','Paolo Banchero','Franz Wagner','Goga Bitadze','Kyle Kuzma','Jordan Poole','Tyus Jones','Deni Avdija','Daniel Gafford','Joel Embiid','Tyrese Maxey','Nikola Jokic','Jamal Murray','Michael Porter Jr.','Aaron Gordon','Kentavious Caldwell-Pope','Trae Young','Dejounte Murray','Clint Capela']

	test_player_ids = defaultdict()
	res = { 'Points': [0, 0], 'Assists': [0, 0], 'Rebounds': [0, 0] }
	nba_players = players.get_players()

	# ud_nba = extract_ud_nba()

	# filter for nba players and stats 
	# ud_players = list(ud_nba.keys())

	for player_name in test_names:

		test_player_ids[player_name] = defaultdict()

		# player_lines = ud_nba[player_name]


		try:

			player_info = next((x for x in nba_players if x.get("is_active") == True and x.get("full_name") == player_name), None)

			player_id = player_info.get("id")

			test_player_ids[player_name]['*player_id'] = player_id

			res[player_name] = defaultdict()

		except:

			# del ud_nba[player_name]
			continue


	# player_arr_str = "["

	print(test_player_ids)


	for ud_player in test_player_ids.keys():

		print('\n')
		print(ud_player)
		print('='*len(ud_player))

		# try:

		player_id = test_player_ids[ud_player]['*player_id']

		game_log_pd = pd.concat(playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames())

		# if not game_log_pd: 

		# 	time.sleep(0.1)
		# 	game_log_pd = pd.concat(playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames())


		game_log = game_log_pd.to_dict('records')

		last_50_games = game_log[0:100]
		games_50 = defaultdict(list)

		for i in range(len(last_50_games)):

			game = last_50_games[i]

			# if 'PR' not in last_21_game_data: last_21_game_data['PR'] = 
			# DREB/OREB

			games_50['Points'].append(game['PTS'])
			games_50['Assists'].append(game['AST'])
			games_50['Rebounds'].append(game['REB'])
			# games_50['FGM'].append(game['FGM'])
			# games_50['FGA'].append(game['FGA'])


		test_stats = ['Points', 'Rebounds', 'Assists']


		for stat in test_stats:

			try:
				print(stat)
				print('-'*len(stat))

				hit = 0
				total = 0

				if len(games_50[stat]) >= 100:

					for i in range(0, 75):

						game_stat_21 = games_50[stat][i:]

						raw_proj, last_8, mean_3, mean_13, med_13, stdev_8 = calculate_projection_stat(game_stat_21, stat)

						# over

						'''
						Points: 2345/3000 | 0.7817
						Rebounds: 2456/3000 | 0.8187
						Assists: 2411/3000 | 0.8037
						'''

						# line = raw_proj - stdev_8

						# line = np.median(last_8)+stdev_8

						max_line = raw_proj+stdev_8

						max_line1 = int(max_line+0.25)

						line = max_line1

						if max_line - max_line1 >= 0.5 and max_line - max_line1 <= 0.75:
							line = max_line1 + 0.5
						elif max_line - max_line1 >= 0.25 and max_line - max_line1 <= 0.5:
							line = max_line1 + 0.5


						next_val = games_50[stat][i+1]

						if line > 0.5 and stdev_8 < math.log(raw_proj, 2):

							if int(next_val + 0.5) <= line: 

								hit += 1 

							total += 1

							print(test_res(raw_proj, line, next_val, False))


					# res[ud_player][stat] = round(hit/total, 4)


					win_rate = 0.0

					if total > 0: 
						win_rate = round(100*(hit/total), 2)

					print('> hits/total: ' + str(hit) + '/' + str(total))
					print('> win rate: ' + str(round(win_rate/100, 4)) + ' (' + str(win_rate) + ' %)')
					print('')


					prev_hit = res[stat][0] 
					prev_total = res[stat][1]

					res[stat][0] = prev_hit + hit
					res[stat][1] = prev_total + total

			except:

				continue

		# time.sleep(0.1)


		# except:

		# 	continue

	# print(res)

		print('Points: ' + str(res['Points'][0]) + '/' + str(res['Points'][1]) + ' | ' + str(winrate(res['Points'][0], res['Points'][1])))
		print('Rebounds: ' + str(res['Rebounds'][0]) + '/' + str(res['Rebounds'][1]) + ' | ' + str(winrate(res['Rebounds'][0], res['Rebounds'][1])))
		print('Assists: ' + str(res['Assists'][0]) + '/' + str(res['Assists'][1]) + ' | ' + str(winrate(res['Assists'][0], res['Assists'][1])))


'''
UNDERS

LINE VALUES > 0.5
=================
Points: 2345/3000 | 0.7817
Rebounds: 2456/3000 | 0.8187
Assists: 2411/3000 | 0.8037


LINE VALUES > 1.5
=================
Points: 2345/3000 | 0.7817
Rebounds: 2456/3000 | 0.8187
Assists: 2369/2951 | 0.8028


LINE VALUES > 2.5
=================
Points: 2345/3000 | 0.7817
Rebounds: 2424/2962 | 0.8184
Assists: 1985/2493 | 0.7962


LINE VALUES > 5.5
=================
Points: 2338/2992 | 0.7814
Rebounds: 1464/1814 | 0.8071
Assists: 944/1198 | 0.788


LINE VALUES > 9.5
=================
Points: 2277/2915 | 0.7811
Rebounds: 468/567 | 0.8254
Assists: 235/309 | 0.7605


********************
stdev < log(proj, 2)
********************

>= 0.5 and log base 2.5
Points: 1045/1292 | 0.8088
Rebounds: 2133/2560 | 0.8332
Assists: 1820/2169 | 0.8391


> 0.5 and log base 2.5
Points: 1045/1292 | 0.8088
Rebounds: 2133/2560 | 0.8332
Assists: 1820/2169 | 0.8391



> 0.5 and (log base 2)
Points: 267/329 | 0.8116
Rebounds: 1204/1402 | 0.8588
Assists: 1106/1291 | 0.8567

'''






find_ud_lines()

# test_1()
# test_2()











