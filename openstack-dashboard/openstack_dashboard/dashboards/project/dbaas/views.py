import json
import logging

from django.http import HttpResponse
from horizon.views import APIView

from  horizon import exceptions

class IndexView(APIView):
    template_name = 'project/dbaas/index.html'

    def get_data(self, request, context, *args, **kwargs):
        return context

