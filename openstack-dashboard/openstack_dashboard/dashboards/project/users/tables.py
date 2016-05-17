import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters

LOG = logging.getLogger(__name__)

class ConsumptionLink(tables.LinkAction):
    name = "sumption_detail"
    verbose_name = _("Comsumption Detail")
    url = "horizon:project:users:detail"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum):
        args = (datum.source_name, datum.source_id)
        return reverse(self.url, args=args)

class ConsumptionTable(tables.DataTable):
    source_name = tables.Column("source_name", verbose_name=_("Source Type"))
    #source_id = tables.Column("source_id", verbose_name=_("Source Id"))
    name = tables.Column("name", verbose_name=_("Source Name"))
    created_at = tables.Column("created_at",
                               verbose_name=_("Start Time"),)
                               #filters=(filters.parse_isotime,
                               #         filters.timesince_sortable),
                               #attrs={'data-type': 'timesince'})
    deleted_at = tables.Column("deleted_at",
                               verbose_name=_("End Time"),)
                               #filters=(filters.parse_isotime,
                               #         filters.timesince_sortable),
                               #attrs={'data-type': 'timesince'})
    total_time = tables.Column("usage", verbose_name=_("Total Time(s)"))

    class Meta:
        name = "consumptions"
        verbose_name = _("Consumptions")
        row_actions = (ConsumptionLink,)

class LoginTable(tables.DataTable):
    user_addr = tables.Column("user_addr", verbose_name=_("Client Address"))
    user_type = tables.Column("user_type", verbose_name=_("Client Browser"))
    updated_at = tables.Column("updated_at",
                               verbose_name=_("Uptime"),)
                               #filters=(filters.parse_isotime,
                               #         filters.timesince_sortable),
                               #attrs={'data-type': 'timesince'})

    class Meta:
        name = "logins"
        verbose_name = _("Logins")

class SumptionDetailTable(tables.DataTable):
    action = tables.Column("action", verbose_name=_("Action"))
    created_at = tables.Column("created_at",
                               verbose_name=_("Uptime"),)
                               #filters=(filters.parse_isotime,
                               #         filters.timesince_sortable),
                               #attrs={'data-type': 'timesince'})

    class Meta:
        name = "details"
        verbose_name = _("Details")
