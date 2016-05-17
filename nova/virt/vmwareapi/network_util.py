# Copyright (c) 2012 VMware, Inc.
# Copyright (c) 2011 Citrix Systems, Inc.
# Copyright 2011 OpenStack Foundation
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
Utility functions for ESX Networking.
"""
from oslo_log import log as logging
from oslo_vmware import exceptions as vexc
from oslo_vmware import vim_util as vutil

from nova import exception
from nova.i18n import _
from nova.virt.vmwareapi import vim_util
from nova.virt.vmwareapi import vm_util

LOG = logging.getLogger(__name__)


def _get_network_obj(session, network_objects, network_name):
    """Gets the network object for the requested network.

    The network object will be used when creating the VM configuration
    spec. The network object contains the relevant network details for
    the specific network type, for example, a distributed port group.

    The method will search for the network_name in the list of
    network_objects.

    :param session: vCenter soap session
    :param network_objects: group of networks
    :param network_name: the requested network
    :return: network object
    """

    network_obj = {}
    # network_objects is actually a RetrieveResult object from vSphere API call
    for obj_content in network_objects:
        # the propset attribute "need not be set" by returning API
        if not hasattr(obj_content, 'propSet'):
            continue
        prop_dict = vm_util.propset_dict(obj_content.propSet)
        network_refs = prop_dict.get('network')
        if network_refs:
            network_refs = network_refs.ManagedObjectReference
            for network in network_refs:
                # Get network properties
                if network._type == 'DistributedVirtualPortgroup':
                    props = session._call_method(vim_util,
                                "get_dynamic_property", network,
                                "DistributedVirtualPortgroup", "config")
                    # NOTE(asomya): This only works on ESXi if the port binding
                    # is set to ephemeral
                    # For a VLAN the network name will be the UUID. For a VXLAN
                    # network this will have a VXLAN prefix and then the
                    # network name.
                    if network_name in props.name:
                        network_obj['type'] = 'DistributedVirtualPortgroup'
                        network_obj['dvpg'] = props.key
                        dvs_props = session._call_method(vim_util,
                                        "get_dynamic_property",
                                        props.distributedVirtualSwitch,
                                        "VmwareDistributedVirtualSwitch",
                                        "uuid")
                        network_obj['dvsw'] = dvs_props
                        return network_obj
                else:
                    props = session._call_method(vim_util,
                                "get_dynamic_property", network,
                                "Network", "summary.name")
                    if props == network_name:
                        network_obj['type'] = 'Network'
                        network_obj['name'] = network_name
                        return network_obj


def get_network_with_the_name(session, network_name="vmnet0", cluster=None):
    """Gets reference to the network whose name is passed as the
    argument.
    """
    vm_networks = session._call_method(vim_util,
                                       'get_object_properties',
                                       None, cluster,
                                       'ClusterComputeResource', ['network'])
    while vm_networks:
        if vm_networks.objects:
            network_obj = _get_network_obj(session, vm_networks.objects,
                                           network_name)
            if network_obj:
                session._call_method(vutil, 'cancel_retrieval',
                                     vm_networks)
                return network_obj
        vm_networks = session._call_method(vutil, 'continue_retrieval',
                                           vm_networks)
    LOG.debug("Network %s not found on cluster!", network_name)


def get_vswitch_for_vlan_interface(session, vlan_interface, cluster=None):
    """Gets the vswitch associated with the physical network adapter
    with the name supplied.
    """
    # Get the list of vSwicthes on the Host System
    host_mor = vm_util.get_host_ref(session, cluster)
    vswitches_ret = session._call_method(vim_util,
                "get_dynamic_property", host_mor,
                "HostSystem", "config.network.vswitch")
    # Meaning there are no vSwitches on the host. Shouldn't be the case,
    # but just doing code check
    if not vswitches_ret:
        return
    vswitches = vswitches_ret.HostVirtualSwitch
    # Get the vSwitch associated with the network adapter
    for elem in vswitches:
        try:
            for nic_elem in elem.pnic:
                if str(nic_elem).split('-')[-1].find(vlan_interface) != -1:
                    return elem.name
        # Catching Attribute error as a vSwitch may not be associated with a
        # physical NIC.
        except AttributeError:
            pass


def check_if_vlan_interface_exists(session, vlan_interface, cluster=None):
    """Checks if the vlan_interface exists on the esx host."""
    host_mor = vm_util.get_host_ref(session, cluster)
    physical_nics_ret = session._call_method(vim_util,
                "get_dynamic_property", host_mor,
                "HostSystem", "config.network.pnic")
    # Meaning there are no physical nics on the host
    if not physical_nics_ret:
        return False
    physical_nics = physical_nics_ret.PhysicalNic
    for pnic in physical_nics:
        if vlan_interface == pnic.device:
            return True
    return False


def get_vlanid_and_vswitch_for_portgroup(session, pg_name, cluster=None):
    """Get the vlan id and vswicth associated with the port group."""
    host_mor = vm_util.get_host_ref(session, cluster)
    port_grps_on_host_ret = session._call_method(vim_util,
                "get_dynamic_property", host_mor,
                "HostSystem", "config.network.portgroup")
    if not port_grps_on_host_ret:
        msg = _("ESX SOAP server returned an empty port group "
                "for the host system in its response")
        LOG.error(msg)
        raise exception.NovaException(msg)
    port_grps_on_host = port_grps_on_host_ret.HostPortGroup
    for p_gp in port_grps_on_host:
        if p_gp.spec.name == pg_name:
            p_grp_vswitch_name = p_gp.vswitch.split("-")[-1]
            return p_gp.spec.vlanId, p_grp_vswitch_name


def create_port_group(session, pg_name, vswitch_name, vlan_id=0, cluster=None):
    """Creates a port group on the host system with the vlan tags
    supplied. VLAN id 0 means no vlan id association.
    """
    client_factory = session.vim.client.factory
    add_prt_grp_spec = vm_util.get_add_vswitch_port_group_spec(
                    client_factory,
                    vswitch_name,
                    pg_name,
                    vlan_id)
    host_mor = vm_util.get_host_ref(session, cluster)
    network_system_mor = session._call_method(vim_util,
        "get_dynamic_property", host_mor,
        "HostSystem", "configManager.networkSystem")
    LOG.debug("Creating Port Group with name %s on "
              "the ESX host", pg_name)
    try:
        session._call_method(session.vim,
                "AddPortGroup", network_system_mor,
                portgrp=add_prt_grp_spec)
    except vexc.AlreadyExistsException:
        # There can be a race condition when two instances try
        # adding port groups at the same time. One succeeds, then
        # the other one will get an exception. Since we are
        # concerned with the port group being created, which is done
        # by the other call, we can ignore the exception.
        LOG.debug("Port Group %s already exists.", pg_name)
    LOG.debug("Created Port Group with name %s on "
              "the ESX host", pg_name)
