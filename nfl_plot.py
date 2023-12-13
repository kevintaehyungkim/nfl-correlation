'''
https://www.python-graph-gallery.com/

# Seaborn Violin Plot
https://seaborn.pydata.org/generated/seaborn.violinplot.html
https://seaborn.pydata.org/examples/grouped_violinplots.html

# Overlap Scatter Plot on top of violin plot
https://stackoverflow.com/questions/59358115/add-one-specific-datapoint-marker-to-boxplot-or-violinplot-using-holoviews-hv

Plotly 

# Subtitle
https://towardsdatascience.com/a-clean-style-for-plotly-charts-250ba2f5f015

# Subplots 
https://plotly.com/python/subplots/
https://plotly.com/python/v3/table-subplots/

# Pie Chart
https://plotly.com/python/pie-charts
'''

import sys, time
# import option_analytics as option_analytics
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np

from datetime import datetime
from plotly.subplots import make_subplots
from pytz import timezone


OI_TICK_COUNT = 0
MAX_PAIN_TICK_COUNT = 0
OPTION_ANALYTICS_TICK_COUNT = 12
OI_TICK_COUNT = 15
MAX_PAIN_TICK_COUNT = 20
INTERVALS = [1, 5, 10, 20, 25, 40, 50, 100, 200]

COLORS = {
	'AQUA': '#7DCDD5',
	'DARK1': '#1E1F24',
	'DARK2': '#61D3D3',
	'GREEN': 'rgb(108,189,191)',
	'ORANGE': 'rgb(242,165,103)',
	'RED': 'rgb(219,119,132)',
	'BLUE_LIGHT': 'rgb(132,198,245)',
	'WHITE': 'rgb(255,255,255)'
}







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




nfl_stats = ["receiving_yds", "passing_yds"]




import requests
from datetime import date

r = requests.get("https://api.underdogfantasy.com/beta/v3/over_under_lines")
lines = r.json()["over_under_lines"]


ud_nfl = defaultdict()
ud_pairs = []


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



extract_ud_nfl()



# points - qb, wr
# ud_lines - qb, wr

# def find_distribution(points, mean, std, ud_lines):





# print(ud_nfl)


'''
process each play and create map of team yards (pass or rec) per game


game yards std. deviation of qb yards 2 standard deviations 

'''
def growth_correlation(qb, rec): 

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


	qb_recs, qb_yards = 0, 0 
	rec_recs, rec_yards = 0, 0

	# for game in growth_yards:


	qb_yards_sum = []
	rc_yards_sum = []

	qb_recs_sum = []
	rc_recs_sum = []


	for game in growth_yards:

		qb_yards = growth_yards[game][qb]
		rc_yards = growth_yards[game][rec]

		qb_recs = growth_recs[game][qb]
		rc_recs = growth_recs[game][rec]



		qb_yards_sum.append(growth_yards[game][qb][-1])
		rc_yards_sum.append(growth_yards[game][rec][-1])

		qb_recs_sum.append(qb_recs[-1])
		rc_recs_sum.append(rc_recs[-1])


	qb_yards_mean = round(np.mean(qb_yards_sum), 1)
	qb_yards_std = round(np.std(qb_yards_sum), 1)

	rc_yards_mean = round(np.mean(rc_yards_sum), 1)
	rc_yards_std = round(np.std(rc_yards_sum), 1)


	qb_recs_mean = round(np.mean(qb_recs_sum), 1)
	qb_recs_std = round(np.std(qb_recs_sum), 1)

	rc_recs_mean = round(np.mean(rc_recs_sum), 1)
	rc_recs_std = round(np.std(rc_recs_sum), 1)

	print("QB mean: " + str(qb_yards_mean) + " std: " + str(qb_yards_std))
	print("RC mean: " + str(rc_yards_mean) + " std: " + str(rc_yards_std))

	yards_growth_rate_game = rc_yards_mean/qb_yards_mean
	recs_growth_rate_game = rc_recs_mean/qb_recs_mean

	print("Growth rate game: " + str(yards_growth_rate_game))


	hit_rate = ''

	# sim_res = run_sim(qb, rec)
	# hit_rate = round(sim_res[2], 4)


	qb_yards_ud = None
	rc_yards_ud = None


	if qb in ud_nfl and rec in ud_nfl:

		qb_yards_ud = ud_nfl[qb]['passing_yds']
		rc_yards_ud = ud_nfl[rec]['receiving_yds']



	fig = go.Figure()
	fig = make_subplots(
	    rows=2, cols=2,
	    subplot_titles=(
	    	"<b> Game State - Receptions </b> <br>", 
	    	"<b> Game State - Yards </b> <br>",
	    	"<b> Growth Rate - Yards </b> <br>",
	    	"10k match sim - UD line win prob: " + str(hit_rate) + "</b><br>")
	    )



	# growth yards

	qb_projected_growth = [0]
	rc_projected_growth = [0]

	for i in range(1, max(qb_yards_sum)):

		qb_projected_growth.append(i)
		rc_projected_growth.append(i*yards_growth_rate_game)



	# growth recs

	qb_projected_growth1 = [0]
	rc_projected_growth1 = [0]

	for i in range(1, 30):

		qb_projected_growth1.append(i)
		rc_projected_growth1.append(i*recs_growth_rate_game)

	# fig.add_trace(go.Scatter(
	#     x=qb_projected_growth, y=rc_projected_growth,
	#     line_color='rgb(255,255,255)',
	# 	mode='lines',
	# 	# fill='tonexty'
	#     # marker=dict(symbol="diamond", size=4)
	# 	), 
	# 	row=2, col=1
	# )

		
	# print(qb_projected_growth1)
	# print(rc_projected_growth1)


	# some inverse function that translates this into quantitative metric/scoring


	distr_score = 0
	distr_hit = 0
	distr_total = 0


	for game in growth_yards:

		qb_yards = growth_yards[game][qb]
		rc_yards = growth_yards[game][rec]

		qb_recs = growth_recs[game][qb]
		rc_recs = growth_recs[game][rec]


		if qb_yards_ud and rc_yards_ud: 

			for i in range(len(qb_yards)):

				rc_yd, qb_yd = rc_yards[i], qb_yards[i]

				qb_low = qb_yards_mean - qb_yards_std*1.5
				qb_high = qb_yards_mean + qb_yards_std

				if qb_yd > qb_low and rc_yd < qb_high:

					qb_score = float(qb_yards_ud) - qb_yd
					rc_score = float(rc_yards_ud) - rc_yd

					score = qb_score * rc_score
					dist = (qb_score**2 + rc_score**2)**0.5

					if score > 0:
						distr_score += math.log(dist, 2)
						distr_hit += 1
					else:
						distr_score -= math.log(dist, 2)
						
					distr_total += 1




		#################
		# Open Interest #
		#################
		
		fig.add_trace(go.Scatter(
		    x=qb_projected_growth1, y=rc_projected_growth1,
		    line_color='rgba(108,189,191,0.1)',
			mode='lines',
		    line = dict(shape = 'linear', color = 'orange', width= 1),
		    # marker=dict(symbol="diamond", size=4)
			), 
			row=1, col=1
		)

		fig.add_trace(go.Scatter(
		    x=qb_recs,
		    y=rc_recs,
		    fill='tonexty',
		    # fill='tonexty',
		    fillcolor='rgba(108,189,191,0.15)',
		    line_color='rgba(255,255,255,0)',
		    showlegend=False,
		    mode='markers',
			),
			row=1, col=1
		)

		fig.add_trace(go.Scatter(
		    x=qb_recs, y=rc_recs,
		    line_color='rgb(255,255,255)',
			mode='markers',
		    marker=dict(symbol="diamond", size=3)
			), 
			row=1, col=1
		)



#### 

		# fig.add_trace(go.Scatter(
		#     x=qb_projected_growth, y=rc_projected_growth,
		#     line_color=COLORS['ORANGE'],
		# 	mode='lines',
		#     line = dict(shape = 'linear', color = 'orange', width= 1),
		# 	), 
		# 	row=1, col=2
		# )


		fig.add_trace(go.Scatter(
		    x=qb_yards, y=rc_yards,
		    line_color='rgb(255,255,255)',
			mode='markers',
		    marker=dict(symbol="diamond", size=3)
			), 
			row=1, col=2
		)





		############
		# Max Pain #
		############

		fig.add_trace(go.Scatter(
		    x=qb_projected_growth, y=rc_projected_growth,
		    line_color='rgba(108,189,191,0.05)',
			mode='lines',
			# visible='legendonly',
			# fill='tonexty'
			), 
			row=2, col=1
		)

		fig.add_trace(go.Scatter(
		    x=qb_yards,
		    y=rc_yards,
		    fill='tonexty',
		    # fill='none',
		    fillcolor='rgba(108,189,191,0.15)',
		    line_color='rgba(255,255,255,0)',
		    showlegend=False,
		    mode='markers',
		    name='Call OI',
			),
			row=2, col=1
		)




		fig.add_trace(go.Scatter(
		    x=qb_projected_growth, y=rc_projected_growth,
		    line_color='rgba(108,189,191,0.05)',
			mode='lines',
			# visible='legendonly',
			# fill='tonexty'
			), 
			row=1, col=2
		)

		fig.add_trace(go.Scatter(
		    x=qb_yards,
		    y=rc_yards,
		    fill='tonexty',
		    # fill='none',
		    fillcolor='rgba(108,189,191,0.15)',
		    line_color='rgba(255,255,255,0)',
		    showlegend=False,
		    mode='markers',
		    name='Call OI',
			),
			row=1, col=2
		)



		fig.add_trace(go.Scatter(
		    x=qb_yards, y=rc_yards,
		    line_color='rgb(255,255,255)',
			mode='lines',
		    # marker=dict(symbol="diamond", size=3)
		    line = dict(shape = 'linear', color = 'white', width= 1),
			), 
			row=2, col=1
		)


		fig.add_trace(go.Scatter(
		    x=qb_yards_sum, y=rc_yards_sum,
		    line_color='WHITE',
			mode='markers',
		    name='Max Pain',
		    marker=dict(symbol="diamond", size=5)
			), 
			row=2, col=1
		)







	if qb in ud_nfl:

		qb_yards_ud = ud_nfl[qb]['passing_yds']


		fig.add_vline(
			x=qb_yards_ud, 
			# name='Max Pain',
			line_width=1,
			# line_color='rgb(204,102,119)',
			line_color=COLORS['ORANGE'],
			row=1, col=2
		)

		fig.add_vline(
			x=qb_yards_ud, 
			# name='Max Pain',
			line_width=1,
			# line_color='rgb(204,102,119)',
			line_color=COLORS['ORANGE'],
			row=2, col=2
		)


	if rec in ud_nfl:

		rc_yards_ud = ud_nfl[rec]['receiving_yds']


		fig.add_hline(
			y=rc_yards_ud, 
			name='Max Pain',
			line_width=1,
			line_color=COLORS['ORANGE'],
			row=1, col=2
		)

		fig.add_hline(
			y=rc_yards_ud, 
			name='Max Pain',
			line_width=1,
			line_color=COLORS['ORANGE'],
			row=2, col=2
		)

		fig.add_trace(go.Scatter(
		    x=qb_yards,
		    y=rc_yards,
		    fill='tonexty',
		    fillcolor='rgba(108,189,191,0.15)',
		    line_color='rgba(255,255,255,0)',
		    showlegend=False,
		    mode='markers',
		    name='Call OI',
			),
			row=2, col=1
		)	




	fig.update_yaxes(
	    title_text="Receptions",
	    title_font={"size": 14},
	    title_standoff = 20,
	    row=1, col=1
	)

	fig.update_xaxes(
        title_text="Completions",
        title_font={"size": 14},
        title_standoff = 20,
        row=1, col=1
	)


	fig.update_yaxes(
	    title_text="Receiving Yds",
	    title_font={"size": 14},
	    title_standoff = 20,
	    row=1, col=2
	)

	fig.update_xaxes(
        title_text="Passing Yds",
        title_font={"size": 14},
        title_standoff = 20,
        row=1, col=2
	)


	fig.update_yaxes(
	    title_text="Receiving Yds",
	    title_font={"size": 14},
	    title_standoff = 20,
	    row=2, col=1
	)

	fig.update_xaxes(
        title_text="Passing Yds",
        title_font={"size": 14},
        title_standoff = 20,
        row=2, col=1
	)












	fig.add_hline(
		y=rc_yards_mean,
		name='rec yards mean',
		line_width=1,
		line_color=COLORS['WHITE'],
		row=1, col=2
	)

	fig.add_vline(
		x=qb_yards_mean, 
		name='qb yards mean',
		line_width=1,
		line_color=COLORS['WHITE'],
		row=1, col=2
	)

	fig.add_vrect(
		x0=qb_yards_mean-qb_yards_std,
		x1=qb_yards_mean+qb_yards_std,
		name='qb yards mean 1std',
		line_width=1,
		line_dash="dash",
		line_color=COLORS['WHITE'],
		row=1, col=2
	)





	fig.add_vrect(
		x0=qb_yards_mean-qb_yards_std,
		x1=qb_yards_mean+qb_yards_std,
		name='Max Pain',
		line_width=1,
		line_dash="dash",
		line_color=COLORS['WHITE'],
		row=2, col=1
	)



	fig.add_vline(
		x=qb_yards_mean+qb_yards_std, 
		name='Max Pain',
		line_width=1,
		line_dash="dash",
		line_color=COLORS['WHITE'],
		row=2, col=1
	)

	fig.add_vline(
		x=qb_yards_mean, 
		name='QB Yards Mean',
		line_width=1,
		line_color=COLORS['WHITE'],
		row=2, col=1
	)




	# qb_yards_sim = sim_res[1]
	# rec_yards_sim = sim_res[0]



	#################
	# Open Interest #
	#################
	
	# fig.add_trace(go.Scatter(
	#     x=qb_projected_growth1, y=rc_projected_growth1,
	#     line_color='rgba(108,189,191,0.1)',
	# 	mode='lines',
	#     line = dict(shape = 'linear', color = 'orange', width= 1),
	#     # marker=dict(symbol="diamond", size=4)
	# 	), 
	# 	row=1, col=1
	# )

	# fig.add_trace(go.Scatter(
	#     x=qb_recs,
	#     y=rc_recs,
	#     fill='tonexty',
	#     # fill='tonexty',
	#     fillcolor='rgba(108,189,191,0.15)',
	#     line_color='rgba(255,255,255,0)',
	#     showlegend=False,
	#     mode='markers',
	# 	),
	# 	row=1, col=1
	# )

	# fig.add_trace(go.Scatter(
	#     x=qb_projected_growth1, y=rc_projected_growth1,
	#     line_color='rgba(108,189,191,0.1)',
	# 	mode='lines',
	#     line = dict(shape = 'linear', color = 'orange', width= 1),
	#     # marker=dict(symbol="diamond", size=4)
	# 	), 
	# 	row=2, col=2
	# )

	# fig.add_trace(go.Scatter(
	#     x=qb_yards, y=rc_yards,
	# 	mode='markers',
	# 	# fill='tonexty',
	# 	# fillcolor='rgba(108,189,191,0.15)',
	# 	# line_color='rgba(255,255,255,0)',
	# 	fillcolor='rgba(108,189,191,0.15)',
	#     marker=dict(symbol="diamond", size=2)
	# 	), 
	# 	row=2, col=2
	# )

	# fig.add_trace(go.Scatter(
	#     x=qb_yards_sim, y=rec_yards_sim,
	#     line_color='rgba(108,189,191,0.2)',
	# 	mode='markers',
	#     marker=dict(symbol="diamond", size=5)
	# 	), 
	# 	row=2, col=2
	# )



	if qb in ud_nfl:


		corr_res = []


		qb_yards_ud = ud_nfl[qb]['passing_yds']


		fig.add_vline(
			x=qb_yards_ud, 
			# name='Max Pain',
			line_width=1,
			# line_color='rgb(204,102,119)',
			line_color=COLORS['ORANGE'],
			row=2, col=2
		)


		if rec in ud_nfl:

			rc_yards_ud = ud_nfl[rec]['receiving_yds']


			fig.add_hline(
				y=rc_yards_ud, 
				name='Max Pain',
				line_width=1,
				line_color=COLORS['ORANGE'],
				row=2, col=2
			)


			# for i in range(len(qb_yards_sim)):

			# 	qb_yard_game = qb_yards_sim[i]
			# 	rec_yard_game = rec_yards_sim[i]

			# 	if (rec_yard_game > float(rc_yards_ud) and qb_yard_game > float(qb_yards_ud)) or (rec_yard_game < float(rc_yards_ud) and qb_yard_game < float(qb_yards_ud)):
			# 		corr_res.append(1)
			# 	else:
			# 		corr_res.append(0)

			# hit_rate = round(sum(corr_res)/len(corr_res), 4)
			# print(hit_rate)

			# fig.update_layout(
			#     subplot_titles=(
			#     	"<b> Game State - Receptions </b> <br>", 
			#     	"<b> Game State - Yards </b> <br>",
			#     	"<b> Growth Rate - Yards </b> <br>",
			#     	"<b> 10k sim end game - prob: " + str(hit_rate) + "</b><br>")
			#    )





	# fig.add_vrect(
	# 	x0=qb_yards_mean-qb_yards_std,
	# 	x1=qb_yards_mean+qb_yards_std,
	# 	name='qb yards mean 1std',
	# 	line_width=1,
	# 	line_dash="dash",
	# 	line_color=COLORS['WHITE'],
	# 	row=2, col=2
	# )










	fig.layout.plot_bgcolor = '#1E1F24'
	fig.layout.paper_bgcolor = '#1E1F24'

	fig.update_layout(template='plotly_dark')
	fig.update_layout(title_text=format_title(qb + ' + ' + rec, "Updated: " + get_updated_time()), title_font = {"size": 22})

	fig.update_xaxes(title_font_color='#7DCDD5')
	fig.update_yaxes(title_font_color='#7DCDD5')

	fig.update_layout(margin=dict(
		l=130, 
		r=60, 
		b=100, 
		t=140, 
		pad=4)
	)

	fig.show()


	return 






import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


from random import seed
from random import gauss


from scipy.special import inv_boxcox



seed(1)






def transform_distribution(data):

	# print("original data: ")
	# print(data)
	# print(np.mean(data))
	# print(np.median(data))
	# print(np.std(data))

	k2, p = stats.normaltest(np.array(data))
	# print('\nChi-squared statistic = %.3f, p = %.3f' % (k2, p))

	alpha = 0.05

	if p > alpha:
	    # print('The original data is Gaussian - p: ' + str(p) + ' alpha: 0.05')
	    return np.mean(data), np.std(data)
	# else:
	    # print('The original data does not look Gaussian')


	# print('Performing box-clot transformation')

	# apply box-cox transformation

	data_trans, lmbda = stats.boxcox(data)
	# print('lambda: ' + str(lmbda))

	k2, p = stats.normaltest(np.array(data_trans))
	# print('\nChi-squared statistic = %.3f, p = %.3f' % (k2, p))

	# alpha = 0.05
	# if p > alpha:
	    # print('The transformed data is Gaussian - p: ' + str(p) + ' alpha: 0.05')
	# else:
		# print('The transformed data does not look Gaussian')


	data_trans_mean = np.mean(data_trans)
	data_trans_std  = np.std(data_trans)


	upper_limit_trans = data_trans_mean + 3 * data_trans_std
	lower_limit_trans = data_trans_mean - 3 * data_trans_std

	back_trans_upper_limits = inv_boxcox(upper_limit_trans, lmbda)
	back_trans_lower_limits = inv_boxcox(lower_limit_trans, lmbda)

	back_trans_mean = inv_boxcox(data_trans_mean, lmbda)
	back_trans_std = inv_boxcox(data_trans_std, lmbda)

	# print('box-clot back-transformation mean: ' + str(back_trans_mean))
	# print('box-clot back-transformation std: ' + str(back_trans_std))


	return back_trans_mean, back_trans_std





def run_sim(qb, rec): 

	'''
	https://www.datasciencecentral.com/choosing-the-correct-type-of-regression-analysis/#:~:text=Linear%20models%20are%20the%20most,first%20type%20you%20should%20consider.
	'''

	# qb_recs, qb_yards = 0, 0 
	# rec_recs, rec_yards = 0, 0
	print('\n')
	print('[' + qb + '+' + rec + ']')


	qb_recs_game = []
	rec_ratio_game = []


	qb_yards_rec = []
	qb_yards_rem = []


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

					qb_yards_rec.append(yards)

				else: 

					growth_recs[game][rec].append(curr_recs)
					growth_yards[game][rec].append(curr_yards)

					qb_yards_rem.append(yards)


	num_games = len(growth_recs.keys())

	if num_games < 5:
		return


	print('games: ' + str(num_games))



	for g in growth_recs.keys():
		game = growth_recs[g]
		qb_recs_game.append(game[qb][-1])
		qb_recs_game.append(game[qb][-2])

		rec_ratio_game.append(game[rec][-1]/game[qb][-1])
		rec_ratio_game.append(game[rec][-2]/game[qb][-2])
	

	qb_yards_rec_const = abs(min(qb_yards_rec))+1
	qb_yards_rec_adj = [x + qb_yards_rec_const for x in qb_yards_rec]

	yards_rec_mean, yards_rec_std = transform_distribution(qb_yards_rec_adj)
	yards_rec_mean -= qb_yards_rec_const



	qb_yards_rem_const = abs(min(qb_yards_rem))+1
	qb_yards_rem_adj = [x + qb_yards_rem_const for x in qb_yards_rem]

	yards_rem_mean, yards_rem_std = transform_distribution(qb_yards_rem_adj)
	yards_rem_mean -= qb_yards_rem_const



	# print("avg yard rec: " + str(yards_rec_mean))
	# print("avg yard rem: " + str(yards_rem_mean))



	corr_res = []


	# print(qb_recs_game)
	# print(rec_ratio_game)

	comp_const = abs(min(qb_recs_game))+1
	comp_mean, comp_std = transform_distribution(qb_recs_game)



	rec_ratio_const = abs(min(rec_ratio_game))+0.1
	rec_ratio_game_adj = [x + rec_ratio_const for x in rec_ratio_game]

	rec_ratio_mean, rec_ratio_std = transform_distribution(rec_ratio_game_adj)
	rec_ratio_mean -= rec_ratio_const


	rec_yards_end = []
	qb_yards_end = []

	for i in range(10000):

		# print(qb_recs_game)


		comp_sim = gauss(comp_mean, comp_std)

		rec_ratio_sim = gauss(rec_ratio_mean, rec_ratio_std)
		rec_sim = int(comp_sim*rec_ratio_sim)

		comp_sim = int(comp_sim)

		# avg yard distances
		rec_yd_raw = gauss(yards_rec_mean, yards_rec_std)
		rec_yd = 0

		if rec_yd_raw > 0:
			rec_yd = int(min(rec_yd_raw, max(qb_yards_rec)))



		non_rec_yd_raw = gauss(yards_rem_mean, yards_rem_std)
		non_rec_yd = 0
		
		if non_rec_yd_raw > 0:
			non_rec_yd = int(min(non_rec_yd_raw, max(qb_yards_rem)))


		# non_rec_yd = max(0, non_rec_yd)
		# non_rec_yd = min(non_rec_yd, max(qb_yards_rem))
		# non_rec_yd = int(non_rec_yd)

		rec_yards_sim = rec_sim*rec_yd
		qb_yards_sim = rec_yards_sim + (comp_sim-rec_sim)*non_rec_yd


		if rec in ud_nfl and qb in ud_nfl:

			rc_yards_ud = ud_nfl[rec]['receiving_yds']
			qb_yards_ud = ud_nfl[qb]['passing_yds']


			if (rec_yards_sim > float(rc_yards_ud) and qb_yards_sim > float(qb_yards_ud)) or rec_yards_sim < float(rc_yards_ud) and qb_yards_sim < float(qb_yards_ud):
				corr_res.append(1)
			else:
				corr_res.append(0)

			hit_rate = round(sum(corr_res)/len(corr_res), 4)
			# print(hit_rate)


		rec_yards_end.append(rec_yards_sim)
		qb_yards_end.append(qb_yards_sim)


	print('')


			
	return [rec_yards_end, qb_yards_end, hit_rate]





def correlation_rank():

	pair_prob = []

	ud_pairs = "S.Howell+T.McLaurin K.Murray+M.Brown K.Murray+Mi.Wilson J.Allen+S.Diggs J.Allen+G.Davis T.Boyle+G.Wilson D.Ridder+D.London D.Ridder+J.Smith B.Young+A.Thielen J.Browning+J.Chase J.Browning+T.Higgins D.Thompson-Robinson+A.Cooper T.DeVito+D.Waller T.DeVito+J.Hyatt D.Prescott+C.Lamb P.Mahomes+R.Rice P.Mahomes+T.Kelce J.Goff+A.Brown J.Goff+S.LaPorta J.Fields+D.Moore J.Fields+C.Kmet J.Love+J.Reed J.Love+C.Watson L.Jackson+Z.Flowers L.Jackson+M.Andrews C.Stroud+N.Brown C.Stroud+N.Collins C.Stroud+N.Dell G.Minshew+J.Downs G.Minshew+M.Pittman T.Lawrence+E.Engram T.Lawrence+C.Kirk T.Lawrence+C.Ridley G.Smith+T.Lockett G.Smith+D.Metcalf M.Stafford+P.Nacua M.Stafford+C.Kupp A.O'Connell+D.Adams A.O'Connell+J.Meyers R.Wilson+C.Sutton T.Tagovailoa+T.Hill T.Tagovailoa+J.Waddle J.Herbert+K.Allen J.Herbert+J.Palmer J.Hurts+A.Brown J.Hurts+D.Smith J.Hurts+D.Goedert M.Jones+K.Bourne K.Pickett+G.Pickens K.Pickett+D.Johnson B.Purdy+D.Samuel B.Purdy+G.Kittle B.Purdy+B.Aiyuk B.Mayfield+C.Godwin B.Mayfield+M.Evans J.Dobbs+J.Jefferson J.Dobbs+T.Hockenson J.Dobbs+J.Addison W.Levis+D.Hopkins"


	ud_pair_arr = ud_pairs.split(' ')

	for pair in ud_pair_arr:
		print(pair)

		try: 
			pair_split = pair.split('+')

			qb, rec = pair_split[0], pair_split[1]
			hit_prob = run_sim(qb, rec)[2]
			pair_prob.append([hit_prob, pair])

		except:
			print('no match')
			continue


	pair_prob_sorted = sorted(pair_prob, reverse=True)


	for p in pair_prob_sorted:
		print (p[1] + ' - ' + str(p[0]))




def find_ud_scores():

	distr_score = 0
	distr_hit = 0
	distr_total = 0

	pair_prob = []

	ud_pairs = "S.Howell+T.McLaurin K.Murray+M.Brown K.Murray+Mi.Wilson J.Allen+S.Diggs J.Allen+G.Davis T.Boyle+G.Wilson D.Ridder+D.London D.Ridder+J.Smith B.Young+A.Thielen J.Browning+J.Chase J.Browning+T.Higgins D.Thompson-Robinson+A.Cooper T.DeVito+D.Waller T.DeVito+J.Hyatt D.Prescott+C.Lamb P.Mahomes+R.Rice P.Mahomes+T.Kelce J.Goff+A.Brown J.Goff+S.LaPorta J.Fields+D.Moore J.Fields+C.Kmet J.Love+J.Reed J.Love+C.Watson L.Jackson+Z.Flowers L.Jackson+M.Andrews C.Stroud+N.Brown C.Stroud+N.Collins C.Stroud+N.Dell G.Minshew+J.Downs G.Minshew+M.Pittman T.Lawrence+E.Engram T.Lawrence+C.Kirk T.Lawrence+C.Ridley G.Smith+T.Lockett G.Smith+D.Metcalf M.Stafford+P.Nacua M.Stafford+C.Kupp A.O'Connell+D.Adams A.O'Connell+J.Meyers R.Wilson+C.Sutton T.Tagovailoa+T.Hill T.Tagovailoa+J.Waddle J.Herbert+K.Allen J.Herbert+J.Palmer J.Hurts+A.Brown J.Hurts+D.Smith J.Hurts+D.Goedert M.Jones+K.Bourne K.Pickett+G.Pickens K.Pickett+D.Johnson B.Purdy+D.Samuel B.Purdy+G.Kittle B.Purdy+B.Aiyuk B.Mayfield+C.Godwin B.Mayfield+M.Evans J.Dobbs+J.Jefferson J.Dobbs+T.Hockenson J.Dobbs+J.Addison W.Levis+D.Hopkins"


	ud_pair_arr = ud_pairs.split(' ')

	for pair in ud_pair_arr:
		print(pair)

		# pair_split = pair.split('+')
		# qb, rec = pair_split[0], pair_split[1]
		# find_score(qb, rec)

		try: 
			pair_split = pair.split('+')

			qb, rec = pair_split[0], pair_split[1]
			distr_prob, distr_score, distr_total, distr, rec_data, qb_data, ud_lines = find_score(qb, rec)

			if distr_total > 50 and distr > 0.2 :

				pair_prob.append([distr_prob, round(distr_score, 4), distr_total, round(distr,3), qb + ' ' + colored(str(ud_lines[0]), 'cyan') + ' ' + rec + ' ' + colored(str(ud_lines[1]), 'cyan'), rec_data, qb_data ])

		except:
			print('no match')
			continue

	pair_prob_sorted = sorted(pair_prob, reverse=True)

	for p in pair_prob_sorted:
		print('')
		print (p[4] + ' --- ' + colored(str(round(100.0*p[0], 2)) + ' %', 'green'))
		print(' - line corr score: ' + colored(str(p[1]), 'yellow') + ' (' + str(p[2]) + ' game states)')
		print(' - avg yard share: ' + str(round(100*p[3], 2)) + ' %')

		rec_total = p[5][0]+p[5][1]
		qb_total = p[6][0]+p[6][1]

		print(' - [rec] over: ' + colored(str(round(p[5][0]/rec_total, 2)), 'yellow') + ' under: ' + colored(str(round(p[5][1]/rec_total, 2)), 'yellow'))
		print(' - [qb] over: ' + colored(str(round(p[6][0]/qb_total, 2)), 'yellow') + ' under: ' + colored(str(round(p[6][1]/qb_total, 2)), 'yellow'))


def find_score(qb, rec):


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


	qb_recs, qb_yards = 0, 0 
	rec_recs, rec_yards = 0, 0

	# for game in growth_yards:


	qb_yards_sum = []
	rc_yards_sum = []

	qb_recs_sum = []
	rc_recs_sum = []


	for game in growth_yards:

		qb_yards = growth_yards[game][qb]
		rc_yards = growth_yards[game][rec]

		qb_recs = growth_recs[game][qb]
		rc_recs = growth_recs[game][rec]



		qb_yards_sum.append(growth_yards[game][qb][-1])
		rc_yards_sum.append(growth_yards[game][rec][-1])

		qb_recs_sum.append(qb_recs[-1])
		rc_recs_sum.append(rc_recs[-1])


	qb_yards_mean = round(np.mean(qb_yards_sum), 1)
	qb_yards_std = round(np.std(qb_yards_sum), 1)

	rc_yards_mean = round(np.mean(rc_yards_sum), 1)
	rc_yards_std = round(np.std(rc_yards_sum), 1)


	qb_recs_mean = round(np.mean(qb_recs_sum), 1)
	qb_recs_std = round(np.std(qb_recs_sum), 1)

	rc_recs_mean = round(np.mean(rc_recs_sum), 1)
	rc_recs_std = round(np.std(rc_recs_sum), 1)



	yards_growth_rate_game = rc_yards_mean/qb_yards_mean
	recs_growth_rate_game = rc_recs_mean/qb_recs_mean


	qb_yards_ud = None
	rc_yards_ud = None


	if qb in ud_nfl and rec in ud_nfl:

		qb_yards_ud = ud_nfl[qb]['passing_yds']
		rc_yards_ud = ud_nfl[rec]['receiving_yds']


	distr_score = 0
	distr_hit = 0
	distr_total = 0

	rec_over = 0
	rec_under = 0
	rec_total = 0

	qb_over = 0
	qb_under = 0
	qb_total = 0



	for game in growth_yards:

		qb_yards = growth_yards[game][qb]
		rc_yards = growth_yards[game][rec]

		qb_recs = growth_recs[game][qb]
		rc_recs = growth_recs[game][rec]


		if qb_yards_ud and rc_yards_ud: 

			for i in range(len(qb_yards)):

				rc_yd, qb_yd = rc_yards[i], qb_yards[i]

				qb_low = qb_yards_mean - qb_yards_std
				qb_high = qb_yards_mean + qb_yards_std

				if qb_yd > qb_low and rc_yd < qb_high:

					qb_score = float(qb_yards_ud) - qb_yd
					rc_score = float(rc_yards_ud) - rc_yd


					if qb_score > 0: 
						qb_under += 1
					else: 
						qb_over += 1 


					if rc_score > 0:
						rec_under += 1
					else:
						rec_over += 1


					score = qb_score * rc_score
					
					scale_factor = 1
					miss_factor = 1.25

					if qb_yd > qb_yards_mean:
						scale_factor = 1.25

					if score >= 0:
						distr_score += scale_factor*math.log(score, 5)
						distr_hit += 1
					else:
						distr_score -= miss_factor*scale_factor*math.log(abs(score), 5)
						
					distr_total += 1

	distr_score = distr_score/distr_total
	distr_prob = round(distr_hit/distr_total, 4)

	
	print(distr_score)
	print(distr_prob)
	print(distr_total)

	return distr_prob, distr_score, distr_total, rc_yards_mean/qb_yards_mean, [rec_over, rec_under], [qb_over, qb_under], [qb_yards_ud, rc_yards_ud]




#########
# utils #
#########

def find_dtick(min_val, max_val, num_intervals):
	interval = (max_val-min_val)/num_intervals
	dtick = find_nearest(INTERVALS, interval)

	return dtick


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def format_title(title, subtitle=None, subtitle_font_size=13):
    title = f'<b>{title}</b>'
    if not subtitle:
        return title
    subtitle = f'<span style="color:#D6D6D6; font-size: {subtitle_font_size}px;">{subtitle}</span>'
    return f'{title}<br>{subtitle}'


def get_updated_time():
	tz = timezone('US/Eastern')
	date_now = datetime.now(tz) 
	time_str = date_now.strftime("%b %d %Y %H:%M UTC-4").upper()

	return time_str



########################
### temporary script ###
########################

growth_correlation(sys.argv[1], sys.argv[2])

find_ud_scores()

# correlation_rank()

# run_sim(sys.argv[1], sys.argv[2])

# growth_correlation(sys.argv[1], sys.argv[2])













