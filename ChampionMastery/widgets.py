from django import forms
from itertools import chain
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode

'''
Adapted from https://pypi.python.org/pypi/django-form-extensions/0.1.2b4
'''


class DataList(forms.TextInput):
    def __init__(self, attrs=None, choices=()):
        super(DataList, self).__init__(attrs)
        self.choices = list(choices)

    def render(self, name, value, attrs={}, choices=()):
        attrs['list'] = u'id_%s_list' % name
        output = super(DataList, self).render(name, value, attrs)
        output += u'\n' + self.render_options(name, choices)
        return output

    def render_options(self, name, choices):
        output = []
        output.append(u'<datalist id="id_%s_list" style="display:none">' % name)
        output.append(u'<select name="%s_select"' % name)
        for option in chain(self.choices, choices):
            output.append(u'<option value="{0}" data-image="{1}"></option>'.format(conditional_escape(force_unicode(option[0])),option[1]))
        output.append(u'</select>')
        output.append(u'</datalist>')
        return u'\n'.join(output)