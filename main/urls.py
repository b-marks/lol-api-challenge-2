from django.conf.urls import include, url

from FirstWin.views import estimate_first_win

from django.contrib import admin
admin.autodiscover()

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', estimate_first_win),
    url(r'^firstwin/(?P<summoner_name>[^/]+)/(?P<api_key>[0-9a-f-]+)/(?P<region>[a-z]+)$',estimate_first_win),
    url(r'^admin/', include(admin.site.urls)),
]
