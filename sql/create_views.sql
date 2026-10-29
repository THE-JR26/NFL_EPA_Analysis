CREATE OR REPLACE VIEW vw_qb_dashboard AS
SELECT 	
	q.game_id,
    p.player_name,
    t.team_abbr,
    t.team_name,
    
    q.team_results,
    
    q.qb_epa,
    q.dropbacks,
    
    q.completions,
    q.attempts,
    
    q.passing_yards,
    q.passing_tds,
    
    q.interceptions,
    q.sacks,
    
    q.cpoe,
    
    q.pass_epa,
    q.rush_epa,
    q.total_epa
    
FROM qb_game_stats q
JOIN players p
	ON q.qb_id = p.player_id
JOIN teams t
	ON q.team_id = t.team_idvw_qb_dashboard;
