# (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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

"""Generic linux scsi subsystem utilities."""

from oslo_concurrency import processutils
from oslo_log import log as logging

from nova.i18n import _LW
from nova.openstack.common import loopingcall
from nova import utils

import os
import re

LOG = logging.getLogger(__name__)

MULTIPATH_WWID_REGEX = re.compile("\((?P<wwid>.+)\)")


def echo_scsi_command(path, content):
    """Used to echo strings to scsi subsystem."""
    args = ["-a", path]
    kwargs = dict(process_input=content, run_as_root=True)
    utils.execute('tee', *args, **kwargs)


def rescan_hosts(hbas):
    for hba in hbas:
        echo_scsi_command("/sys/class/scsi_host/%s/scan"
                          % hba['host_device'], "- - -")


def get_device_list():
    (out, err) = utils.execute('sginfo', '-r', run_as_root=True)
    devices = []
    if out:
        line = out.strip()
        devices = line.split(" ")

    return devices


def get_device_info(device):
    (out, err) = utils.execute('sg_scan', device, run_as_root=True)
    dev_info = {'device': device, 'host': None,
                'channel': None, 'id': None, 'lun': None}
    if out:
        line = out.strip()
        line = line.replace(device + ": ", "")
        info = line.split(" ")

        for item in info:
            if '=' in item:
                pair = item.split('=')
                dev_info[pair[0]] = pair[1]
            elif 'scsi' in item:
                dev_info['host'] = item.replace('scsi', '')

    return dev_info


def _wait_for_remove(device, tries):
    tries = tries + 1
    LOG.debug("Trying (%(tries)s) to remove device %(device)s",
              {'tries': tries, 'device': device["device"]})

    path = "/sys/bus/scsi/drivers/sd/%s:%s:%s:%s/delete"
    echo_scsi_command(path % (device["host"], device["channel"],
                              device["id"], device["lun"]),
                      "1")

    devices = get_device_list()
    if device["device"] not in devices:
        raise loopingcall.LoopingCallDone()


def remove_device(device):
    tries = 0
    timer = loopingcall.FixedIntervalLoopingCall(_wait_for_remove, device,
                                                 tries)
    timer.start(interval=2).wait()
    timer.stop()


def find_multipath_device(device):
    """Try and discover the multipath device for a volume."""
    mdev = None
    devices = []
    out = None
    try:
        (out, err) = utils.execute('multipath', '-l', device,
                               run_as_root=True)
    except processutils.ProcessExecutionError as exc:
        LOG.warning(_LW("Multipath call failed exit (%(code)s)"),
                    {'code': exc.exit_code})
        return None

    if out:
        lines = out.strip()
        lines = lines.split("\n")
        if lines:

            # Use the device name, be it the WWID, mpathN or custom alias of
            # a device to build the device path. This should be the first item
            # on the first line of output from `multipath -l /dev/${path}`.
            mdev_name = lines[0].split(" ")[0]
            mdev = '/dev/mapper/%s' % mdev_name

            # Find the WWID for the LUN if we are using mpathN or aliases.
            wwid_search = MULTIPATH_WWID_REGEX.search(lines[0])
            if wwid_search is not None:
                mdev_id = wwid_search.group('wwid')
            else:
                mdev_id = mdev_name

            # Confirm that the device is present.
            try:
                os.stat(mdev)
            except OSError:
                LOG.warning(_LW("Couldn't find multipath device %s"), mdev)
                return None

            LOG.debug("Found multipath device = %s", mdev)

            device_lines = lines[3:]
            for dev_line in device_lines:
                if dev_line.find("policy") != -1:
                    continue
                if '#' in dev_line:
                    LOG.warning(_LW('Skip faulty line "%(dev_line)s" of'
                                    ' multipath device %(mdev)s'),
                                {'mdev': mdev, 'dev_line': dev_line})
                    continue

                dev_line = dev_line.lstrip(' |-`')
                dev_info = dev_line.split()
                address = dev_info[0].split(":")

                dev = {'device': '/dev/%s' % dev_info[1],
                       'host': address[0], 'channel': address[1],
                       'id': address[2], 'lun': address[3]
                      }

                devices.append(dev)

    if mdev is not None:
        info = {"device": mdev,
                "id": mdev_id,
                "name": mdev_name,
                "devices": devices}
        return info
    return None
