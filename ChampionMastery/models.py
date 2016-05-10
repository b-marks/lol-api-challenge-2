from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Summoners(models.Model):
    summoner_id=models.CharField(max_length=100, db_index=True)
    summoner_priority=models.IntegerField(default=1, db_index=True)
    summoner_used=models.BooleanField(default=False, db_index=True)
    region=models.CharField(max_length=10, db_index=True)
    class Meta:
        unique_together = (('summoner_id', 'region'),)

class Champions(models.Model):
    champion_id=models.IntegerField(unique=True)
    champion_name=models.CharField(max_length=100)
    image_name=models.CharField(max_length=256)

class ChampionMastery(models.Model):
    champion=models.ForeignKey('Champions', to_field='champion_id', on_delete=models.CASCADE)
    summoner_id=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE)
    champion_level=models.IntegerField()
    champion_points=models.IntegerField()
    chest_granted=models.BooleanField()
    highest_grade=models.CharField(max_length=100)
    region=models.CharField(max_length=10, db_index=True)
    class Meta:
        unique_together = (('champion', 'summoner_id', 'region'),)

class MatchList(models.Model):
    summoner_id=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE)
    region=models.CharField(max_length=10, db_index=True)
    match_id=models.ForeignKey('Match', to_field='id', on_delete=models.CASCADE)
    match_used=models.BooleanField(default=False, db_index=True)
    match_priority=models.IntegerField(default=1, db_index=True)
    champion=models.ForeignKey('Champions', to_field='champion_id', on_delete=models.CASCADE)
    role=models.CharField(max_length=100)
    lane=models.CharField(max_length=100)
    queue=models.CharField(max_length=100)
    class Meta:
        unique_together = (('summoner_id', 'match_id', 'region'),)

class Match(models.Model):
    match_id=models.CharField(max_length=100, db_index=True)
    region=models.CharField(max_length=10, db_index=True)
    winner=models.NullBooleanField(null=True)  # False if blue side, True if red side
    #blue side
    summoner_0=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_0', null=True)
    summoner_1=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_1', null=True)
    summoner_2=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_2', null=True)
    summoner_3=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_3', null=True)
    summoner_4=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_4', null=True)
    #red side
    summoner_5=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_5', null=True)
    summoner_6=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_6', null=True)
    summoner_7=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_7', null=True)
    summoner_8=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_8', null=True)
    summoner_9=models.ForeignKey('Summoners', to_field='id', on_delete=models.CASCADE, related_name='summoner_9', null=True)
    class Meta:
        unique_together = (('match_id', 'region'),)

class APIUsage(models.Model):
    api_hash=models.CharField(max_length=512, db_index=True)
    region=models.CharField(max_length=10, db_index=True)
    timestamp=models.DateTimeField(auto_now_add=True, db_index=True)

class Matchup():
    champion_level=0
    champion_points=0
    chest_granted='f'
    highest_grade='N/A'
    champion_id=0
    summoner_table_id=0
    region='na'
    role='SOLO'
    lane='TOP'
    queue='TEAM_BUILDER_DRAFT_RANKED_5x5 '
    match_id=0
    won=0
    grade=0
    chest=0
    champion_level_avg=0
    champion_level_diff=0
    opponent_champion_id=0
    matchup=0