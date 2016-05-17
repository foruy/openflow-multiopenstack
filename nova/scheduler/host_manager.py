# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
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

"""
Manage hosts in the current zone.
"""

import collections
import time
import UserDict

import iso8601
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
from oslo_utils import timeutils

from nova.compute import task_states
from nova.compute import vm_states
from nova import context as context_module
from nova import exception
from nova.i18n import _, _LI, _LW
from nova import objects
from nova.pci import stats as pci_stats
from nova.scheduler import filters
from nova.scheduler import weights
from nova import utils
from nova.virt import hardware

host_manager_opts = [
    cfg.MultiStrOpt('scheduler_available_filters',
            default=['nova.scheduler.filters.all_filters'],
            help='Filter classes available to the scheduler which may '
                    'be specified more than once.  An entry of '
                    '"nova.scheduler.filters.all_filters" '
                    'maps to all filters included with nova.'),
    cfg.ListOpt('scheduler_default_filters',
                default=[
                  'RetryFilter',
                  'AvailabilityZoneFilter',
                  'RamFilter',
                  'ComputeFilter',
                  'ComputeCapabilitiesFilter',
                  'ImagePropertiesFilter',
                  'ServerGroupAntiAffinityFilter',
                  'ServerGroupAffinityFilter',
                  ],
                help='Which filter class names to use for filtering hosts '
                      'when not specified in the request.'),
    cfg.ListOpt('scheduler_weight_classes',
                default=['nova.scheduler.weights.all_weighers'],
                help='Which weight class names to use for weighing hosts'),
    cfg.BoolOpt('scheduler_tracks_instance_changes',
               default=True,
               help='Determines if the Scheduler tracks changes to instances '
                    'to help with its filtering decisions.'),
]

CONF = cfg.CONF
CONF.register_opts(host_manager_opts)

LOG = logging.getLogger(__name__)
HOST_INSTANCE_SEMAPHORE = "host_instance"


class ReadOnlyDict(UserDict.IterableUserDict):
    """A read-only dict."""
    def __init__(self, source=None):
        self.data = {}
        if source:
            self.data.update(source)

    def __setitem__(self, key, item):
        raise TypeError()

    def __delitem__(self, key):
        raise TypeError()

    def clear(self):
        raise TypeError()

    def pop(self, key, *args):
        raise TypeError()

    def popitem(self):
        raise TypeError()

    def update(self):
        raise TypeError()


# Representation of a single metric value from a compute node.
MetricItem = collections.namedtuple(
             'MetricItem', ['value', 'timestamp', 'source'])


class HostState(object):
    """Mutable and immutable information tracked for a host.
    This is an attempt to remove the ad-hoc data structures
    previously used and lock down access.
    """

    def __init__(self, host, node, compute=None):
        self.host = host
        self.nodename = node

        # Mutable available resources.
        # These will change as resources are virtually "consumed".
        self.total_usable_ram_mb = 0
        self.total_usable_disk_gb = 0
        self.disk_mb_used = 0
        self.free_ram_mb = 0
        self.free_disk_mb = 0
        self.vcpus_total = 0
        self.vcpus_used = 0
        self.pci_stats = None
        self.numa_topology = None

        # Additional host information from the compute node stats:
        self.num_instances = 0
        self.num_io_ops = 0

        # Other information
        self.host_ip = None
        self.hypervisor_type = None
        self.hypervisor_version = None
        self.hypervisor_hostname = None
        self.cpu_info = None
        self.supported_instances = None

        # Resource oversubscription values for the compute host:
        self.limits = {}

        # Generic metrics from compute nodes
        self.metrics = {}

        # List of aggregates the host belongs to
        self.aggregates = []

        # Instances on this host
        self.instances = {}

        self.updated = None
        if compute:
            self.update_from_compute_node(compute)

    def update_service(self, service):
        self.service = ReadOnlyDict(service)

    def _update_metrics_from_compute_node(self, compute):
        """Update metrics from a ComputeNode object."""
        # NOTE(llu): The 'or []' is to avoid json decode failure of None
        #            returned from compute.get, because DB schema allows
        #            NULL in the metrics column
        metrics = compute.metrics or []
        if metrics:
            metrics = jsonutils.loads(metrics)
        for metric in metrics:
            # 'name', 'value', 'timestamp' and 'source' are all required
            # to be valid keys, just let KeyError happen if any one of
            # them is missing. But we also require 'name' to be True.
            name = metric['name']
            item = MetricItem(value=metric['value'],
                              timestamp=metric['timestamp'],
                              source=metric['source'])
            if name:
                self.metrics[name] = item
            else:
                LOG.warning(_LW("Metric name unknown of %r"), item)

    def update_from_compute_node(self, compute):
        """Update information about a host from a ComputeNode object."""
        if (self.updated and compute.updated_at
                and self.updated > compute.updated_at):
            return
        all_ram_mb = compute.memory_mb

        # Assume virtual size is all consumed by instances if use qcow2 disk.
        free_gb = compute.free_disk_gb
        least_gb = compute.disk_available_least
        if least_gb is not None:
            if least_gb > free_gb:
                # can occur when an instance in database is not on host
                LOG.warning(_LW("Host %(hostname)s has more disk space than "
                                "database expected "
                                "(%(physical)sgb > %(database)sgb)"),
                            {'physical': least_gb, 'database': free_gb,
                             'hostname': compute.hypervisor_hostname})
            free_gb = min(least_gb, free_gb)
        free_disk_mb = free_gb * 1024

        self.disk_mb_used = compute.local_gb_used * 1024

        # NOTE(jogo) free_ram_mb can be negative
        self.free_ram_mb = compute.free_ram_mb
        self.total_usable_ram_mb = all_ram_mb
        self.total_usable_disk_gb = compute.local_gb
        self.free_disk_mb = free_disk_mb
        self.vcpus_total = compute.vcpus
        self.vcpus_used = compute.vcpus_used
        self.updated = compute.updated_at
        self.numa_topology = compute.numa_topology
        self.pci_stats = pci_stats.PciDeviceStats(
            compute.pci_device_pools)

        # All virt drivers report host_ip
        self.host_ip = compute.host_ip
        self.hypervisor_type = compute.hypervisor_type
        self.hypervisor_version = compute.hypervisor_version
        self.hypervisor_hostname = compute.hypervisor_hostname
        self.cpu_info = compute.cpu_info
        if compute.supported_hv_specs:
            self.supported_instances = [spec.to_list() for spec
                                        in compute.supported_hv_specs]
        else:
            self.supported_instances = []

        # Don't store stats directly in host_state to make sure these don't
        # overwrite any values, or get overwritten themselves. Store in self so
        # filters can schedule with them.
        self.stats = compute.stats or {}

        # Track number of instances on host
        self.num_instances = int(self.stats.get('num_instances', 0))

        self.num_io_ops = int(self.stats.get('io_workload', 0))

        # update metrics
        self._update_metrics_from_compute_node(compute)

    def consume_from_instance(self, instance):
        """Incrementally update host state from an instance."""
        disk_mb = (instance['root_gb'] + instance['ephemeral_gb']) * 1024
        ram_mb = instance['memory_mb']
        vcpus = instance['vcpus']
        self.free_ram_mb -= ram_mb
        self.free_disk_mb -= disk_mb
        self.vcpus_used += vcpus

        now = timeutils.utcnow()
        # NOTE(sbauza): Objects are UTC tz-aware by default
        self.updated = now.replace(tzinfo=iso8601.iso8601.Utc())

        # Track number of instances on host
        self.num_instances += 1

        pci_requests = instance.get('pci_requests')
        # NOTE(danms): Instance here is still a dict, which is converted from
        # an object. The pci_requests are a dict as well. Convert this when
        # we get an object all the way to this path.
        if pci_requests and pci_requests['requests'] and self.pci_stats:
            pci_requests = objects.InstancePCIRequests \
                .from_request_spec_instance_props(pci_requests)
            pci_requests = pci_requests.requests
        else:
            pci_requests = None

        # Calculate the numa usage
        host_numa_topology, _fmt = hardware.host_topology_and_format_from_host(
                                self)
        instance_numa_topology = hardware.instance_topology_from_instance(
            instance)

        instance['numa_topology'] = hardware.numa_fit_instance_to_host(
            host_numa_topology, instance_numa_topology,
            limits=self.limits.get('numa_topology'),
            pci_requests=pci_requests, pci_stats=self.pci_stats)
        if pci_requests:
            instance_cells = None
            if instance['numa_topology']:
                instance_cells = instance['numa_topology'].cells
            self.pci_stats.apply_requests(pci_requests, instance_cells)

        self.numa_topology = hardware.get_host_numa_usage_from_instance(
                self, instance)

        vm_state = instance.get('vm_state', vm_states.BUILDING)
        task_state = instance.get('task_state')
        if vm_state == vm_states.BUILDING or task_state in [
                task_states.RESIZE_MIGRATING, task_states.REBUILDING,
                task_states.RESIZE_PREP, task_states.IMAGE_SNAPSHOT,
                task_states.IMAGE_BACKUP, task_states.UNSHELVING,
                task_states.RESCUING]:
            self.num_io_ops += 1

    def __repr__(self):
        return ("(%s, %s) ram:%s disk:%s io_ops:%s instances:%s" %
                (self.host, self.nodename, self.free_ram_mb, self.free_disk_mb,
                 self.num_io_ops, self.num_instances))


class HostManager(object):
    """Base HostManager class."""

    # Can be overridden in a subclass
    def host_state_cls(self, host, node, **kwargs):
        return HostState(host, node, **kwargs)

    def __init__(self):
        self.host_state_map = {}
        self.filter_handler = filters.HostFilterHandler()
        filter_classes = self.filter_handler.get_matching_classes(
                CONF.scheduler_available_filters)
        self.filter_cls_map = {cls.__name__: cls for cls in filter_classes}
        self.filter_obj_map = {}
        self.default_filters = self._choose_host_filters(self._load_filters())
        self.weight_handler = weights.HostWeightHandler()
        weigher_classes = self.weight_handler.get_matching_classes(
                CONF.scheduler_weight_classes)
        self.weighers = [cls() for cls in weigher_classes]
        # Dict of aggregates keyed by their ID
        self.aggs_by_id = {}
        # Dict of set of aggregate IDs keyed by the name of the host belonging
        # to those aggregates
        self.host_aggregates_map = collections.defaultdict(set)
        self._init_aggregates()
        self.tracks_instance_changes = CONF.scheduler_tracks_instance_changes
        # Dict of instances and status, keyed by host
        self._instance_info = {}
        if self.tracks_instance_changes:
            self._init_instance_info()

    def _load_filters(self):
        return CONF.scheduler_default_filters

    def _init_aggregates(self):
        elevated = context_module.get_admin_context()
        aggs = objects.AggregateList.get_all(elevated)
        for agg in aggs:
            self.aggs_by_id[agg.id] = agg
            for host in agg.hosts:
                self.host_aggregates_map[host].add(agg.id)

    def update_aggregates(self, aggregates):
        """Updates internal HostManager information about aggregates."""
        if isinstance(aggregates, (list, objects.AggregateList)):
            for agg in aggregates:
                self._update_aggregate(agg)
        else:
            self._update_aggregate(aggregates)

    def _update_aggregate(self, aggregate):
        self.aggs_by_id[aggregate.id] = aggregate
        for host in aggregate.hosts:
            self.host_aggregates_map[host].add(aggregate.id)
        # Refreshing the mapping dict to remove all hosts that are no longer
        # part of the aggregate
        for host in self.host_aggregates_map:
            if (aggregate.id in self.host_aggregates_map[host]
                    and host not in aggregate.hosts):
                self.host_aggregates_map[host].remove(aggregate.id)

    def delete_aggregate(self, aggregate):
        """Deletes internal HostManager information about a specific aggregate.
        """
        if aggregate.id in self.aggs_by_id:
            del self.aggs_by_id[aggregate.id]
        for host in aggregate.hosts:
            if aggregate.id in self.host_aggregates_map[host]:
                self.host_aggregates_map[host].remove(aggregate.id)

    def _init_instance_info(self):
        """Creates the initial view of instances for all hosts.

        As this initial population of instance information may take some time,
        we don't wish to block the scheduler's startup while this completes.
        The async method allows us to simply mock out the _init_instance_info()
        method in tests.
        """

        def _async_init_instance_info():
            context = context_module.get_admin_context()
            LOG.debug("START:_async_init_instance_info")
            self._instance_info = {}
            compute_nodes = objects.ComputeNodeList.get_all(context).objects
            LOG.debug("Total number of compute nodes: %s", len(compute_nodes))
            # Break the queries into batches of 10 to reduce the total number
            # of calls to the DB.
            batch_size = 10
            start_node = 0
            end_node = batch_size
            while start_node <= len(compute_nodes):
                curr_nodes = compute_nodes[start_node:end_node]
                start_node += batch_size
                end_node += batch_size
                filters = {"host": [curr_node.host
                                    for curr_node in curr_nodes]}
                result = objects.InstanceList.get_by_filters(context,
                                                             filters)
                instances = result.objects
                LOG.debug("Adding %s instances for hosts %s-%s",
                          len(instances), start_node, end_node)
                for instance in instances:
                    host = instance.host
                    if host not in self._instance_info:
                        self._instance_info[host] = {"instances": {},
                                                     "updated": False}
                    inst_dict = self._instance_info[host]
                    inst_dict["instances"][instance.uuid] = instance
                # Call sleep() to cooperatively yield
                time.sleep(0)
            LOG.debug("END:_async_init_instance_info")

        # Run this async so that we don't block the scheduler start-up
        utils.spawn_n(_async_init_instance_info)

    def _choose_host_filters(self, filter_cls_names):
        """Since the caller may specify which filters to use we need
        to have an authoritative list of what is permissible. This
        function checks the filter names against a predefined set
        of acceptable filters.
        """
        if not isinstance(filter_cls_names, (list, tuple)):
            filter_cls_names = [filter_cls_names]

        good_filters = []
        bad_filters = []
        for filter_name in filter_cls_names:
            if filter_name not in self.filter_obj_map:
                if filter_name not in self.filter_cls_map:
                    bad_filters.append(filter_name)
                    continue
                filter_cls = self.filter_cls_map[filter_name]
                self.filter_obj_map[filter_name] = filter_cls()
            good_filters.append(self.filter_obj_map[filter_name])
        if bad_filters:
            msg = ", ".join(bad_filters)
            raise exception.SchedulerHostFilterNotFound(filter_name=msg)
        return good_filters

    def get_filtered_hosts(self, hosts, filter_properties,
            filter_class_names=None, index=0):
        """Filter hosts and return only ones passing all filters."""

        def _strip_ignore_hosts(host_map, hosts_to_ignore):
            ignored_hosts = []
            for host in hosts_to_ignore:
                for (hostname, nodename) in host_map.keys():
                    if host == hostname:
                        del host_map[(hostname, nodename)]
                        ignored_hosts.append(host)
            ignored_hosts_str = ', '.join(ignored_hosts)
            msg = _('Host filter ignoring hosts: %s')
            LOG.info(msg % ignored_hosts_str)

        def _match_forced_hosts(host_map, hosts_to_force):
            forced_hosts = []
            for (hostname, nodename) in host_map.keys():
                if hostname not in hosts_to_force:
                    del host_map[(hostname, nodename)]
                else:
                    forced_hosts.append(hostname)
            if host_map:
                forced_hosts_str = ', '.join(forced_hosts)
                msg = _('Host filter forcing available hosts to %s')
            else:
                forced_hosts_str = ', '.join(hosts_to_force)
                msg = _("No hosts matched due to not matching "
                        "'force_hosts' value of '%s'")
            LOG.info(msg % forced_hosts_str)

        def _match_forced_nodes(host_map, nodes_to_force):
            forced_nodes = []
            for (hostname, nodename) in host_map.keys():
                if nodename not in nodes_to_force:
                    del host_map[(hostname, nodename)]
                else:
                    forced_nodes.append(nodename)
            if host_map:
                forced_nodes_str = ', '.join(forced_nodes)
                msg = _('Host filter forcing available nodes to %s')
            else:
                forced_nodes_str = ', '.join(nodes_to_force)
                msg = _("No nodes matched due to not matching "
                        "'force_nodes' value of '%s'")
            LOG.info(msg % forced_nodes_str)

        if filter_class_names is None:
            filters = self.default_filters
        else:
            filters = self._choose_host_filters(filter_class_names)
        ignore_hosts = filter_properties.get('ignore_hosts', [])
        force_hosts = filter_properties.get('force_hosts', [])
        force_nodes = filter_properties.get('force_nodes', [])

        if ignore_hosts or force_hosts or force_nodes:
            # NOTE(deva): we can't assume "host" is unique because
            #             one host may have many nodes.
            name_to_cls_map = {(x.host, x.nodename): x for x in hosts}
            if ignore_hosts:
                _strip_ignore_hosts(name_to_cls_map, ignore_hosts)
                if not name_to_cls_map:
                    return []
            # NOTE(deva): allow force_hosts and force_nodes independently
            if force_hosts:
                _match_forced_hosts(name_to_cls_map, force_hosts)
            if force_nodes:
                _match_forced_nodes(name_to_cls_map, force_nodes)
            if force_hosts or force_nodes:
                # NOTE(deva): Skip filters when forcing host or node
                if name_to_cls_map:
                    return name_to_cls_map.values()
            hosts = name_to_cls_map.itervalues()

        return self.filter_handler.get_filtered_objects(filters,
                hosts, filter_properties, index)

    def get_weighed_hosts(self, hosts, weight_properties):
        """Weigh the hosts."""
        return self.weight_handler.get_weighed_objects(self.weighers,
                hosts, weight_properties)

    def get_all_host_states(self, context):
        """Returns a list of HostStates that represents all the hosts
        the HostManager knows about. Also, each of the consumable resources
        in HostState are pre-populated and adjusted based on data in the db.
        """

        service_refs = {service.host: service
                        for service in objects.ServiceList.get_by_binary(
                            context, 'nova-compute')}
        # Get resource usage across the available compute nodes:
        compute_nodes = objects.ComputeNodeList.get_all(context)
        seen_nodes = set()
        for compute in compute_nodes:
            service = service_refs.get(compute.host)

            if not service:
                LOG.warning(_LW(
                    "No compute service record found for host %(host)s"),
                    {'host': compute.host})
                continue
            host = compute.host
            node = compute.hypervisor_hostname
            state_key = (host, node)
            host_state = self.host_state_map.get(state_key)
            if host_state:
                host_state.update_from_compute_node(compute)
            else:
                host_state = self.host_state_cls(host, node, compute=compute)
                self.host_state_map[state_key] = host_state
            # We force to update the aggregates info each time a new request
            # comes in, because some changes on the aggregates could have been
            # happening after setting this field for the first time
            host_state.aggregates = [self.aggs_by_id[agg_id] for agg_id in
                                     self.host_aggregates_map[
                                         host_state.host]]
            host_state.update_service(dict(service.iteritems()))
            self._add_instance_info(context, compute, host_state)
            seen_nodes.add(state_key)

        # remove compute nodes from host_state_map if they are not active
        dead_nodes = set(self.host_state_map.keys()) - seen_nodes
        for state_key in dead_nodes:
            host, node = state_key
            LOG.info(_LI("Removing dead compute node %(host)s:%(node)s "
                         "from scheduler"), {'host': host, 'node': node})
            del self.host_state_map[state_key]

        return self.host_state_map.itervalues()

    def _add_instance_info(self, context, compute, host_state):
        """Adds the host instance info to the host_state object.

        Some older compute nodes may not be sending instance change updates to
        the Scheduler; other sites may disable this feature for performance
        reasons. In either of these cases, there will either be no information
        for the host, or the 'updated' value for that host dict will be False.
        In those cases, we need to grab the current InstanceList instead of
        relying on the version in _instance_info.
        """
        host_name = compute.host
        host_info = self._instance_info.get(host_name)
        if host_info and host_info.get("updated"):
            inst_dict = host_info["instances"]
        else:
            # Host is running old version, or updates aren't flowing.
            inst_list = objects.InstanceList.get_by_host(context, host_name)
            inst_dict = {instance.uuid: instance
                         for instance in inst_list.objects}
        host_state.instances = inst_dict

    def _recreate_instance_info(self, context, host_name):
        """Get the InstanceList for the specified host, and store it in the
        _instance_info dict.
        """
        instances = objects.InstanceList.get_by_host(context, host_name)
        inst_dict = {instance.uuid: instance for instance in instances}
        host_info = self._instance_info[host_name] = {}
        host_info["instances"] = inst_dict
        host_info["updated"] = False

    @utils.synchronized(HOST_INSTANCE_SEMAPHORE)
    def update_instance_info(self, context, host_name, instance_info):
        """Receives an InstanceList object from a compute node.

        This method receives information from a compute node when it starts up,
        or when its instances have changed, and updates its view of hosts and
        instances with it.
        """
        host_info = self._instance_info.get(host_name)
        if host_info:
            inst_dict = host_info.get("instances")
            for instance in instance_info.objects:
                # Overwrite the entry (if any) with the new info.
                inst_dict[instance.uuid] = instance
            host_info["updated"] = True
        else:
            instances = instance_info.objects
            if len(instances) > 1:
                # This is a host sending its full instance list, so use it.
                host_info = self._instance_info[host_name] = {}
                host_info["instances"] = {instance.uuid: instance
                                          for instance in instances}
                host_info["updated"] = True
            else:
                self._recreate_instance_info(context, host_name)
                LOG.info(_LI("Received an update from an unknown host '%s'. "
                             "Re-created its InstanceList."), host_name)

    @utils.synchronized(HOST_INSTANCE_SEMAPHORE)
    def delete_instance_info(self, context, host_name, instance_uuid):
        """Receives the UUID from a compute node when one of its instances is
        terminated.

        The instance in the local view of the host's instances is removed.
        """
        host_info = self._instance_info.get(host_name)
        if host_info:
            inst_dict = host_info["instances"]
            # Remove the existing Instance object, if any
            inst_dict.pop(instance_uuid, None)
            host_info["updated"] = True
        else:
            self._recreate_instance_info(context, host_name)
            LOG.info(_LI("Received a delete update from an unknown host '%s'. "
                         "Re-created its InstanceList."), host_name)

    @utils.synchronized(HOST_INSTANCE_SEMAPHORE)
    def sync_instance_info(self, context, host_name, instance_uuids):
        """Receives the uuids of the instances on a host.

        This method is periodically called by the compute nodes, which send a
        list of all the UUID values for the instances on that node. This is
        used by the scheduler's HostManager to detect when its view of the
        compute node's instances is out of sync.
        """
        host_info = self._instance_info.get(host_name)
        if host_info:
            local_set = set(host_info["instances"].keys())
            compute_set = set(instance_uuids)
            if not local_set == compute_set:
                self._recreate_instance_info(context, host_name)
                LOG.info(_LI("The instance sync for host '%s' did not match. "
                             "Re-created its InstanceList."), host_name)
                return
            host_info["updated"] = True
            LOG.info(_LI("Successfully synced instances from host '%s'."),
                     host_name)
        else:
            self._recreate_instance_info(context, host_name)
            LOG.info(_LI("Received a sync request from an unknown host '%s'. "
                         "Re-created its InstanceList."), host_name)
