import logging
from django.conf import settings
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import tabs
from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.users import tables

from openstack_dashboard.dashboards.project.users \
    import base as project_base

LOG = logging.getLogger(__name__)

class ConsumptionTab(tabs.TableTab):
    table_classes = (tables.ConsumptionTable,)
    name = _("Consumption")
    slug = "consumption_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_consumptions_data(self):
        try:
            instances = api.proxy.server_list(self.request)
        except Exception:
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'),
                              ignore=True)
        try:
            resources = api.proxy.resource_list(self.request)
        except Exception:
            resources = []
            exceptions.handle(self.request,
                              _("Unable to retrieve resource list"))

        instance_dict = SortedDict([(inst.id, inst.name)
                                   for inst in instances])
        for res in resources:
            res.name = instance_dict.get(res.source_id, 'i-%s' % res.source_id[:8])
        return resources

class LoginTab(tabs.TableTab):
    table_classes = (tables.LoginTable,)
    name = _("Login")
    slug = "login_tab"
    usage_class = project_base.ProjectUsage
    template_name = ("project/users/_user.html")

    def __init__(self, *args, **kwargs):
        super(LoginTab, self).__init__(*args, **kwargs)
        if not issubclass(self.usage_class, project_base.BaseUsage):
            raise AttributeError("You must specify a usage_class attribute "
                                 "which is a subclass of BaseUsage.")

    def get_logins_data(self):
        try:
            self.usage = self.usage_class(self.request)
            self.usage.summarize(*self.usage.get_date_range())
        except Exception:
            self.usage = []
            exceptions.handle(self.request,
                              _("Unable to retrieve login list"))
        return self.usage.usage_list

    def get_context_data(self,request):
        context = super(LoginTab, self).get_context_data(request)
        context['form'] = self.usage.form
        return context

    #def get_logins_data(self):
    #    try:
    #        logins = api.proxy.user_login_get(self.request)
    #    except Exception:
    #        logins = []
    #        exceptions.handle(self.request,
    #                          _("Unable to retrieve login list"))
    #    return logins

class RecordTabs(tabs.TabGroup):
    slug = "comsumption_and_login"
    tabs = (ConsumptionTab, LoginTab,)
    sticky = True
