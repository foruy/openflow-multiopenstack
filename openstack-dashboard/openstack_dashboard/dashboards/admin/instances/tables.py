from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables

class AdminUpdateRow(project_tables.UpdateRow):
    def get_data(self, request, instance_id):
        instance = super(AdminUpdateRow, self).get_data(request, instance_id)
        user = api.proxy.user_get(instance.user_id)
        instance.user_name = getattr(user, "name", None)
        return instance

def get_ips(instance):
    ips = [addr['address'] for addr in instance.addresses]
    return '/'.join(ips)

class AdminInstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )

    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("unknown", True),
        ("error", False),
    )
    user = tables.Column("user_name", verbose_name=_("Project"))
    host = tables.Column("host", verbose_name=_("Host"), classes=('nowrap-col',))
    name = tables.Column("name", verbose_name=_("Name"))
    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=
                               project_tables.STATUS_DISPLAY_CHOICES)
    state = tables.Column(project_tables.get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"))
    created = tables.Column("created_at",
                            verbose_name=_("Uptime"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status"]
        table_actions = (project_tables.TerminateInstance,)
        row_actions = AdminUpdateRow
        row_actions = (project_tables.TerminateInstance,)
