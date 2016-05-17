# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright (c) 2010 Citrix Systems, Inc.
# Copyright (c) 2011 Piston Cloud Computing, Inc
# Copyright (c) 2012 University Of Minho
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

"""
Manages information about the host OS and hypervisor.

This class encapsulates a connection to the libvirt
daemon and provides certain higher level APIs around
the raw libvirt API. These APIs are then used by all
the other libvirt related classes
"""

import operator
import os
import socket
import threading

import eventlet
from eventlet import greenio
from eventlet import greenthread
from eventlet import patcher
from eventlet import tpool
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

from nova import context as nova_context
from nova import exception
from nova.i18n import _
from nova.i18n import _LE
from nova.i18n import _LI
from nova.i18n import _LW
from nova import rpc
from nova import utils
from nova.virt import event as virtevent
from nova.virt.libvirt import compat
from nova.virt.libvirt import config as vconfig

libvirt = None

LOG = logging.getLogger(__name__)

native_socket = patcher.original('socket')
native_threading = patcher.original("threading")
native_Queue = patcher.original("Queue")

CONF = cfg.CONF
CONF.import_opt('host', 'nova.netconf')
CONF.import_opt('my_ip', 'nova.netconf')


class DomainJobInfo(object):
    """Information about libvirt background jobs

    This class encapsulates information about libvirt
    background jobs. It provides a mapping from either
    the old virDomainGetJobInfo API which returned a
    fixed list of fields, or the modern virDomainGetJobStats
    which returns an extendable dict of fields.
    """

    _have_job_stats = True

    def __init__(self, **kwargs):

        self.type = kwargs.get("type", libvirt.VIR_DOMAIN_JOB_NONE)
        self.time_elapsed = kwargs.get("time_elapsed", 0)
        self.time_remaining = kwargs.get("time_remaining", 0)
        self.downtime = kwargs.get("downtime", 0)
        self.setup_time = kwargs.get("setup_time", 0)
        self.data_total = kwargs.get("data_total", 0)
        self.data_processed = kwargs.get("data_processed", 0)
        self.data_remaining = kwargs.get("data_remaining", 0)
        self.memory_total = kwargs.get("memory_total", 0)
        self.memory_processed = kwargs.get("memory_processed", 0)
        self.memory_remaining = kwargs.get("memory_remaining", 0)
        self.memory_constant = kwargs.get("memory_constant", 0)
        self.memory_normal = kwargs.get("memory_normal", 0)
        self.memory_normal_bytes = kwargs.get("memory_normal_bytes", 0)
        self.memory_bps = kwargs.get("memory_bps", 0)
        self.disk_total = kwargs.get("disk_total", 0)
        self.disk_processed = kwargs.get("disk_processed", 0)
        self.disk_remaining = kwargs.get("disk_remaining", 0)
        self.disk_bps = kwargs.get("disk_bps", 0)
        self.comp_cache = kwargs.get("compression_cache", 0)
        self.comp_bytes = kwargs.get("compression_bytes", 0)
        self.comp_pages = kwargs.get("compression_pages", 0)
        self.comp_cache_misses = kwargs.get("compression_cache_misses", 0)
        self.comp_overflow = kwargs.get("compression_overflow", 0)

    @classmethod
    def _get_job_stats_compat(cls, dom):
        # Make the old virDomainGetJobInfo method look similar to the
        # modern virDomainGetJobStats method
        try:
            info = dom.jobInfo()
        except libvirt.libvirtError as ex:
            # When migration of a transient guest completes, the guest
            # goes away so we'll see NO_DOMAIN error code
            #
            # When migration of a persistent guest completes, the guest
            # merely shuts off, but libvirt unhelpfully raises an
            # OPERATION_INVALID error code
            #
            # Lets pretend both of these mean success
            if ex.get_error_code() in (libvirt.VIR_ERR_NO_DOMAIN,
                                       libvirt.VIR_ERR_OPERATION_INVALID):
                LOG.debug("Domain has shutdown/gone away: %s", ex)
                return cls(type=libvirt.VIR_DOMAIN_JOB_COMPLETED)
            else:
                LOG.debug("Failed to get job info: %s", ex)
                raise

        return cls(
            type=info[0],
            time_elapsed=info[1],
            time_remaining=info[2],
            data_total=info[3],
            data_processed=info[4],
            data_remaining=info[5],
            memory_total=info[6],
            memory_processed=info[7],
            memory_remaining=info[8],
            disk_total=info[9],
            disk_processed=info[10],
            disk_remaining=info[11])

    @classmethod
    def for_domain(cls, dom):
        '''Get job info for the domain

        Query the libvirt job info for the domain (ie progress
        of migration, or snapshot operation)

        Returns: a DomainJobInfo instance
        '''

        if cls._have_job_stats:
            try:
                stats = dom.jobStats()
                return cls(**stats)
            except libvirt.libvirtError as ex:
                if ex.get_error_code() == libvirt.VIR_ERR_NO_SUPPORT:
                    # Remote libvirt doesn't support new API
                    LOG.debug("Missing remote virDomainGetJobStats: %s", ex)
                    cls._have_job_stats = False
                    return cls._get_job_stats_compat(dom)
                elif ex.get_error_code() in (
                        libvirt.VIR_ERR_NO_DOMAIN,
                        libvirt.VIR_ERR_OPERATION_INVALID):
                    # Transient guest finished migration, so it has gone
                    # away completely
                    LOG.debug("Domain has shutdown/gone away: %s", ex)
                    return cls(type=libvirt.VIR_DOMAIN_JOB_COMPLETED)
                else:
                    LOG.debug("Failed to get job stats: %s", ex)
                    raise
            except AttributeError as ex:
                # Local python binding doesn't support new API
                LOG.debug("Missing local virDomainGetJobStats: %s", ex)
                cls._have_job_stats = False
                return cls._get_job_stats_compat(dom)
        else:
            return cls._get_job_stats_compat(dom)


class Host(object):

    def __init__(self, uri, read_only=False,
                 conn_event_handler=None,
                 lifecycle_event_handler=None):

        global libvirt
        if libvirt is None:
            libvirt = __import__('libvirt')

        self._uri = uri
        self._read_only = read_only
        self._conn_event_handler = conn_event_handler
        self._lifecycle_event_handler = lifecycle_event_handler
        self._skip_list_all_domains = False
        self._caps = None
        self._hostname = None

        self._wrapped_conn = None
        self._wrapped_conn_lock = threading.Lock()
        self._event_queue = None

        self._events_delayed = {}
        # Note(toabctl): During a reboot of a Xen domain, STOPPED and
        #                STARTED events are sent. To prevent shutting
        #                down the domain during a reboot, delay the
        #                STOPPED lifecycle event some seconds.
        if uri.find("xen://") != -1:
            self._lifecycle_delay = 15
        else:
            self._lifecycle_delay = 0

    def _native_thread(self):
        """Receives async events coming in from libvirtd.

        This is a native thread which runs the default
        libvirt event loop implementation. This processes
        any incoming async events from libvirtd and queues
        them for later dispatch. This thread is only
        permitted to use libvirt python APIs, and the
        driver.queue_event method. In particular any use
        of logging is forbidden, since it will confuse
        eventlet's greenthread integration
        """

        while True:
            libvirt.virEventRunDefaultImpl()

    def _dispatch_thread(self):
        """Dispatches async events coming in from libvirtd.

        This is a green thread which waits for events to
        arrive from the libvirt event loop thread. This
        then dispatches the events to the compute manager.
        """

        while True:
            self._dispatch_events()

    @staticmethod
    def _event_lifecycle_callback(conn, dom, event, detail, opaque):
        """Receives lifecycle events from libvirt.

        NB: this method is executing in a native thread, not
        an eventlet coroutine. It can only invoke other libvirt
        APIs, or use self._queue_event(). Any use of logging APIs
        in particular is forbidden.
        """

        self = opaque

        uuid = dom.UUIDString()
        transition = None
        if event == libvirt.VIR_DOMAIN_EVENT_STOPPED:
            transition = virtevent.EVENT_LIFECYCLE_STOPPED
        elif event == libvirt.VIR_DOMAIN_EVENT_STARTED:
            transition = virtevent.EVENT_LIFECYCLE_STARTED
        elif event == libvirt.VIR_DOMAIN_EVENT_SUSPENDED:
            transition = virtevent.EVENT_LIFECYCLE_PAUSED
        elif event == libvirt.VIR_DOMAIN_EVENT_RESUMED:
            transition = virtevent.EVENT_LIFECYCLE_RESUMED

        if transition is not None:
            self._queue_event(virtevent.LifecycleEvent(uuid, transition))

    def _close_callback(self, conn, reason, opaque):
        close_info = {'conn': conn, 'reason': reason}
        self._queue_event(close_info)

    @staticmethod
    def _test_connection(conn):
        try:
            conn.getLibVersion()
            return True
        except libvirt.libvirtError as e:
            if (e.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                       libvirt.VIR_ERR_INTERNAL_ERROR) and
                e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                         libvirt.VIR_FROM_RPC)):
                LOG.debug('Connection to libvirt broke')
                return False
            raise

    @staticmethod
    def _connect_auth_cb(creds, opaque):
        if len(creds) == 0:
            return 0
        raise exception.NovaException(
            _("Can not handle authentication request for %d credentials")
            % len(creds))

    @staticmethod
    def _connect(uri, read_only):
        auth = [[libvirt.VIR_CRED_AUTHNAME,
                 libvirt.VIR_CRED_ECHOPROMPT,
                 libvirt.VIR_CRED_REALM,
                 libvirt.VIR_CRED_PASSPHRASE,
                 libvirt.VIR_CRED_NOECHOPROMPT,
                 libvirt.VIR_CRED_EXTERNAL],
                Host._connect_auth_cb,
                None]

        flags = 0
        if read_only:
            flags = libvirt.VIR_CONNECT_RO
        # tpool.proxy_call creates a native thread. Due to limitations
        # with eventlet locking we cannot use the logging API inside
        # the called function.
        return tpool.proxy_call(
            (libvirt.virDomain, libvirt.virConnect),
            libvirt.openAuth, uri, auth, flags)

    def _queue_event(self, event):
        """Puts an event on the queue for dispatch.

        This method is called by the native event thread to
        put events on the queue for later dispatch by the
        green thread. Any use of logging APIs is forbidden.
        """

        if self._event_queue is None:
            return

        # Queue the event...
        self._event_queue.put(event)

        # ...then wakeup the green thread to dispatch it
        c = ' '.encode()
        self._event_notify_send.write(c)
        self._event_notify_send.flush()

    def _dispatch_events(self):
        """Wait for & dispatch events from native thread

        Blocks until native thread indicates some events
        are ready. Then dispatches all queued events.
        """

        # Wait to be notified that there are some
        # events pending
        try:
            _c = self._event_notify_recv.read(1)
            assert _c
        except ValueError:
            return  # will be raised when pipe is closed

        # Process as many events as possible without
        # blocking
        last_close_event = None
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get(block=False)
                if isinstance(event, virtevent.LifecycleEvent):
                    # call possibly with delay
                    self._event_emit_delayed(event)

                elif 'conn' in event and 'reason' in event:
                    last_close_event = event
            except native_Queue.Empty:
                pass
        if last_close_event is None:
            return
        conn = last_close_event['conn']
        # get_new_connection may already have disabled the host,
        # in which case _wrapped_conn is None.
        with self._wrapped_conn_lock:
            if conn == self._wrapped_conn:
                reason = str(last_close_event['reason'])
                msg = _("Connection to libvirt lost: %s") % reason
                self._wrapped_conn = None
                if self._conn_event_handler is not None:
                    self._conn_event_handler(False, msg)

    def _event_emit_delayed(self, event):
        """Emit events - possibly delayed."""
        def event_cleanup(gt, *args, **kwargs):
            """Callback function for greenthread. Called
            to cleanup the _events_delayed dictionary when a event
            was called.
            """
            event = args[0]
            self._events_delayed.pop(event.uuid, None)

        if self._lifecycle_delay > 0:
            # Cleanup possible delayed stop events.
            if event.uuid in self._events_delayed.keys():
                self._events_delayed[event.uuid].cancel()
                self._events_delayed.pop(event.uuid, None)
                LOG.debug("Removed pending event for %s due to "
                          "lifecycle event", event.uuid)

            if event.transition == virtevent.EVENT_LIFECYCLE_STOPPED:
                # Delay STOPPED event, as they may be followed by a STARTED
                # event in case the instance is rebooting, when runned with Xen
                id_ = greenthread.spawn_after(self._lifecycle_delay,
                                              self._event_emit, event)
                self._events_delayed[event.uuid] = id_
                # add callback to cleanup self._events_delayed dict after
                # event was called
                id_.link(event_cleanup, event)
            else:
                self._event_emit(event)
        else:
            self._event_emit(event)

    def _event_emit(self, event):
        if self._lifecycle_event_handler is not None:
            self._lifecycle_event_handler(event)

    def _init_events_pipe(self):
        """Create a self-pipe for the native thread to synchronize on.

        This code is taken from the eventlet tpool module, under terms
        of the Apache License v2.0.
        """

        self._event_queue = native_Queue.Queue()
        try:
            rpipe, wpipe = os.pipe()
            self._event_notify_send = greenio.GreenPipe(wpipe, 'wb', 0)
            self._event_notify_recv = greenio.GreenPipe(rpipe, 'rb', 0)
        except (ImportError, NotImplementedError):
            # This is Windows compatibility -- use a socket instead
            #  of a pipe because pipes don't really exist on Windows.
            sock = native_socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            sock.listen(50)
            csock = native_socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            csock.connect(('localhost', sock.getsockname()[1]))
            nsock, addr = sock.accept()
            self._event_notify_send = nsock.makefile('wb', 0)
            gsock = greenio.GreenSocket(csock)
            self._event_notify_recv = gsock.makefile('rb', 0)

    def _init_events(self):
        """Initializes the libvirt events subsystem.

        This requires running a native thread to provide the
        libvirt event loop integration. This forwards events
        to a green thread which does the actual dispatching.
        """

        self._init_events_pipe()

        LOG.debug("Starting native event thread")
        self._event_thread = native_threading.Thread(
            target=self._native_thread)
        self._event_thread.setDaemon(True)
        self._event_thread.start()

        LOG.debug("Starting green dispatch thread")
        eventlet.spawn(self._dispatch_thread)

    def _get_new_connection(self):
        # call with _wrapped_conn_lock held
        LOG.debug('Connecting to libvirt: %s', self._uri)
        wrapped_conn = None

        try:
            wrapped_conn = self._connect(self._uri, self._read_only)
        finally:
            # Enabling the compute service, in case it was disabled
            # since the connection was successful.
            disable_reason = None
            if not wrapped_conn:
                disable_reason = 'Failed to connect to libvirt'

            if self._conn_event_handler is not None:
                self._conn_event_handler(bool(wrapped_conn), disable_reason)

        self._wrapped_conn = wrapped_conn

        try:
            LOG.debug("Registering for lifecycle events %s", self)
            wrapped_conn.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                self._event_lifecycle_callback,
                self)
        except Exception as e:
            LOG.warn(_LW("URI %(uri)s does not support events: %(error)s"),
                     {'uri': self._uri, 'error': e})

        try:
            LOG.debug("Registering for connection events: %s", str(self))
            wrapped_conn.registerCloseCallback(self._close_callback, None)
        except (TypeError, AttributeError) as e:
            # NOTE: The registerCloseCallback of python-libvirt 1.0.1+
            # is defined with 3 arguments, and the above registerClose-
            # Callback succeeds. However, the one of python-libvirt 1.0.0
            # is defined with 4 arguments and TypeError happens here.
            # Then python-libvirt 0.9 does not define a method register-
            # CloseCallback.
            LOG.debug("The version of python-libvirt does not support "
                      "registerCloseCallback or is too old: %s", e)
        except libvirt.libvirtError as e:
            LOG.warn(_LW("URI %(uri)s does not support connection"
                         " events: %(error)s"),
                     {'uri': self._uri, 'error': e})

        return wrapped_conn

    def _get_connection(self):
        # multiple concurrent connections are protected by _wrapped_conn_lock
        with self._wrapped_conn_lock:
            wrapped_conn = self._wrapped_conn
            if not wrapped_conn or not self._test_connection(wrapped_conn):
                wrapped_conn = self._get_new_connection()

        return wrapped_conn

    def get_connection(self):
        """Returns a connection to the hypervisor

        This method should be used to create and return a well
        configured connection to the hypervisor.

        :returns: a libvirt.virConnect object
        """
        try:
            conn = self._get_connection()
        except libvirt.libvirtError as ex:
            LOG.exception(_LE("Connection to libvirt failed: %s"), ex)
            payload = dict(ip=CONF.my_ip,
                           method='_connect',
                           reason=ex)
            rpc.get_notifier('compute').error(nova_context.get_admin_context(),
                                              'compute.libvirt.error',
                                              payload)
            raise exception.HypervisorUnavailable(host=CONF.host)

        return conn

    @staticmethod
    def _libvirt_error_handler(context, err):
        # Just ignore instead of default outputting to stderr.
        pass

    def initialize(self):
        # NOTE(dkliban): Error handler needs to be registered before libvirt
        #                connection is used for the first time.  Otherwise, the
        #                handler does not get registered.
        libvirt.registerErrorHandler(self._libvirt_error_handler, None)
        libvirt.virEventRegisterDefaultImpl()
        self._init_events()

    def _version_check(self, lv_ver=None, hv_ver=None, hv_type=None,
                       op=operator.lt):
        conn = self.get_connection()
        try:
            if lv_ver is not None:
                libvirt_version = conn.getLibVersion()
                if op(libvirt_version, utils.convert_version_to_int(lv_ver)):
                    return False

            if hv_ver is not None:
                hypervisor_version = conn.getVersion()
                if op(hypervisor_version,
                      utils.convert_version_to_int(hv_ver)):
                    return False

            if hv_type is not None:
                hypervisor_type = conn.getType()
                if hypervisor_type != hv_type:
                    return False

            return True
        except Exception:
            return False

    def has_min_version(self, lv_ver=None, hv_ver=None, hv_type=None):
        return self._version_check(
            lv_ver=lv_ver, hv_ver=hv_ver, hv_type=hv_type, op=operator.lt)

    def has_version(self, lv_ver=None, hv_ver=None, hv_type=None):
        return self._version_check(
            lv_ver=lv_ver, hv_ver=hv_ver, hv_type=hv_type, op=operator.ne)

    def get_domain(self, instance):
        """Retrieve libvirt domain object for an instance.

        :param instance: an nova.objects.Instance object

        Attempt to lookup the libvirt domain objects
        corresponding to the Nova instance, based on
        its name. If not found it will raise an
        exception.InstanceNotFound exception. On other
        errors, it will raise a exception.NovaException
        exception.

        :returns: a libvirt.Domain object
        """
        return self._get_domain_by_name(instance.name)

    def _get_domain_by_id(self, instance_id):
        """Retrieve libvirt domain object given an instance id.

        All libvirt error handling should be handled in this method and
        relevant nova exceptions should be raised in response.

        """
        try:
            conn = self.get_connection()
            return conn.lookupByID(instance_id)
        except libvirt.libvirtError as ex:
            error_code = ex.get_error_code()
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise exception.InstanceNotFound(instance_id=instance_id)

            msg = (_("Error from libvirt while looking up %(instance_id)s: "
                     "[Error Code %(error_code)s] %(ex)s")
                   % {'instance_id': instance_id,
                      'error_code': error_code,
                      'ex': ex})
            raise exception.NovaException(msg)

    def _get_domain_by_name(self, instance_name):
        """Retrieve libvirt domain object given an instance name.

        All libvirt error handling should be handled in this method and
        relevant nova exceptions should be raised in response.

        """
        try:
            conn = self.get_connection()
            return conn.lookupByName(instance_name)
        except libvirt.libvirtError as ex:
            error_code = ex.get_error_code()
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise exception.InstanceNotFound(instance_id=instance_name)

            msg = (_('Error from libvirt while looking up %(instance_name)s: '
                     '[Error Code %(error_code)s] %(ex)s') %
                   {'instance_name': instance_name,
                    'error_code': error_code,
                    'ex': ex})
            raise exception.NovaException(msg)

    def _list_instance_domains_fast(self, only_running=True):
        # The modern (>= 0.9.13) fast way - 1 single API call for all domains
        flags = libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE
        if not only_running:
            flags = flags | libvirt.VIR_CONNECT_LIST_DOMAINS_INACTIVE
        return self.get_connection().listAllDomains(flags)

    def _list_instance_domains_slow(self, only_running=True):
        # The legacy (< 0.9.13) slow way - O(n) API call for n domains
        uuids = []
        doms = []
        # Redundant numOfDomains check is for libvirt bz #836647
        if self.get_connection().numOfDomains() > 0:
            for id in self.get_connection().listDomainsID():
                try:
                    dom = self._get_domain_by_id(id)
                    doms.append(dom)
                    uuids.append(dom.UUIDString())
                except exception.InstanceNotFound:
                    continue

        if only_running:
            return doms

        for name in self.get_connection().listDefinedDomains():
            try:
                dom = self._get_domain_by_name(name)
                if dom.UUIDString() not in uuids:
                    doms.append(dom)
            except exception.InstanceNotFound:
                continue

        return doms

    def list_instance_domains(self, only_running=True, only_guests=True):
        """Get a list of libvirt.Domain objects for nova instances

        :param only_running: True to only return running instances
        :param only_guests: True to filter out any host domain (eg Dom-0)

        Query libvirt to a get a list of all libvirt.Domain objects
        that correspond to nova instances. If the only_running parameter
        is true this list will only include active domains, otherwise
        inactive domains will be included too. If the only_guests parameter
        is true the list will have any "host" domain (aka Xen Domain-0)
        filtered out.

        :returns: list of libvirt.Domain objects
        """

        if not self._skip_list_all_domains:
            try:
                alldoms = self._list_instance_domains_fast(only_running)
            except (libvirt.libvirtError, AttributeError) as ex:
                LOG.info(_LI("Unable to use bulk domain list APIs, "
                             "falling back to slow code path: %(ex)s"),
                         {'ex': ex})
                self._skip_list_all_domains = True

        if self._skip_list_all_domains:
            # Old libvirt, or a libvirt driver which doesn't
            # implement the new API
            alldoms = self._list_instance_domains_slow(only_running)

        doms = []
        for dom in alldoms:
            if only_guests and dom.ID() == 0:
                continue
            doms.append(dom)

        return doms

    def get_online_cpus(self):
        """Get the set of CPUs that are online on the host

        Method is only used by NUMA code paths which check on
        libvirt version >= 1.0.4. getCPUMap() was introduced in
        libvirt 1.0.0.

        :returns: set of online CPUs, raises libvirtError on error

        """

        (cpus, cpu_map, online) = self.get_connection().getCPUMap()

        online_cpus = set()
        for cpu in range(cpus):
            if cpu_map[cpu]:
                online_cpus.add(cpu)

        return online_cpus

    def get_capabilities(self):
        """Returns the host capabilities information

        Returns an instance of config.LibvirtConfigCaps representing
        the capabilities of the host.

        Note: The result is cached in the member attribute _caps.

        :returns: a config.LibvirtConfigCaps object
        """
        if not self._caps:
            xmlstr = self.get_connection().getCapabilities()
            LOG.info(_LI("Libvirt host capabilities %s"), xmlstr)
            self._caps = vconfig.LibvirtConfigCaps()
            self._caps.parse_str(xmlstr)
            if hasattr(libvirt, 'VIR_CONNECT_BASELINE_CPU_EXPAND_FEATURES'):
                try:
                    features = self.get_connection().baselineCPU(
                        [self._caps.host.cpu.to_xml()],
                        libvirt.VIR_CONNECT_BASELINE_CPU_EXPAND_FEATURES)
                    # FIXME(wangpan): the return value of baselineCPU should be
                    #                 None or xml string, but libvirt has a bug
                    #                 of it from 1.1.2 which is fixed in 1.2.0,
                    #                 this -1 checking should be removed later.
                    if features and features != -1:
                        cpu = vconfig.LibvirtConfigCPU()
                        cpu.parse_str(features)
                        self._caps.host.cpu.features = cpu.features
                except libvirt.libvirtError as ex:
                    error_code = ex.get_error_code()
                    if error_code == libvirt.VIR_ERR_NO_SUPPORT:
                        LOG.warn(_LW("URI %(uri)s does not support full set"
                                     " of host capabilities: " "%(error)s"),
                                     {'uri': self._uri, 'error': ex})
                    else:
                        raise
        return self._caps

    def get_driver_type(self):
        """Get hypervisor type.

        :returns: hypervisor type (ex. qemu)

        """

        return self.get_connection().getType()

    def get_version(self):
        """Get hypervisor version.

        :returns: hypervisor version (ex. 12003)

        """

        return self.get_connection().getVersion()

    def get_hostname(self):
        """Returns the hostname of the hypervisor."""
        hostname = self.get_connection().getHostname()
        if self._hostname is None:
            self._hostname = hostname
        elif hostname != self._hostname:
            LOG.error(_LE('Hostname has changed from %(old)s '
                          'to %(new)s. A restart is required to take effect.'),
                          {'old': self._hostname,
                           'new': hostname})
        return self._hostname

    def find_secret(self, usage_type, usage_id):
        """Find a secret.

        usage_type: one of 'iscsi', 'ceph', 'rbd' or 'volume'
        usage_id: name of resource in secret
        """
        if usage_type == 'iscsi':
            usage_type_const = libvirt.VIR_SECRET_USAGE_TYPE_ISCSI
        elif usage_type in ('rbd', 'ceph'):
            usage_type_const = libvirt.VIR_SECRET_USAGE_TYPE_CEPH
        elif usage_type == 'volume':
            usage_type_const = libvirt.VIR_SECRET_USAGE_TYPE_VOLUME
        else:
            msg = _("Invalid usage_type: %s")
            raise exception.NovaException(msg % usage_type)

        try:
            conn = self.get_connection()
            return conn.secretLookupByUsage(usage_type_const, usage_id)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_SECRET:
                return None

    def create_secret(self, usage_type, usage_id, password=None):
        """Create a secret.

        usage_type: one of 'iscsi', 'ceph', 'rbd' or 'volume'
                           'rbd' will be converted to 'ceph'.
        usage_id: name of resource in secret
        """
        secret_conf = vconfig.LibvirtConfigSecret()
        secret_conf.ephemeral = False
        secret_conf.private = False
        secret_conf.usage_id = usage_id
        if usage_type in ('rbd', 'ceph'):
            secret_conf.usage_type = 'ceph'
        elif usage_type == 'iscsi':
            secret_conf.usage_type = 'iscsi'
        elif usage_type == 'volume':
            secret_conf.usage_type = 'volume'
        else:
            msg = _("Invalid usage_type: %s")
            raise exception.NovaException(msg % usage_type)

        xml = secret_conf.to_xml()
        try:
            LOG.debug('Secret XML: %s' % xml)
            conn = self.get_connection()
            secret = conn.secretDefineXML(xml)
            if password is not None:
                secret.setValue(password)
            return secret
        except libvirt.libvirtError:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE('Error defining a secret with XML: %s') % xml)

    def delete_secret(self, usage_type, usage_id):
        """Delete a secret.

        usage_type: one of 'iscsi', 'ceph', 'rbd' or 'volume'
        usage_id: name of resource in secret
        """
        secret = self.find_secret(usage_type, usage_id)
        if secret is not None:
            secret.undefine()

    def get_domain_info(self, virt_dom):
        return compat.get_domain_info(libvirt, self, virt_dom)
