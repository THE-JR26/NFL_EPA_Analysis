-- Negative EPA Wins

SELECT 
	p.player_name,
    q.game_id,
    q.qb_epa,
    q.team_results
FROM qb_game_stats q
JOIN players p
	ON q.qb_id = p.player_id
WHERE q.qb_epa < 0
	AND q.team_results = 'W'
ORDER BY q.qb_epa ASC;
