import json
import logging

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import forms
from horizon.utils import functions
from horizon import workflows
from horizon import exceptions

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils

LOG = logging.getLogger(__name__)

class SetInstanceDetailsAction(workflows.Action):
    #availability_zone = forms.ChoiceField(label=_("Availability Zone"),
    #                                      required=False)

    name = forms.CharField(label=_("Instance Name"),
                           max_length=255)

    #flavor = forms.ChoiceField(label=_("Flavor"),
    #                           help_text=_("Size of image to launch."))

    count = forms.IntegerField(label=_("Instance Count"),
                               min_value=1,
                               initial=1,
                               #widget=forms.TextInput(attrs={'readonly': 'readonly'}),
                               help_text=_("Number of instances to launch."))

    #address = forms.IPField(label=_("Network Address"),
    #                              required=False,
    #                              help_text=_("Specify the IP Address of instance. "
    #                                          "If you use the default, leave blank."),
    #                              version=forms.IPv4,
    #                              mask=False)
    cidr = forms.ChoiceField(label=_("Select subnet"))

    #gateway = forms.ChoiceField(label=("Select Default Access Point for SSH"))

    image_id = forms.ChoiceField(
        label=_("Image Name"),
        #required=False,
        widget=forms.SelectWidget(
            data_attrs=('volume_size',),
            transform=lambda x: ("%s (%s)" % (x.name,
                                              filesizeformat(x.bytes)))))
    class Meta:
        name = _("Details")
        #help_text_template = ("project/instances/"
        #                      "_launch_details_help.html")

    def __init__(self, request, context, *args, **kwargs):
        self._init_images_cache()
        super(SetInstanceDetailsAction, self).__init__(
            request, context, *args, **kwargs)

        try:
            netypes = api.proxy.network_type_list(request)
        except:
            netypes = []
            exceptions.handle(request, _('Unable to retrieve network type.'),
                              ignore=True)

        self.fields['cidr'].choices = ((nt.id, nt.cidr) for nt in netypes)

    def clean(self):
        cleaned_data = super(SetInstanceDetailsAction, self).clean()
        if not cleaned_data.get('image_id'):
            msg = _("You must select a image.")
            raise forms.ValidationError(msg)

        count = cleaned_data.get('count', 1)
        #limit = api.proxy.project_absolute_limits(
        #    self.request, self.initial['zone_id'])
        #if limit.maxTotalInstances - limit.totalInstancesUsed - count < 0:
        #    msg = _("Quota exceeded.")
        #    raise forms.ValidationError(msg)

        limits = api.proxy.user_absolute_limits(self.request)

        if limits.maxTotalInstances - limits.totalInstancesUsed - count < 0:
            msg = _("Quota exceeded.")
            raise forms.ValidationError(msg)

        address = cleaned_data.get('address', None)
        if address is not None:
            try:
                api.proxy.server_network(self.request, address)
            except:
                msg = _("This address was in used.")
                raise forms.ValidationError(msg)
        
        return cleaned_data

    #def populate_flavor_choices(self, request, context):
    #    flavors = instance_utils.flavor_list(request, context['zone_id'])
    #    if flavors:
    #        return instance_utils.sort_flavor_list(request, flavors)
    #    return []

    #def populate_availability_zone_choices(self, request, context):
    #    try:
    #        zones = api.nova.availability_zone_list(self._request)
    #    except Exception:
    #        zones = []
    #        exceptions.handle(request,
    #                          _('Unable to retrieve availability zones.'))

    #    zone_list = [(zone.zoneName, zone.zoneName)
    #                  for zone in zones if zone.zoneState['available']]
    #    zone_list.sort()
    #    if not zone_list:
    #        zone_list.insert(0, ("", _("No availability zones found")))
    #    elif len(zone_list) > 1:
    #        zone_list.insert(0, ("", _("Any Availability Zone")))
    #    return zone_list

    #def get_help_text(self):
    #    extra = {}
    #    try:
    #        flavors = json.dumps([f._info for f in
    #                              instance_utils.flavor_list(self.request,
    #                              self.initial['zone_id'])])
    #        extra['flavors'] = flavors

    #    except Exception:
    #        exceptions.handle(self.request,
    #                          _("Unable to retrieve quota information."))
    #    return super(SetInstanceDetailsAction, self).get_help_text(extra)

    def _init_images_cache(self):
        if not hasattr(self, '_images_cache'):
            self._images_cache = {}

    def populate_image_id_choices(self, request, context):
        choices = []
        image_dict = {}
        #images = image_utils.get_available_images(request,
        #                                    context.get('zone_id'),
        #                                    images_cache=self._images_cache)
        try:
            zones = api.proxy.availability_zone_list(request)
        except:
            zones = []
            exceptions.handle(request, _('Unable to retrieve zones.'), ignore=True)

        for zone in zones:
            images = image_utils.get_available_images(
                    request, zone.id, images_cache=self._images_cache)
            for image in images:
                image_dict[image.name] = image

        for image in image_dict.values():
            image.bytes = image.size
            image.volume_size = max(
                image.min_disk, functions.bytes_to_gigabytes(image.bytes))
            choices.append((image.imageid, image))
        if choices:
            choices.sort(key=lambda c: c[1].name)
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        return choices


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    #depends_on = ("zone_id",)
    #contributes = ("name", "count", "address", "flavor", "image_id")
    contributes = ("name", "count", "cidr", "flavor", "image_id")

class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SetInstanceDetails,)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        count = self.context.get('count', 1)
        if int(count) > 1:
            return message % {"count": _("%s instances") % count,
                              "name": name}
        else:
            return message % {"count": _("instance"), "name": name}

    @sensitive_variables('context')
    def handle(self, request, context):
        custom_script = context.get('customization_script', '')

        image_id = context['image_id']

        if not context.get('zone_id', None):
            context['zone_id'] = None

        if not context.get('count', None):
            context['count'] = 1

        if not context.get('address', None):
            context['address'] = None

        if not context.get('flavor', None):
            context['flavor'] = 1

        if not context.get('cidr', None):
            context['cidr'] = 1

        request.session['netype'] = int(context['cidr'])

        netids = context.get('network_id', None)
        if netids:
            nics = [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            nics = None

        avail_zone = context.get('availability_zone', None)

        if not context.get('keypair_id', None):
            context['keypair_id'] = None

        if not context.get('security_group_ids', None):
            context['security_group_ids'] = None

        if not context.get('admin_pass', None):
            context['admin_pass'] = None

        if not context.get('disk_config', None):
            context['disk_config'] = None

        api.proxy.server_create(request,
                                context['name'],
                                image_id,
                                context['flavor'],
                                zone_id=context['zone_id'],
                                key_name=context['keypair_id'],
                                user_data=normalize_newlines(custom_script),
                                security_groups=None,
                                block_device_mapping=None,
                                block_device_mapping_v2=None,
                                nics=nics,
                                availability_zone=avail_zone,
                                instance_count=int(context['count']),
                                admin_pass=context['admin_pass'],
                                disk_config=context['disk_config'],
                                accessIPv4=context['address'],
                                net_type=int(context['cidr']))
        return True
