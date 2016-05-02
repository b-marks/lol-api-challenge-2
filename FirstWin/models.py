from __future__ import unicode_literals

from django.db import models
# Create your models here.
class EstimateFirstWin(models.Model):
    summoner_name = models.CharField(max_length=100)
    region = models.CharField(max_length=10)
    summoner_id=models.CharField(max_length=10)
    first_win_time=models.DateField()

    class Meta:
        unique_together = (('summoner_name', 'region',),)

class RateLimitTimer(models.Model):
    region = models.CharField(max_length=10,unique=True)
    next_check_time = models.DateField()