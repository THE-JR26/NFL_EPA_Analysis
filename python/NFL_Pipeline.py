import pandas as pd
from sqlalchemy import create_engine

# ================ LOAD TEAMS ================

# Load parquet file
# Load raw pbp date
from pathlib import Path

file_path = Path(r"C:\Users\rendo\OneDrive\Documents\NFL Project EPA\pbp_2023_2026.parquet")

print(file_path.exists())

pbp = pd.read_parquet(file_path)

# Connect to MySQL database
engine = create_engine("mysql+pymysql://root:password@localhost:3306/nfl_analytics")

# Extract unique teams
teams = (
    pd.concat([pbp['home_team'], pbp['away_team']])
    .dropna()
    .drop_duplicates()
    .to_frame(name = 'team_abbr')
)

teams['team_name'] = teams['team_abbr'] # You can map full names later

# Check existing teams
existing_teams = pd.read_sql("SELECT team_abbr FROM teams", engine)

# Insert only new teams
new_teams = teams[~teams['team_abbr'].isin(existing_teams['team_abbr'])]

if not new_teams.empty:
    new_teams.to_sql('teams', engine, if_exists = 'append', index = False)
    print("Inserted new teams:", new_teams.shape)
else:
    print("Teams already loaded, skipping insert")

# ================ INSERT PLAYERS (QBs) ================

# Extract unique QB rows
qbs = (
    pbp[['passer_id', 'passer']]
    .dropna()
    .drop_duplicates()
    .rename(columns = {'passer_id': 'gsis_id', 'passer': 'player_name'})
)

# Add position column 
qbs['position'] = 'QB'

# Check existing players
existing_players = pd.read_sql("SELECT gsis_id FROM players", engine)

# Insert only new players
new_players = qbs[~qbs['gsis_id'].isin(existing_players['gsis_id'])]

if not new_players.empty:
    new_players.to_sql('players', engine, if_exists = 'append', index = False)
    print("Inserted new players:", new_players.shape)
else:
    print("Players already loaded, skipping insert")

# ================ INSERT GAMES ================

# Extract unique game-level rows
games = pbp[['game_id', 'season', 'week', 'home_team', 'away_team', 
             'home_score', 'away_score', 'game_date']].drop_duplicates()

# Load team lookup from MySQL
team_lookup = pd.read_sql("SELECT team_id, team_abbr FROM teams", engine)

# Map home_team -> home_team_id
games = games.merge(team_lookup, left_on = 'home_team', right_on = 'team_abbr') \
             .rename(columns = {'team_id': 'home_team_id'}) \
             .drop(columns = ['team_abbr'])

# Map away_team -> away_team_id
games = games.merge(team_lookup, left_on = 'away_team', right_on = 'team_abbr') \
             .rename(columns = {'team_id': 'away_team_id'}) \
             .drop(columns = ['team_abbr'])

games_final = games[['game_id', 'season', 'week',
                     'home_team_id', 'away_team_id',
                      'home_score', 'away_score', 'game_date']]

# Check existing games
existing_games = pd.read_sql("SELECT game_id FROM games", engine)

# Insert only new games
new_games = games_final[~games_final['game_id'].isin(existing_games['game_id'])]

if not new_games.empty:
    new_games.to_sql('games', engine, if_exists = 'append', index = False)
    print("Inserted new games:", new_games.shape)
else:
    print("Games already loaded, skipping insert")

# ================ QB GAME STATS ================

qb_stats = (
    pbp.groupby(['game_id', 'passer_id', 'passer'])
       .agg({
           'qb_epa': 'sum',
           'qb_dropback': 'sum',
           'complete_pass': 'sum',
           'pass_attempt': 'sum',
           'passing_yards': 'sum',
           'interception': 'sum',
           'sack': 'sum',
           'cpoe' : 'mean'
       })
       .reset_index()
)


# Load games table for team_id mapping
games_table = pd.read_sql("""SELECT game_id, home_team_id, away_team_id, home_score, away_score, season, week  FROM games""", engine)

qb_stats = qb_stats.merge(
    games_table[['game_id', 'home_team_id', 'away_team_id', 'home_score', 'away_score', 'season', 'week']],
    on='game_id',
    how='left'
)

# Get actual QB team from play-by-play data
qb_team_lookup = (
    pbp[['game_id', 'passer_id', 'posteam']]
    .dropna(subset=['passer_id'])
    .drop_duplicates()
)

qb_stats = qb_stats.merge(
    qb_team_lookup,
    on=['game_id', 'passer_id'],
    how='left'
)

# Convert team abbreviation to team_id
qb_stats = qb_stats.merge(
    team_lookup,
    left_on='posteam',
    right_on='team_abbr',
    how='left'
)

# Determine win/loss
qb_stats['team_results'] = qb_stats.apply(
    lambda row: 'W' if (
        (row ['team_id'] == row ['home_team_id'] and row ['home_score'] > row ['away_score']) or
        (row ['team_id'] == row ['away_team_id'] and row ['away_score'] > row ['home_score'])
    )else 'L',
    axis = 1
)

# Rename columns 
qb_stats = qb_stats.rename(columns = {
    'passer_id' : 'gsis_id',
    'passer' : 'player_name',
    'qb_dropback' : 'dropbacks',
    'game_id_y' : 'game_id'
})

# Get player IDs from database
player_lookup = pd.read_sql(
    "SELECT  player_id, gsis_id FROM players",
    engine
)

# Match gsis_id to player_id
qb_stats = qb_stats.merge(
    player_lookup,
    on='gsis_id',
    how='left'
)

# Rename players_id -> qb_id
qb_stats = qb_stats.rename(columns={
    'player_id' : 'qb_id'
})

# Check existing QB game stats
existing_qb_stats = pd.read_sql(
    "SELECT game_id, qb_id FROM qb_game_stats",
    engine
)

merge_qb = qb_stats.merge(
    existing_qb_stats,
    on=['game_id', 'qb_id'],
    how='left',
    indicator=True
)

new_qb_stats = merge_qb[merge_qb['_merge'] == 'left_only'].drop(columns=['_merge'])

# Rename columns to match SQL table
new_qb_stats = new_qb_stats.rename(columns={
    'complete_pass': 'completions',
    'pass_attempt': 'attempts',
    'interception': 'interceptions',
    'sack': 'sacks'
})

# Keep ONLY columns that exist in qb_game_stats table
new_qb_stats = new_qb_stats[
    [
        'game_id',
        'team_id',
        'qb_id',
        'dropbacks',
        'qb_epa',
        'completions',
        'attempts',
        'passing_yards',
        'interceptions',
        'sacks',
        'cpoe',
        'team_results'
    ]
]

if not new_qb_stats.empty:
    new_qb_stats.to_sql(
        'qb_game_stats',
        engine,
        if_exists='append',
        index=False
    )
    print("Inserted new QB game stats:", new_qb_stats.shape)
else:
    print("QB game stats already loaded, skipping insert")

# ================ TEAM GAME STATS ================

team_stats = (
    pbp.groupby(['game_id', 'posteam'])
        .agg({
             'epa': 'sum',
             'success': 'sum',
             'play': 'sum',
         })
         .reset_index()
         .rename(columns = {'posteam': 'team_abbr'})
)

team_stats = team_stats.rename(columns={
    'epa' : 'total_off_epa'
})

# Map team_abbr to team_id
team_stats = team_stats.merge(team_lookup, on = 'team_abbr')

# Add game metadata
team_stats = team_stats.merge(
    games_table[['game_id', 'season', 'week', 'home_team_id', 'away_team_id',
                 'home_score', 'away_score']],
    on = 'game_id'
)

# Determine win/loss
team_stats['team_results'] = team_stats.apply(
    lambda row: 'W' if (
        (row['team_id'] == row['home_team_id'] and row['home_score'] > row['away_score']) or
        (row['team_id'] == row['away_team_id'] and row['away_score'] > row['home_score'])
    ) else 'L',
    axis = 1
)

# Check existing team game stats
existing_team_stats = pd.read_sql("SELECT game_id, team_id FROM team_game_stats", engine)

merge_team = team_stats.merge(existing_team_stats, on = ['game_id', 'team_id'], how = 'left', indicator = True)
new_team_stats = merge_team[merge_team['_merge'] == 'left_only'].drop(columns = ['_merge'])

# Rename to match SQL schema
new_team_stats = new_team_stats.rename(columns={
    'epa' : 'total_off_epa',
    'success' : 'success_rate'
})

new_team_stats = new_team_stats[
    [
        'game_id',
        'team_id',
        'total_off_epa',
        'success_rate'
    ]
]

if not new_team_stats.empty:
    new_team_stats.to_sql('team_game_stats', engine, if_exists = 'append', index = False)
    print("Inserted new team game stats:", new_team_stats.shape)
else:
    print("Team game stats already loaded, skipping insert")

