# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from openstack_dashboard.dashboards.project.instances import views

INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'
INSTANCES_KEYPAIR = r'^(?P<instance_id>[^/]+)/(?P<keypair_name>[^/]+)/%s$'
VIEW_MOD = 'openstack_dashboard.dashboards.project.instances.views'


urlpatterns = patterns(VIEW_MOD,
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^choice/$', views.ChoiceView.as_view(), name='choice'),
    url(r'^network/$', 'network', name='network'),
    url(r'^network_type/$', 'network_type', name='network_type'),
    url(r'^quotas/$', 'quotas', name='quotas'),
    url(r'^launch/$', views.LaunchInstanceView.as_view(), name='launch'),
    #url(r'^launch/(?P<id>[^/]+)$', views.LaunchInstanceView.as_view(), name='launch'),
)
