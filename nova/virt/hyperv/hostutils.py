# Copyright 2013 Cloudbase Solutions Srl
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

import ctypes
import socket
import sys

if sys.platform == 'win32':
    import wmi

from nova.i18n import _
from nova.virt.hyperv import constants


class HostUtils(object):

    _HOST_FORCED_REBOOT = 6
    _HOST_FORCED_SHUTDOWN = 12
    _DEFAULT_VM_GENERATION = constants.IMAGE_PROP_VM_GEN_1

    def __init__(self):
        if sys.platform == 'win32':
            self._conn_cimv2 = wmi.WMI(privileges=["Shutdown"])

    def get_cpus_info(self):
        cpus = self._conn_cimv2.query("SELECT * FROM Win32_Processor "
                                      "WHERE ProcessorType = 3")
        cpus_list = []
        for cpu in cpus:
            cpu_info = {'Architecture': cpu.Architecture,
                        'Name': cpu.Name,
                        'Manufacturer': cpu.Manufacturer,
                        'NumberOfCores': cpu.NumberOfCores,
                        'NumberOfLogicalProcessors':
                        cpu.NumberOfLogicalProcessors}
            cpus_list.append(cpu_info)
        return cpus_list

    def is_cpu_feature_present(self, feature_key):
        return ctypes.windll.kernel32.IsProcessorFeaturePresent(feature_key)

    def get_memory_info(self):
        """Returns a tuple with total visible memory and free physical memory
        expressed in kB.
        """
        mem_info = self._conn_cimv2.query("SELECT TotalVisibleMemorySize, "
                                          "FreePhysicalMemory "
                                          "FROM win32_operatingsystem")[0]
        return (long(mem_info.TotalVisibleMemorySize),
                long(mem_info.FreePhysicalMemory))

    def get_volume_info(self, drive):
        """Returns a tuple with total size and free space
        expressed in bytes.
        """
        logical_disk = self._conn_cimv2.query("SELECT Size, FreeSpace "
                                              "FROM win32_logicaldisk "
                                              "WHERE DeviceID='%s'"
                                              % drive)[0]
        return (long(logical_disk.Size), long(logical_disk.FreeSpace))

    def check_min_windows_version(self, major, minor, build=0):
        version_str = self.get_windows_version()
        return map(int, version_str.split('.')) >= [major, minor, build]

    def get_windows_version(self):
        return self._conn_cimv2.Win32_OperatingSystem()[0].Version

    def get_local_ips(self):
        addr_info = socket.getaddrinfo(socket.gethostname(), None, 0, 0, 0)
        # Returns IPv4 and IPv6 addresses, ordered by protocol family
        addr_info.sort()
        return [a[4][0] for a in addr_info]

    def get_host_tick_count64(self):
        return ctypes.windll.kernel32.GetTickCount64()

    def host_power_action(self, action):
        win32_os = self._conn_cimv2.Win32_OperatingSystem()[0]

        if action == constants.HOST_POWER_ACTION_SHUTDOWN:
            win32_os.Win32Shutdown(self._HOST_FORCED_SHUTDOWN)
        elif action == constants.HOST_POWER_ACTION_REBOOT:
            win32_os.Win32Shutdown(self._HOST_FORCED_REBOOT)
        else:
            raise NotImplementedError(
                _("Host %(action)s is not supported by the Hyper-V driver") %
                {"action": action})

    def get_supported_vm_types(self):
        """Get the supported Hyper-V VM generations.
        Hyper-V Generation 2 VMs are supported in Windows 8.1,
        Windows Server / Hyper-V Server 2012 R2 or newer.

        :returns: array of supported VM generations (ex. ['hyperv-gen1'])
        """
        if self.check_min_windows_version(6, 3):
            return [constants.IMAGE_PROP_VM_GEN_1,
                    constants.IMAGE_PROP_VM_GEN_2]
        else:
            return [constants.IMAGE_PROP_VM_GEN_1]

    def get_default_vm_generation(self):
        return self._DEFAULT_VM_GENERATION
