from collections import defaultdict
from itertools import combinations


# number of 16x slip sets
NUM_SETS = 30
# update depending on performances, injuries, roster changes, etc.
TIER_LIST = [
    ["bears", "vikings"], # dolphins, rams ineligible week 3
    ["cardinals", "falcons"],  
    ["buccaneers", "saints", "raiders", "bengals"]
]

# just to match spreadsheet order/formatting consistency
tier_rank = {
    'bears': 1.1, 'vikings': 1.2,
    'cardinals': 2.1,'falcons': 2.2,
    'buccaneers': 3.1, 'saints': 3.2,  'raiders': 3.4, "bengals": 3.5
}

# max ratio of total slips
TIER_WEIGHTS = [0.4, 0.3, 0.25]

# list of games that week
# WEEKLY_GAMES = [
#     ("pats", "jets"),
#     ("giants", "browns"),
#     ("packers", "titans"),
#     ("bears", "colts"),
#     ("texans", "vikings"),
#     ("eagles", "saints"),
#     ("chargers", "steelers"),
#     ("broncos", "buccaneers"),
#     ("panthers", "raiders"),
#     ("dolphins", "seahawks"),
#     ("ravens", "cowboys"),
#     ("49ers", "rams"),
#     ("lions", "cardinals"),
#     ("chiefs", "falcons")
# ]

WEEKLY_GAMES = [
    ("saints", "falcons"),
    ("rams", "bears"),
    ("vikings", "packers"),
    ("steelers", "colts"),
    ("broncos", "jets"),
    ("eagles", "buccaneers"),
    ("bengals", "panthers"),
    ("jaguars", "texans"),
    ("commanders", "cardinals"),
    ("pats", "49ers"),
    ("browns", "raiders"),
    ("chiefs", "chargers"),
    ("bills", "ravens")
]


def is_subset(arr1, arr2):
    return set(arr1).issubset(set(arr2))


# do not touch below #

# Generate list of tuples with team and its index
teams = [(team, tier_index) for tier_index, tier in enumerate(TIER_LIST) for team in tier]

ineligible = {team1: team2 for team1, team2 in WEEKLY_GAMES}

# print(teams)

for team1, team2 in WEEKLY_GAMES:
    ineligible[team2] = team1

set_count = defaultdict(int)
pair_count = defaultdict(lambda: defaultdict(int))

res = []


def is_eligible(cmb): 

    teams = {team for team, _ in cmb}
    if teams in res:
        return False

    for team, tier in cmb: 
        # same game
        if ineligible[team] in teams:
            return False
        # team usage limit
        if set_count[team] > NUM_SETS*TIER_WEIGHTS[tier]:
            return False
        
    for i in range(len(cmb)):

        t1, t1_tier = cmb[i][0],  cmb[i][1]

        for j in range(i+1, len(cmb)):

            t2, t2_tier = cmb[j][0],  cmb[j][1]

            # pair_limit = 1.5*NUM_SETS*(TIER_WEIGHTS[t1_tier]*TIER_WEIGHTS[t2_tier])

            # if pair_count[t1][t2] >= pair_limit:
            #     return False

            if len(res) > 0 and is_subset([t1,t2], res[-1]):
                return False

            
    return True


def update_count(teams):
    teams = list(teams)
    for i in range(len(teams)):

        t1 = teams[i]
        set_count[t1] += 1

        for j in range(i+1, len(teams)):

            t2 = teams[j]

            pair_count[t1][t2] += 1
            pair_count[t2][t1] += 1

    return


combinations_of_4 = combinations(teams,4)
combination_scores = defaultdict()

for cmb in combinations_of_4:
    score = 1
    for c in cmb:
        team, tier_weight = c[0], TIER_WEIGHTS[c[1]]
        score *= tier_weight

    combination_scores[cmb] = score

print(combination_scores)

sorted_combination_keys = sorted(combination_scores, key=combination_scores.get, reverse=True)




# while len(res) < 22:
#     print(len(res))

for cmb in sorted_combination_keys: 

    if is_eligible(cmb):

        teams = {team for team, _ in cmb}
        res.append(sorted(list(teams)))

        update_count(teams)

# just to match spreadsheet order/formatting consistency
# tier_rank = {
#     'cowboys': 1, 'vikings': 1.2, 'lions': 1.3,
#     'seahawks': 2.1, 'jets': 2.2, 'cardinals': 2.3,
#     'saints': 3.1, 'buccaneers': 3.2, 'bears': 3.3, '49ers': 3.4
# }

# Sort each sublist based on tier ranking
sorted_res = [
    sorted(sublist, key=lambda team: tier_rank.get(team, float('inf')))
    for sublist in res
]

sorted_res.sort(key=lambda sublist: tier_rank.get(sublist[0], float('inf')))


print(len(sorted_res))
for r in sorted_res:
    print('\t'.join(r))


print('\n')
print(set_count)
print('\n')

for k,v in pair_count.items():
    print(k)
    print(v)

