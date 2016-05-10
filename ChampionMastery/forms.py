from django import forms
from widgets import DataList
from models import Champions
class FindCounterPick(forms.Form):
    '''summoner_name = forms.CharField(label='Summoner name', max_length=100)
    region = forms.ChoiceField(choices=[(x, x.upper()) for x in ["br","eune","euw","kr","lan","las","na","oce","ru","tr"]],label='Region', initial='na')
    lane = forms.ChoiceField(choices=[(0, 'Mid'), (1, 'Top')])
    opponent_champion = forms.ChoiceField(widget=DataList, choices=[(x.champion_name, 'http://ddragon.leagueoflegends.com/cdn/6.9.1/img/champion/{0}'.format(x.image_name)) for x in Champions.objects.all().order_by('champion_name')])
    num_counters = forms.ChoiceField(choices=[(x + 1, x + 1) for x in range(10)], label="Number of counter picks to return")
        '''