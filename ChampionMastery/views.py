from datetime import timedelta, datetime
from django.http import HttpResponse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import urllib2
import json
import hashlib
import csv
import os
import pytz
from time import sleep

from FirstWin.models import RateLimitTimer
from main.settings import API_KEY
from models import Champions, Matchup
from models import ChampionMastery
from models import Summoners
from models import MatchList
from models import Match
from models import APIUsage
from forms import FindCounterPick
from django.shortcuts import redirect

# Create your views here.
def load_champions(request):
    if Champions.objects.exists():
        Champions.objects.all().delete()
    region = 'na'
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/static-data/{0}/v1.2/champion?dataById=True&champData=image&api_key={1}".format(region, API_KEY))
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        raise
    data = json.load(response)['data']
    for key,value in data.iteritems():
        champ=Champions(champion_id=key, champion_name=value['name'], image_name=value['image']['full'])
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

def load_matchups(is_mid, opponent_champion_id):
    matchups=[]
    filename = 'solo_mid_matchups.csv' if is_mid else 'solo_top_matchups.csv'
    csv_filepathname = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
    dataReader = csv.reader(open(csv_filepathname), delimiter=',', quotechar='"')
    for row in dataReader:
        if row[16] == str(opponent_champion_id):
            matchup = Matchup()
            matchup.champion_level=int(row[0])
            matchup.champion_points=int(row[1])
            matchup.chest_granted=row[2]
            matchup.highest_grade=row[3]
            matchup.champion_id=int(row[4])
            matchup.summoner_table_id=row[5]
            matchup.region=row[6]
            matchup.role=row[7]
            matchup.lane=row[8]
            matchup.queue=row[9]
            matchup.match_id=row[10]
            matchup.won=int(row[11])
            matchup.grade=row[12]
            matchup.chest=int(row[13])
            matchup.champion_level_avg=row[14]
            matchup.champion_level_diff=row[15]
            matchup.opponent_champion_id=int(row[16])
            matchup.matchup=row[17]
            matchups.append(matchup)
    return matchups

def get_champion_masteries(summoner_id, region):
    platforms = {'br':'br1', 'euw':'euw1', 'eune':'eun1', 'jp':'jp1', 'kr':'kr', 'lan':'la1', 'las':'la2', 'na':'na1', 'oce':'oc1', 'ru':'ru', 'tr':'tr1'}
    url = urllib2.Request("https://{0}.api.pvp.net/championmastery/location/{1}/player/{2}/champions?api_key={3}".format(region, platforms[region], summoner_id, API_KEY))
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
    champion_masteries = []
    for champ in data:
        c = (champ.get('championId', 'N/A'), champ.get('championLevel', 'N/A'))
        champion_masteries.append(c)
    return champion_masteries

def get_summoner_id(summoner_name, region):
    url_summoner_name = urllib2.quote(summoner_name.encode("utf8")).lower()
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/{0}/v1.4/summoner/by-name/{1}?api_key={2}".format(region, url_summoner_name, API_KEY))
    valid_regions = ["br","eune","euw","kr","lan","las","na","oce","ru","tr"]
    if region not in valid_regions:
        return -400
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if e.code == 429:
            num_seconds = 5
            if "Retry-After" in e.headers:
                num_seconds = e.headers.get("Retry-After")
            timers = RateLimitTimer.objects.filter(region=region)
            try:
                timer = timers[0]
            except:
                timer=RateLimitTimer(region=region)
            timer.next_check_time = datetime.now() + timedelta(seconds=num_seconds)
            timer.save()
            return -429
        else:
            return -e.code
    except urllib2.URLError:
        return -504

    data = json.load(response)
    try:
        return data.values()[0]["id"]
    except:
        return -404

def get_counters(matchups, champion_masteries, num_counters):
    counters = []
    for champ in champion_masteries:
        champion_id = champ[0]
        champion_level = champ[1]
        wins = 0
        games = 0
        for matchup in matchups:
            if matchup.champion_level == champion_level and matchup.champion_id == champion_id:
                games += 1
                if matchup.won:
                    wins += 1
        if games < 3:
            continue
        win_rate = float(wins)/games
        counter = (champion_id, win_rate, games)
        counters.append(counter)
    counters.sort(key=lambda tup: tup[1], reverse=True)
    if num_counters < len(counters):
        return counters[0:num_counters]
    return counters

def find_my_counterpick(request):
    img_url = 'http://ddragon.leagueoflegends.com/cdn/6.9.1/img/champion/{0}'
    if request.method == 'POST':
        form = FindCounterPick(request.POST)
        if form.is_valid():
            opponent = Champions.objects.filter(champion_name=form.cleaned_data['opponent_champion'])[0]
            matchups = load_matchups(form.cleaned_data['lane'] == '0', opponent.champion_id)
            summoner_id = get_summoner_id(form.cleaned_data['summoner_name'], form.cleaned_data['region'])
            if summoner_id == -404:
                return HttpResponse('Summoner name could not be found. Ensure spelling and region are correct.', status=404)
            if summoner_id == -429:
                return HttpResponse('Rate limit of Riot API exceeded. Try again soon.', status=429)
            if summoner_id < 0:
                return HttpResponse('Error occurred. Please ensure everything is correct and try again soon.',status=-summoner_id)
            champion_masteries = get_champion_masteries(summoner_id, form.cleaned_data['region'])
            counter_picks = get_counters(matchups, champion_masteries, int(form.cleaned_data['num_counters']))
            counters = []
            for counter in counter_picks:
                champ = Champions.objects.filter(champion_id=counter[0])[0]
                counters.append((champ.champion_name, img_url.format(champ.image_name), '{:10.2f}%'.format(counter[1] * 100) , '*' if counter[2] < 10 else ''))
            return render(request, 'counter_pick_results.html', {'counters': counters, 'lane': 'Mid' if form.cleaned_data['lane'] == '0' else 'Top', 'opponent': opponent.champion_name, 'opponent_img': img_url.format(opponent.image_name)})

    else:
        form = FindCounterPick()
    return render(request, 'counter_pick.html', {'form': form})