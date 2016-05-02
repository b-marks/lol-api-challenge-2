import urllib2
from datetime import timedelta, datetime
import json
from django.shortcuts import render
from django.http import HttpResponse
from forms import EstimateFirstWinForm
from main.settings import API_KEY
from models import EstimateFirstWin
from models import RateLimitTimer
# Create your views here.

def estimate_first_win(request):
    if request.method == 'GET':
        form = EstimateFirstWinForm()
        return render(request, 'firstwin.html', {"message": "", "form": form})
    form = EstimateFirstWinForm(request.POST)
    if not form.is_valid():
        return render(request, 'firstwin.html', {"message": "", "form": form})
    region = form.cleaned_data['region']
    summoner_name = form.cleaned_data['summoner_name']
    api_key = API_KEY
    timers = RateLimitTimer.objects.filter(region=region)
    try:
        timer = timers[0]
        if datetime.now() < timer.next_check_time:
            return HttpResponse(render(request, 'firstwin.html',{"message": "Rate limit exceeded. Try again in " + (timer.next_check_time-datetime.now()).seconds + " seconds.", "form": form}), status=429)
    except:
        pass
    models = EstimateFirstWin.objects.filter(summoner_name=summoner_name, region=region)
    try:
        model=models[0]
    except:
        url_summoner_name = urllib2.quote(summoner_name.encode("utf8")).lower()
        url = urllib2.Request("https://{0}.api.pvp.net/api/lol/{0}/v1.4/summoner/by-name/{1}?api_key={2}".format(region, url_summoner_name, api_key))
        http_error_responses = {
            400:"Bad request. Ensure API key, summoner name, and region are correct.",
            401:"Unauthorized request. Recheck your API key (first parameter) and try again.",
            404:"Summoner name \"" + summoner_name + "\" not found in region \"" + region + ".\" Recheck your summoner name and region and try again.",
            500:"Internal server error. Try again soon.",
            503:"Service unavailable. Try again soon."
        }
        valid_regions = ["br","eune","euw","kr","lan","las","na","oce","ru","tr"]
        if not region in valid_regions:
            return HttpResponse(render(request, 'firstwin.html',{"message": "Region must be one of: \"br\", \"eune\", \"euw\", \"kr\", \"lan\", \"las\", \"na\", \"oce\", \"ru\", or \"tr\"", "form": form}), status=400)
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
                return HttpResponse(render(request, 'firstwin.html',{"message": "Rate limit exceeded. Try again in " + num_seconds + " seconds.", "form": form}), status=429)
            else:
                return HttpResponse(render(request, 'firstwin.html',{"message": http_error_responses[e.code], "form": form}), status=e.code)
        except urllib2.URLError:
            return HttpResponse(render(request, 'firstwin.html',{"message": "Error connecting to the Riot API. Try again soon.", "form": form}), status=504)

        data = json.load(response)
        try:
            summoner_id = data.values()[0]["id"]
        except:
            return HttpResponse(render(request, 'firstwin.html',{"message": "Could not find summoner id for summoner name: " + summoner_name, "form": form}), status=404)

        model = EstimateFirstWin(summoner_name=summoner_name, region=region, summoner_id=summoner_id, first_win_time=datetime.utcfromtimestamp(0))
        model.save()
    url = urllib2.Request("https://{0}.api.pvp.net/api/lol/{0}/v1.3/game/by-summoner/{1}/recent?api_key={2}".format(region, model.summoner_id, api_key))
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
            return HttpResponse(render(request, 'firstwin.html',{"message": "Rate limit exceeded. Try again in " + num_seconds + " seconds.", "form": form}), status=429)
        else:
            return HttpResponse(render(request, 'firstwin.html',{"message": http_error_responses[e.code], "form": form}), status=e.code)
    except urllib2.URLError:
        return HttpResponse(render(request, 'firstwin.html',{"message": "Error connecting to the Riot API. Try again soon.", "form": form}), status=504)

    data = json.load(response)
    games = data["games"]
    dates = []
    for game in games:
        if game["gameType"]=="MATCHED_GAME" and game["ipEarned"] > 150:
            dates.append(datetime.utcfromtimestamp(game["createDate"] / 1000.0))

    match = 1
    if len(dates) < 1:
        match = 0
        for game in games:
            dates.append(datetime.utcfromtimestamp(game["createDate"] / 1000.0))
    dates.sort()
    worst_case_date = dates[-1]
    if not match:
        worst_case_date = dates[0]
    worst_case_date2 = worst_case_date + timedelta(0, 60 * 60 * 22)
    cur_time = datetime.utcnow()
    if worst_case_date2 < cur_time:
        message = "First win of the day is ready!"
    else:
        message = "In the worst case, your first win of the day will be ready "+str(getTime(worst_case_date2, cur_time))

    model.first_win_time = worst_case_date2
    model.save()
    return render(request, 'firstwin.html', {"message":message,"form":form})

def getTime(utc_time, cur_time_utc):
    local_time = utc_time
    return_value = "today"
    if local_time.time() < (cur_time_utc).time():
        return_value = "tomorrow"
    return_value += " at " + local_time.strftime("%I:%M%p").lstrip("0") + "."
    return return_value