from horizon import forms
from django.utils.translation import ugettext_lazy as _

class AddPeopleForm(forms.SelfHandlingForm):
    user_name = forms.CharField(label=_("UserName"))
    email = forms.CharField(label=_("Email"))
    def __init__(self, request, *args, **kwargs):
        super(AddPeopleForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        ###
        return True


