from django.utils.translation import ugettext_lazy as _

from horizon import forms

class SettingForm(forms.SelfHandlingForm):
    device = forms.ChoiceField(
        label=_("Select Gateway Device"),
        widget=forms.SelectWidget(attrs={'class': 'image-selector'},
                                  data_attrs=('size', 'display-name')))

    def __init__(self, request, *args, **kwargs):
        super(SettingForm, self).__init__(request, *args, **kwargs)
        self.fields['device'].choices = []

    def handle(self, request, data):
        return True
