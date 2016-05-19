import json
import logging

from horizon.views import APIView

from  horizon import exceptions

class IndexView(APIView):
    template_name = 'project/whitepaper/index.html'

    def get_data(self, request, context, *args, **kwargs):
        context['horizon_language'] = request.session.get('horizon_language', request.LANGUAGE_CODE)
        return context
