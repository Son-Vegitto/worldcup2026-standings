import requests
import json

# Fetch raw tournament data
url = "https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json"
data = requests.get(url).json()

# Structures to track teams and assignments
team_to_group = {}
standings = {}

# 1. First Pass: Map teams to their assigned groups from the match schedules
for r in data.get("rounds", []):
    for m in r.get("matches", []):
        group_name = m.get("group")
        if group_name:
            team_to_group[m["team1"]] = group_name
            team_to_group[m["team2"]] = group_name

def init_team(team_name, g_name):
    if team_name not in standings:
        standings[team_name] = {
            "team": team_name, 
            "group": g_name,
            "points": 0, 
            "wins": 0, 
            "draws": 0, 
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0
        }

# 2. Second Pass: Process match scores and calculate statistics
for r in data.get("rounds", []):
    for m in r.get("matches", []):
        if m.get("score1") is not None and m.get("score2") is not None:
            t1, t2 = m["team1"], m["team2"]
            g1, g2 = team_to_group.get(t1, "Unknown"), team_to_group.get(t2, "Unknown")
            s1, s2 = int(m["score1"]), int(m["score2"])
            
            init_team(t1, g1)
            init_team(t2, g2)
            
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

# Calculate final goal differences
for team in standings.values():
    team["goal_difference"] = team["goals_for"] - team["goals_against"]

# 3. Group and Sort internally (Group Stage Logic)
groups_data = {}
for team_stats in standings.values():
    grp = team_stats["group"]
    if grp not in groups_data:
        groups_data[grp] = []
    groups_data[grp].append(team_stats)

# Sort teams inside each group: Points -> Goal Difference -> Goals For
for grp in groups_data:
    groups_data[grp] = sorted(
        groups_data[grp], 
        key=lambda x: (x["points"], x["goal_difference"], x["goals_for"]), 
        reverse=True
    )

# 4. Extract and rank the 3rd-place wild cards
third_place_teams = []
for grp, teams in groups_data.items():
    if len(teams) >= 3:
        third_place_teams.append(teams[2]) # Index 2 is the 3rd-place team

# Sort the 3rd place tracker overall
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

# Write final file to the public directory
with open("public/standings.json", "w") as f:
    json.dump(output_json, f, indent=4)
