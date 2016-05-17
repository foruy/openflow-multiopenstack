from __future__ import division
import logging
import time
import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG=logging.getLogger(__name__)


class BaseUsage(object):
    show_terminated = False

    def __init__(self, request, project_id=None):
        self.project_id = project_id or request.user.id
        self.request = request
        self.summary = {}
        self.usage_list = []

    @property
    def today(self):
        return timezone.now()

    @staticmethod
    def get_start(year, month, day):
	start = datetime.datetime(year, month, day, 0, 0, 0)
        return timezone.make_aware(start, timezone.utc)
        #return start

    @staticmethod
    def get_end(year, month, day):
        end = datetime.datetime(year, month, day, 23, 59, 59)
        return timezone.make_aware(end, timezone.utc)
        #return end

    def get_instances(self):
        instance_list = []
        [instance_list.extend(u.server_usages) for u in self.usage_list]
        return instance_list

    def get_date_range(self):
        if not hasattr(self, "start") or not hasattr(self, "end"):
            args_start = args_end = (self.today.year,
                                     self.today.month,
                                     self.today.day)
            form = self.get_form()
            if form.is_valid():
                start = form.cleaned_data['start']
                end = form.cleaned_data['end']
                args_start = (start.year,
                              start.month,
                              start.day)
                args_end = (end.year,
                            end.month,
                            end.day)
            elif form.is_bound:
                messages.error(self.request,
                               _("Invalid date format: "
                                 "Using today as default."))
            else:
                start = self.today - datetime.timedelta(days=7)
                args_start = (start.year,start.month,start.day)
	        LOG.error(self.today)
        self.start = self.get_start(*args_start)
        self.end = self.get_end(*args_end)
        return self.start, self.end
    def init_form(self):
        #today = datetime.date.today()
        #first = datetime.date(day=1, month=today.month, year=today.year)
        #if today.day in range(7):
            #self.end = first - datetime.timedelta(days=1)
        self.end = self.today
            #self.start = datetime.date(day=1,
             #                          month=self.end.month,
              #                         year=self.end.year)
        self.start = self.end - datetime.timedelta(days=7)
        #else:
         #   self.end = today
          #  self.start = first
        return self.start, self.end

    def get_form(self):
        if not hasattr(self, 'form'):
            if any(key in ['start', 'end'] for key in self.request.GET):
                self.form = forms.DateForm(self.request.GET)
            else:
                init = self.init_form()
                self.form = forms.DateForm(initial={'start': init[0],
                                                    'end': init[1]})
        return self.form

    def get_usage_list(self, start, end):
        raise NotImplementedError("You must define a get_usage_list method.")

    def summarize(self, start, end):
        if start <= end and start <= self.today:
            start = timezone.make_naive(start, timezone.utc)
            end = timezone.make_naive(end, timezone.utc)
	    #LOG.error(end)
            try:
                self.usage_list = self.get_usage_list(start, end)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve usage information.'))
        elif end < start:
            messages.error(self.request,
                           _("Invalid time period. The end date should be "
                             "more recent than the start date."))
        elif start > self.today:
            messages.error(self.request,
                           _("Invalid time period. You are requesting "
                             "data from the future which may not exist."))

class ProjectUsage(BaseUsage):
    #show_terminated = True 
    def get_usage_list(self, start, end):
        #show_terminated = self.request.GET.get('show_terminated',
         #                                    self.show_terminated)
        instances = []
        user=api.proxy.user_login_list(self.request)
    	instance_list = []

        end=str(end)
        end=datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')  
        end=str(end)
        td=time.mktime(time.strptime(end,'%Y-%m-%d %H:%M:%S'))

        start=str(start)
        start=datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')  
        start=str(start)
        sd=time.mktime(time.strptime(start,'%Y-%m-%d %H:%M:%S'))

        for instance_list in user:
            if hasattr(instance_list, 'created_at'):
                end_time=instance_list.created_at
                end_time=time.mktime(time.strptime(end_time,'%Y-%m-%dT%H:%M:%S.000000'))
                if end_time <= td and end_time >= sd:
                    instances.append(instance_list)
        return instances
        #return user
