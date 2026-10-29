CREATE TABLE teams (
	team_id 				SERIAL PRIMARY KEY,
    team_abbr 				VARCHAR(5) NOT NULL UNIQUE, -- e.q 'CIN'
    team_name 				VARCHAR(50) NOT NULL -- e.g 'Cincinnati Bengals'
);

CREATE TABLE players (
	player_id 				SERIAL PRIMARY KEY,
    gsis_id					VARCHAR(20) UNIQUE, -- NFL ID
    player_name 			VARCHAR(100) NOT NULL,
    position 				VARCHAR(5) NOT NULL -- e.g. 'QB'
);

CREATE TABLE games (
	game_id 				SERIAL PRIMARY KEY,teams
    season					INT NOT NULL,
    week 					INT NOT NULL,
    home_team_id 			INT NOT NULL references teams(team_id),
    away_team_id 			INT NOT NULL references teams(team_id),
    home_score 				INT NOT NULL,
    away_score 				INT NOT NULL,
    game_date 				DATE NOT NULL
);

CREATE TABLE qb_game_stats(
    qb_game_id 				BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    game_id					VARCHAR(20) NOT NULL, 
    team_id 				INT NOT NULL references teams(team_id),
    qb_id 					INT NOT NULL references players(player_id),
    
    dropbacks 				INT NOT NULL,
    qb_epa 					DECIMAL(8,4) NOT NULL, -- EPA per dropback
    pass_epa 				DECIMAL(8,4),
    rush_epa 				DECIMAL(8,4), -- QB rushing EPA
    total_epa 				DECIMAL(8,4), -- QB total EPA
    
    completions 			INT,
    attempts 				INT,
    passing_yards   		INT,
    passing_tds				INT,
    interceptions			INT,
    sacks					INT,
    
    cpoe					DECIMAL(6,2), -- Completion % over expected
    pressure_rate 			DECIMAL(6,2), 
    success_rate 			DECIMAL(6,2), 	
    explosive_plays			INT, -- plays > X yards
    
    team_results			VARCHAR(1) NOT NULL 	-- 'W' or 'L'
);

DROP TABLE IF EXISTS team_game_stats;

CREATE TABLE team_game_stats (
	team_game_id 			SERIAL PRIMARY KEY,
    game_id					VARCHAR(20),
    team_id 				INT NOT NULL references teams(team_id),
    
    total_off_epa 			NUMERIC(8,4), 		
    rush_epa 				NUMERIC(8,4),
    pass_epa				NUMERIC(8,4),
    
    turnovers				INT,
    opponent_turnovers 	INT,
    explosive_plays			INT,
    success_rate			NUMERIC(6,2),
    pressure_rate			NUMERIC(6,2)
);

