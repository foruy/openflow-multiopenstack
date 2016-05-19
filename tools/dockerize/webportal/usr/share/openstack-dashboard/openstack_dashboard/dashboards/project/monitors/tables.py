# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import logging

from django.conf import settings
from django.core import urlresolvers
from django import template
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import conf
from horizon import exceptions
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)
SNAPSHOT_READY_STATES = ("ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED")

POWER_STATES = {
    0: "NO STATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
    8: "FAILED",
    9: "BUILDING",
}

PAUSE = 0
UNPAUSE = 1
SUSPEND = 0
RESUME = 1


def is_deleting(instance):
    task_state = getattr(instance, "OS-EXT-STS:task_state", None)
    if not task_state:
        return False
    return task_state.lower() == "deleting"

class DetailLink(tables.LinkAction):
    name = "detail"
    verbose_name = _("Monitor Detail")
    url = "horizon:project:monitors:detail"
    classes = ("btn-launch", "btn-edit")

    def allowed(self, request, instance=None):
        if instance.status in ACTIVE_STATES and instance.host != 'sh_05.daolicloud.com':
            return True
        return False

    def get_link_url(self, instance):
        return urlresolvers.reverse(self.url, args=(instance.id,))


def get_ips(instance):
    template_name = 'project/instances/_instance_ips.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_size(instance):
    if hasattr(instance, "full_flavor"):
        size_string = _("%(name)s | %(RAM)s RAM | %(VCPU)s VCPU "
                        "| %(disk)s Disk")
        vals = {'name': instance.full_flavor.name,
                'RAM': sizeformat.mbformat(instance.full_flavor.ram),
                'VCPU': instance.full_flavor.vcpus,
                'disk': sizeformat.diskgbformat(instance.full_flavor.disk)}
        return size_string % vals
    return _("Not available")


def get_keyname(instance):
    if hasattr(instance, "key_name"):
        keyname = instance.key_name
        return keyname
    return _("Not available")


def get_power_state(instance):
    return POWER_STATES.get(int(getattr(instance, "power_state", 0)), '')


STATUS_DISPLAY_CHOICES = (
    ("resize", _("Resize/Migrate")),
    ("verify_resize", _("Confirm or Revert Resize/Migrate")),
    ("revert_resize", _("Revert Resize/Migrate")),
)


TASK_DISPLAY_CHOICES = (
    ("image_snapshot", _("Snapshotting")),
    ("resize_prep", _("Preparing Resize or Migrate")),
    ("resize_migrating", _("Resizing or Migrating")),
    ("resize_migrated", _("Resized or Migrated")),
    ("resize_finish", _("Finishing Resize or Migrate")),
    ("resize_confirming", _("Confirming Resize or Migrate")),
    ("resize_reverting", _("Reverting Resize or Migrate")),
    ("unpausing", _("Resuming")),
)


class InstancesFilterAction(tables.FilterAction):

    def filter(self, table, instances, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [instance for instance in instances
                if q in instance.name.lower()]


class InstanceTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("error", False),
    )
    name = tables.Column("name",
                         verbose_name=_("Instance Name"))
    instance_type= tables.Column("instance_type",
                              verbose_name=_("Instance Type"))
    address = tables.Column("address",
                            verbose_name=_("IP Address"),
                            attrs={'data-type': "ip"})
    #ext_ip = tables.Column("ext_ip", verbose_name=_("Gateway IP"))
    #gateway = tables.Column("gateway", verbose_name=_("Access Gateway (ssh)"))
    #idc = tables.Column("idc", verbose_name=_("IDC"))
    #az = tables.Column("availability_zone",
    #                   verbose_name=_("Availability Zone"))
    #size = tables.Column(get_size,
    #                     verbose_name=_("Size"),
    #                     attrs={'data-type': 'size'})
    #keypair = tables.Column(get_keyname, verbose_name=_("Key Pair"))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    #task = tables.Column("OS-EXT-STS:task_state",
    #                     verbose_name=_("Task"),
    #                     filters=(title, filters.replace_underscores),
    #                     status=True,
    #                     status_choices=TASK_STATUS_CHOICES,
    #                     display_choices=TASK_DISPLAY_CHOICES)
    #state = tables.Column(get_power_state,
    #                      filters=(title, filters.replace_underscores),
    #                      verbose_name=_("Power State"))
    created_at = tables.Column("created_at",
                            verbose_name=_("Uptime"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    class Meta:
        name = "monitors"
        verbose_name = _("Monitoring")
        row_actions = (DetailLink,)
