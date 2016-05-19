# -*- coding: utf-8 -*-
from django import template
from django.shortcuts import render_to_response
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import tabs
import models

#dashboard page manage
class DashboardTab(tabs.Tab):
    name = _("Dashboard")
    slug = "dashboard"
    template_name = ("project/pertino/dashboard/detail.html")
    def get_context_data(self, request):
        try:
            context = super(DashboardTab, self).get_context_data(request)
            now = 1
            context["people_online"] = now 
            context["device_online"] = now
            context["total"] = now
            context["windows_quota"] = now 
            context["linux_quota"] = now
            context["android_quota"] = now
        except Exception:
            exceptions.handle(self.request)
        return context

#peopleview page manage
class PeopleViewTab(tabs.Tab):
    name = _("Peopleview")
    slug = "peopleview"
    template_name = ("project/pertino/people_view/peopleview.html")

#deviceview page manage
class DeviceViewTab(tabs.Tab):
    name = _("Deviceview")
    slug = "deviceview"
    template_name = ("project/pertino/device_view/deviceview.html")

#   def get_display_device(self): 
#       devices = [
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3053', 'name': 'Jimi',     'online': True,   'type': 'linux'  },
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3054', 'name': 'Louis',    'online': True,   'type': 'windows'},
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3055', 'name': 'Yanni',    'online': True,   'type': 'android'},
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3056', 'name': 'Ella',     'online': True,   'type': 'windows'},
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3057', 'name': 'Wesley',   'online': True,   'type': 'android'},
#           {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3058', 'name': 'Bono',     'online': True,   'type': 'linux'  },
#       ]
#       return devices
#
#   def get_context_data(self,request):
#       try:
#           display_list =self.get_display_device()
#           context = super(DeviceViewTab, self).get_context_data(request)
#           context["display_list"] = display_list
#       except Exception:
#           exceptions.handle(self.request)
#       return context

#setting page manage
class SettingsTab(tabs.Tab):
    name = _("Settings")
    slug = "settings"
    template_name = ("project/pertino/settings/detail.html")


#tabgroup  include all display tabs
class PertinoTabs(tabs.TabGroup):
    slug = "pertino"
    tabs = (DashboardTab,PeopleViewTab,DeviceViewTab,)
    sticky = True
