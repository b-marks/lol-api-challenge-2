from django import forms

class EstimateFirstWinForm(forms.Form):
    summoner_name = forms.CharField(label='Summoner name', max_length=100)
    region = forms.ChoiceField(choices=[(x, x) for x in ["br","eune","euw","kr","lan","las","na","oce","ru","tr"]], initial='na')