from datetime import timedelta, datetime
from django.http import HttpResponse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import urllib2
import json
import hashlib
import pytz
from time import sleep

from FirstWin.models import RateLimitTimer
from main.settings import API_KEY
from models import Champions
from models import ChampionMastery
from models import Summoners
from models import MatchList
from models import Match
from models import APIUsage
from django.shortcuts import redirect

# Create your views here.
def load_champions(request):
    if Champions.objects.exists():
        return redirect('home')
    region = 'na'
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/static-data/{0}/v1.2/champion?dataById=True&api_key={1}".format(region, API_KEY))
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        raise
    data = json.load(response)['data']
    for key,value in data.iteritems():
        champ=Champions(champion_id=key, champion_name=value['name'])
        champ.save()
    return redirect('home')

def update_rate_limits(api_key, region):
    api_hash=hashlib.sha512(api_key.encode()).hexdigest()
    query=APIUsage.objects.filter(region=region, api_hash=api_hash)
    delete_query=query.filter(timestamp__lt=datetime.utcnow()-timedelta(seconds=10*60)).delete()
    ten_minute=query.filter(timestamp__gte=datetime.utcnow()-timedelta(seconds=10*60))
    ten_minute_count=ten_minute.count()
    ten_second=query.filter(timestamp__gte=datetime.utcnow()-timedelta(seconds=10))
    ten_second_count=ten_second.count()
    if ten_minute_count < 500 and ten_second_count < 10:
        usage=APIUsage(api_hash=api_hash, region=region)
        usage.save()
        return True
    else:
        wait_until_time=datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        if ten_minute_count >= 500:
            wait_until_time=ten_minute.order_by('timestamp')[0].timestamp+timedelta(seconds=60*10)
        if ten_second_count >= 10:
            wait_until_time_other=ten_second.order_by('timestamp')[0].timestamp+timedelta(seconds=10)
            wait_until_time=max(wait_until_time,wait_until_time_other)
        sleep((wait_until_time-datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds())
    return True

@csrf_exempt
def get_matchlist_and_champion_mastery(request, region=None, summoner_id=None):
    region = 'na' if region is None else region
    api_key = request.body if request.body else API_KEY

    #doing 2 requests
    proceed = update_rate_limits(api_key, region)
    if not proceed:
        return HttpResponse("Rate limit exceeded. Try again in a few seconds.", status=429)
    proceed = update_rate_limits(api_key, region)
    if not proceed:
        return HttpResponse("Rate limit exceeded. Try again in a few seconds.", status=429)
    if summoner_id is None:
        try:
            summoner_id = Summoners.objects.filter(summoner_used=False, region=region).order_by('-summoner_priority')[0].summoner_id
        except:
            return HttpResponse('No summoners in database',status=404)
    if not Summoners.objects.filter(summoner_id=summoner_id, region=region).exists():
        summoner = Summoners(summoner_id=summoner_id, region=region, summoner_priority=0)
        summoner.save()
    else:
        summoner = Summoners.objects.filter(summoner_id=summoner_id, region=region)[0]

    #match_list
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/{0}/v2.2/matchlist/by-summoner/{1}?beginTime=1430870400000&api_key={2}".format(region, summoner_id, api_key))
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if e.code == 429:
            num_seconds = 5
            if "Retry-After" in e.headers:
                num_seconds = int(e.headers.get("Retry-After"))
            timers = RateLimitTimer.objects.filter(region=region)
            try:
                timer = timers[0]
            except:
                timer=RateLimitTimer(region=region)
            timer.next_check_time = datetime.utcnow() + timedelta(seconds=num_seconds)
            timer.save()
            return HttpResponse("Rate limit exceeded. Try again in " + num_seconds + " seconds.", status=429)
        else:
            return HttpResponse(status=e.code)
    except urllib2.URLError:
        return HttpResponse("Error connecting to the Riot API. Try again soon.", status=504)
    data = json.load(response)['matches']
    for match in data:
        try:
            m2 = Match.objects.filter(match_id=match.get('matchId', 'N/A'), region=region)[0]
        except:
            m2 = Match(match_id=match.get('matchId', 'N/A'), region=region)
            m2.save()
        champion = Champions.objects.filter(champion_id=match.get('champion', 'N/A'))[0]
        m = MatchList(summoner_id=summoner, region=region, match_id=m2, champion=champion, role=match.get('role', 'N/A'), lane=match.get('lane', 'N/A'), queue=match.get('queue', 'N/A'))
        try:
            m.save()
        except:
            pass

    #champion_mastery
    platforms = {'br':'br1', 'euw':'euw1', 'eune':'eun1', 'jp':'jp1', 'kr':'kr', 'lan':'la1', 'las':'la2', 'na':'na1', 'oce':'oc1', 'ru':'ru', 'tr':'tr1'}
    url = urllib2.Request("https://{0}.api.pvp.net/championmastery/location/{1}/player/{2}/champions?api_key={3}".format(region, platforms[region], summoner_id, api_key))
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if e.code == 429:
            num_seconds = 5
            if "Retry-After" in e.headers:
                num_seconds = int(e.headers.get("Retry-After"))
            timers = RateLimitTimer.objects.filter(region=region)
            try:
                timer = timers[0]
            except:
                timer=RateLimitTimer(region=region)
            timer.next_check_time = datetime.utcnow() + timedelta(seconds=num_seconds)
            timer.save()
            return HttpResponse("Rate limit exceeded. Try again in " + num_seconds + " seconds.", status=429)
        else:
            return HttpResponse(status=e.code)
    except urllib2.URLError:
        return HttpResponse("Error connecting to the Riot API. Try again soon.", status=504)
    data = json.load(response)
    for champ in data:
        champion = Champions.objects.filter(champion_id=champ.get('championId', 'N/A'))[0]
        c = ChampionMastery(champion=champion, summoner_id=summoner, region=region, champion_level=champ.get('championLevel', 'N/A'), champion_points=champ.get('championPoints', 'N/A'), chest_granted=champ.get('chestGranted', 'N/A'), highest_grade=champ.get('highestGrade', 'N/A'))
        try:
            c.save()
        except:
            pass

    summoner.summoner_used=True
    summoner.save()
    return redirect('home')

@csrf_exempt
def get_match(request, region=None, match_id=None):
    region = 'na' if region is None else region
    api_key = request.body if request.body else  API_KEY
    proceed = update_rate_limits(api_key, region)
    if not proceed:
        return HttpResponse("Rate limit exceeded. Try again in a few seconds.", status=429)
    if match_id is not None:
        try:
            match = Match.objects.filter(match_id=match_id)[0]
        except:
            match = Match(match_id=match_id, region=region)
            match.save()
    else:
        try:
            match_priorities = MatchList.objects.filter(match_used=False, region=region).values('match_id').annotate(priority_sum=Sum('match_priority')).order_by('-priority_sum')[0]
            # if summoners have a higher priority than matches, then input a summoner's champion mastery and matchlist
            if Summoners.objects.filter(summoner_used=False, region=region).exists():
                if Summoners.objects.filter(summoner_used=False, region=region).order_by('-summoner_priority')[0].summoner_priority > 2 *match_priorities['priority_sum']:
                    return get_matchlist_and_champion_mastery(request, region, None)
            match = Match.objects.get(pk=match_priorities['match_id'])
            match_id = match.match_id
        except:
            return get_matchlist_and_champion_mastery(request, region, None)
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/{0}/v2.2/match/{1}?api_key={2}".format(region, match_id, api_key))
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if e.code == 429:
            num_seconds = 5
            if "Retry-After" in e.headers:
                num_seconds = int(e.headers.get("Retry-After"))
            timers = RateLimitTimer.objects.filter(region=region)
            try:
                timer = timers[0]
            except:
                timer=RateLimitTimer(region=region)
            timer.next_check_time = datetime.utcnow() + timedelta(seconds=num_seconds)
            timer.save()
            return HttpResponse("Rate limit exceeded. Try again in " + num_seconds + " seconds.", status=429)
        elif e.code == 404: #not sure why it gets this sometimes (perhaps match is too recent?)
            matchlists = MatchList.objects.filter(match_id=match, region=region)
            for matchlist in matchlists:
                matchlist.match_used = True
                matchlist.save()
            return get_matchlist_and_champion_mastery(request, region, None)
        else:
            return HttpResponse(status=e.code)
    except urllib2.URLError:
        return HttpResponse("Error connecting to the Riot API. Try again soon.", status=504)
    data = json.load(response)
    matchlist_tuples = {}
    for i, participant in enumerate(data['participants']):
        index = i % 5
        if participant.get('teamId', 'N/A') == 200:
            index += 5
        matchlist_tuples[participant.get('participantId', 'N/A')] = (index, MatchList(match_id=match, region=region, match_used=1, champion_id=participant.get('championId', 'N/A'), lane=participant.get('timeline', 'N/A').get('lane', 'N/A'), role=participant.get('timeline', 'N/A').get('role', 'N/A'), queue=data.get('queueType', 'N/A')))
    summoners = []
    num_summoners_used = 0
    for participant in data['participantIdentities']:
        participant_id = participant.get('participantId', 'N/A')
        try:
            summoner_id = participant.get('player', 'N/A').get('summonerId', 'N/A')
        except:
            continue
        if not Summoners.objects.filter(summoner_id=summoner_id, region=region).exists():
            summoner = Summoners(summoner_id=summoner_id, region=region, summoner_priority=0)
            summoner.save()
            summoners.append(summoner)
        else:
            summoner = Summoners.objects.filter(summoner_id=summoner_id, region=region)[0]
            if not summoner.summoner_used:
                summoners.append(summoner)
            else:
                num_summoners_used += 1
        matchlist_tuples[participant_id][1].summoner_id = summoner
        try:
            matchlist = MatchList.objects.filter(summoner_id=summoner, match_id=match, region=region)[0]
            matchlist.match_used = True
        except:
            matchlist = matchlist_tuples[participant_id][1]
        matchlist.save()
        setattr(match, 'summoner_'+str(matchlist_tuples[participant_id][0]), summoner)
    for summoner in summoners:
        summoner.summoner_priority += num_summoners_used
        summoner.save()
    for team in data['teams']:
        if team.get('teamId', 'N/A') == 200:
            match.winner = team.get('winner', 'N/A')
    match.save()
    return redirect('home')