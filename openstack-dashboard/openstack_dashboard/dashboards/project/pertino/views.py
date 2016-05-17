
from horizon import forms
from horizon import tabs
from horizon import exceptions
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard.dashboards.project.pertino import tabs as project_tabs
from openstack_dashboard.dashboards.project.pertino import forms as pertino_forms

class IndexView(tabs.TabView):
    tab_group_class = project_tabs.PertinoTabs
    template_name = 'project/pertino/index.html'

class AddView(forms.ModalFormView):
    form_class = pertino_forms.AddPeopleForm
    template_name = 'project/pertino/people_view/add.html'
    success_url = reverse_lazy('horizon:project:pertino:index')

    def get_context_data(self, **kwargs):
        context = super(AddView, self).get_context_data(**kwargs)
        return context

def get_all_dev(): 
    devices = get_devices_bynetworkid('1')
    return devices

def get_online_dev(): 
    devices = [
        {'id': 'a5edf6a5-a5ed-4cab-baa6-18b021bb3053', 'name': 'Jimi', 'status'  : 'online',   'type': 'linux'  },
    ]
    return devices

def device_display(request, display_type):
    all_dev_list=get_all_dev()
    online_dev_list=get_online_dev()
    if display_type == "dev_all":
        return render_to_response("project/pertino/device_view/device_display.html", {'display_list': all_dev_list})
    elif display_type == "dev_online":
        return render_to_response("project/pertino/device_view/device_display.html", {'display_list': online_dev_list})
    else:
        exceptions.handle(self.request)
#def device_display(request, device_id):
#    device = get_devices_bydeviceid(device_id)    
#    return render_to_response("project/pertino/device_view/device_display.html", {'display_list': all_dev_list})
