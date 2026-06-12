import requests
import json

# Fetch raw tournament data
url = "https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json"
data = requests.get(url).json()

team_to_group = {}
standings = {}

# Helper to initialize a team with default zero stats
def init_team(team_name, g_name):
    if team_name not in standings:
        standings[team_name] = {
            "team": team_name, 
            "group": g_name,
            "wins": 0, 
            "draws": 0, 
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0
        }

# 1. Map all teams to their assigned groups and initialize with zero stats
for m in data.get("matches", []):
    group_name = m.get("group")
    if group_name:
        team_to_group[m["team1"]] = group_name
        team_to_group[m["team2"]] = group_name
        init_team(m["team1"], group_name)
        init_team(m["team2"], group_name)

# 2. Process match scores using the correct nested "score" -> "ft" format
for m in data.get("matches", []):
    score_obj = m.get("score")
    if score_obj and isinstance(score_obj, dict):
        ft_score = score_obj.get("ft")
        # Ensure 'ft' exists and contains exactly two scores [score1, score2]
        if ft_score and len(ft_score) == 2:
            t1, t2 = m["team1"], m["team2"]
            s1, s2 = int(ft_score[0]), int(ft_score[1])
            
            # Update goals
            standings[t1]["goals_for"] += s1
            standings[t1]["goals_against"] += s2
            standings[t2]["goals_for"] += s2
            standings[t2]["goals_against"] += s1
            
            # Record outcome
            if s1 > s2:
                standings[t1]["points"] += 3
                standings[t1]["wins"] += 1
                standings[t2]["losses"] += 1
            elif s2 > s1:
                standings[t2]["points"] += 3
                standings[t2]["wins"] += 1
                standings[t1]["losses"] += 1
            else:
                standings[t1]["points"] += 1
                standings[t2]["points"] += 1
                standings[t1]["draws"] += 1
                standings[t2]["draws"] += 1

# Calculate final goal differences for initialized teams
for team in standings.values():
    team["goal_difference"] = team["goals_for"] - team["goals_against"]

# 3. Structure by Group and Sort
groups_data = {}
for team_stats in standings.values():
    grp = team_stats["group"]
    if grp not in groups_data:
        groups_data[grp] = []
    groups_data[grp].append(team_stats)

# Sort: Points -> Goal Difference -> Goals For -> Team Name (Alphabetical fallback)
for grp in groups_data:
    groups_data[grp] = sorted(
        groups_data[grp], 
        key=lambda x: (x["points"], x["goal_difference"], x["goals_for"], x["team"].lower()), 
        reverse=True
    )

# 4. Extract and rank the 3rd-place wild cards
third_place_teams = []
for grp, teams in groups_data.items():
    if len(teams) >= 3:
        third_place_teams.append(teams[2])

third_place_ranked = sorted(
    third_place_teams, 
    key=lambda x: (x["points"], x["goal_difference"], x["goals_for"]), 
    reverse=True
)

# Build unified output structure
output_json = {
    "groups": groups_data,
    "third_place_leaderboard": third_place_ranked
}

# Write final file to public directory
with open("public/standings.json", "w") as f:
    json.dump(output_json, f, indent=4)
