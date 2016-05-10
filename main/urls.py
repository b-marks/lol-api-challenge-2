from django.conf.urls import include, url

from FirstWin.views import estimate_first_win

from ChampionMastery.views import load_champions
from ChampionMastery.views import get_matchlist_and_champion_mastery
from ChampionMastery.views import get_match
from ChampionMastery.views import find_my_counterpick

from django.contrib import admin
admin.autodiscover()

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', find_my_counterpick, name='home'),
    url(r'^firstwin/(?P<summoner_name>[^/]+)/(?P<api_key>[0-9a-f-]+)/(?P<region>[a-z]+)$', estimate_first_win),
    url(r'^firstwin/$', estimate_first_win),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^champs/$',load_champions),
    url(r'^match_list(/(?P<region>[a-z]+)(/(?P<summoner_id>\d+))?)?/$',get_matchlist_and_champion_mastery),
    url(r'^match(/(?P<region>[a-z]+)(/(?P<match_id>\d+))?)?/$',get_match),
    url(r'^get_counter_pick/$', find_my_counterpick),
]
