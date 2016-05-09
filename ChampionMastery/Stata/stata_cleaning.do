cd C:\Users\Ben\Documents\GitHub\lol-api-challenge-2\ChampionMastery\Stata
insheet using summoners.csv,clear
save summoners,replace
insheet using matchlist.csv,clear
save matchlist,replace
insheet using matches.csv,clear
save matches,replace
insheet using champion_masteries.csv,clear
save champion_masteries,replace
use matchlist,clear
drop id
rename match_id_id id
rename summoner_id_id summoner
rename summoner summoner_id
drop if match_used=="f"
tab queue
merge m:1 id region using matches
keep if _merge==3
drop _merge
gen won=0
forv x=0/9{
}
forv x=0/4{
replace won=1 if winner=="f" & summoner_id==summoner_`x'_id
}
forv x=5/9{
replace won=1 if winner=="t" & summoner_id==summoner_`x'_id
}
egen total_won=sum(won),by(match_id region)
egen total_played=count(won),by(match_id region)
drop if total_won*2!=total_played
drop total_won total_played
tab lane queue
replace lane="MIDDLE" if lane=="MID"
tab lane queue
tab role queue
bys queue:tab lane role
rename summoner_id summoner_table_id
save matches_used,replace

use summoners
rename id summoner_table_id
merge 1:m summoner_table_id region using matches_used

keep if _merge==3
tab summoner_used
keep if summoner_used=="t"
egen total_won=sum(won),by(match_id region)
egen total_played=count(won),by(match_id region)
tab total_played total_won
bys queue:tab total_played total_won
gen incomplete = 0
replace incomplete = 1 if regexm(queue,"3")&total_played!=6
replace incomplete = 1 if !regexm(queue,"3")&total_played!=10
drop _merge
save summoner_matches_used,replace

use champion_masteries
rename summoner_id_id summoner_table_id
merge 1:m summoner_table_id region champion_id using summoner_matches_used
drop if _merge==1

replace champion_level=0 if missing(champion_level)
replace champion_points=0 if missing(champion_points)
replace highest_grade="N/A" if missing(highest_grade)
replace chest_granted="f" if missing(chest_granted)
encode highest_grade,g(grade)
replace grade=grade/3
replace grade=5-grade
replace grade=grade-2/3 if !regexm(highest,"\+")&!regexm(highest,"-")
replace grade=grade+2/3 if regexm(highest,"\+")
replace grade=grade-1/3 if regexm(highest,"-")
replace grade=grade+5+1/3 if regexm(highest,"S")
replace grade=0 if regexm(highest,"N/A")
gen chest=chest_granted=="t"
save champion_summoner_matches_used,replace


egen champion_level_avg=mean(champion_level),by(match_id region lane role)
gen champion_level_diff=2*(champion_level-champion_level_avg)
gen opponent_champion_id=0
egen lane_role_match = group(match_id region lane role)
bys lane_:replace opponent_champion_id=champion_id[_n+1] if _n==1 & _N==2
bys lane_:replace opponent_champion_id=champion_id[_n-1] if _n==2 & _N==2

egen matchup = group(champion_id opponent_champion_id)
drop if regexm(queue,"3")
drop  id summoner_id summoner_priority summoner_used match_used match_priority winner summoner_0_id summoner_1_id summoner_2_id summoner_3_id summoner_4_id summoner_5_id summoner_6_id summoner_7_id summoner_8_id summoner_9_id total_won total_played incomplete _merge lane_role_match
save matchups,replace
keep if lane=="TOP"&role=="SOLO"
save solo_top_matchups,replace
use matchups,clear
keep if lane=="MIDDLE"&role=="SOLO"
save solo_mid_matchups,replace
