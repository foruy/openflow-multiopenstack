# Copyright (c) 2014 VMware, Inc.
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
Shared constants across the VMware driver
"""

from nova.network import model as network_model

DISK_FORMAT_ISO = 'iso'
DISK_FORMAT_VMDK = 'vmdk'
DISK_FORMATS_ALL = [DISK_FORMAT_ISO, DISK_FORMAT_VMDK]

DISK_TYPE_THIN = 'thin'
CONTAINER_FORMAT_BARE = 'bare'
CONTAINER_FORMAT_OVA = 'ova'
CONTAINER_FORMATS_ALL = [CONTAINER_FORMAT_BARE, DISK_FORMAT_VMDK]

DISK_TYPE_SPARSE = 'sparse'
DISK_TYPE_PREALLOCATED = 'preallocated'
DISK_TYPE_STREAM_OPTIMIZED = 'streamOptimized'
DISK_TYPE_EAGER_ZEROED_THICK = 'eagerZeroedThick'

DATASTORE_TYPE_VMFS = 'VMFS'
DATASTORE_TYPE_NFS = 'NFS'
DATASTORE_TYPE_VSAN = 'vsan'

DEFAULT_VIF_MODEL = network_model.VIF_MODEL_E1000
DEFAULT_OS_TYPE = "otherGuest"
DEFAULT_ADAPTER_TYPE = "lsiLogic"
DEFAULT_DISK_TYPE = DISK_TYPE_PREALLOCATED
DEFAULT_DISK_FORMAT = DISK_FORMAT_VMDK
DEFAULT_CONTAINER_FORMAT = CONTAINER_FORMAT_BARE

IMAGE_VM_PREFIX = "OSTACK_IMG"
SNAPSHOT_VM_PREFIX = "OSTACK_SNAP"

ADAPTER_TYPE_BUSLOGIC = "busLogic"
ADAPTER_TYPE_IDE = "ide"
ADAPTER_TYPE_LSILOGICSAS = "lsiLogicsas"
ADAPTER_TYPE_PARAVIRTUAL = "paraVirtual"

SUPPORTED_FLAT_VARIANTS = ["thin", "preallocated", "thick", "eagerZeroedThick"]

EXTENSION_KEY = 'org.openstack.compute'
EXTENSION_TYPE_INSTANCE = 'instance'

# The max number of devices that can be connnected to one adapter
# One adapter has 16 slots but one reserved for controller
SCSI_MAX_CONNECT_NUMBER = 15

# This list was extracted from the installation iso image for ESX 5.5 Update 1.
# It is contained in s.v00, which is gzipped. The list was obtained by
# searching for the string 'otherGuest' in the uncompressed contents of that
# file, copying out the full list less the 'family' ids at the end, and sorting
# it. The contents of this list should be updated whenever there is a new
# release of ESX.
VALID_OS_TYPES = set([
    'asianux3_64Guest',
    'asianux3Guest',
    'asianux4_64Guest',
    'asianux4Guest',
    'centos64Guest',
    'centosGuest',
    'darwin10_64Guest',
    'darwin10Guest',
    'darwin11_64Guest',
    'darwin11Guest',
    'darwin12_64Guest',
    'darwin13_64Guest',
    'darwin64Guest',
    'darwinGuest',
    'debian4_64Guest',
    'debian4Guest',
    'debian5_64Guest',
    'debian5Guest',
    'debian6_64Guest',
    'debian6Guest',
    'debian7_64Guest',
    'debian7Guest',
    'dosGuest',
    'eComStation2Guest',
    'eComStationGuest',
    'fedora64Guest',
    'fedoraGuest',
    'freebsd64Guest',
    'freebsdGuest',
    'genericLinuxGuest',
    'mandrakeGuest',
    'mandriva64Guest',
    'mandrivaGuest',
    'netware4Guest',
    'netware5Guest',
    'netware6Guest',
    'nld9Guest',
    'oesGuest',
    'openServer5Guest',
    'openServer6Guest',
    'opensuse64Guest',
    'opensuseGuest',
    'oracleLinux64Guest',
    'oracleLinuxGuest',
    'os2Guest',
    'other24xLinux64Guest',
    'other24xLinuxGuest',
    'other26xLinux64Guest',
    'other26xLinuxGuest',
    'other3xLinux64Guest',
    'other3xLinuxGuest',
    'otherGuest',
    'otherGuest64',
    'otherLinux64Guest',
    'otherLinuxGuest',
    'redhatGuest',
    'rhel2Guest',
    'rhel3_64Guest',
    'rhel3Guest',
    'rhel4_64Guest',
    'rhel4Guest',
    'rhel5_64Guest',
    'rhel5Guest',
    'rhel6_64Guest',
    'rhel6Guest',
    'rhel7_64Guest',
    'rhel7Guest',
    'sjdsGuest',
    'sles10_64Guest',
    'sles10Guest',
    'sles11_64Guest',
    'sles11Guest',
    'sles12_64Guest',
    'sles12Guest',
    'sles64Guest',
    'slesGuest',
    'solaris10_64Guest',
    'solaris10Guest',
    'solaris11_64Guest',
    'solaris6Guest',
    'solaris7Guest',
    'solaris8Guest',
    'solaris9Guest',
    'turboLinux64Guest',
    'turboLinuxGuest',
    'ubuntu64Guest',
    'ubuntuGuest',
    'unixWare7Guest',
    'vmkernel5Guest',
    'vmkernelGuest',
    'win2000AdvServGuest',
    'win2000ProGuest',
    'win2000ServGuest',
    'win31Guest',
    'win95Guest',
    'win98Guest',
    'windows7_64Guest',
    'windows7Guest',
    'windows7Server64Guest',
    'windows8_64Guest',
    'windows8Guest',
    'windows8Server64Guest',
    'windowsHyperVGuest',
    'winLonghorn64Guest',
    'winLonghornGuest',
    'winMeGuest',
    'winNetBusinessGuest',
    'winNetDatacenter64Guest',
    'winNetDatacenterGuest',
    'winNetEnterprise64Guest',
    'winNetEnterpriseGuest',
    'winNetStandard64Guest',
    'winNetStandardGuest',
    'winNetWebGuest',
    'winNTGuest',
    'winVista64Guest',
    'winVistaGuest',
    'winXPHomeGuest',
    'winXPPro64Guest',
    'winXPProGuest',
])
