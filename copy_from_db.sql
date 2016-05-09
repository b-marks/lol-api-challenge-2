\COPY public."ChampionMastery_matchlist" TO 'matchlist.csv' DELIMITER ',' CSV HEADER;
\COPY public."ChampionMastery_match" TO 'matches.csv' DELIMITER ',' CSV HEADER;
\COPY public."ChampionMastery_summoners" TO 'summoners.csv' DELIMITER ',' CSV HEADER;
\COPY public."ChampionMastery_championmastery" TO 'champion_masteries.csv' DELIMITER ',' CSV HEADER;