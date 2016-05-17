from oslo_log import log as logging

from daoliproxy.api import vm_states
from daoliproxy.i18n import _

LOG = logging.getLogger(__name__)

_STATE_MAP = {
    vm_states.ACTIVE: {
        'default': 'ACTIVE',
    },
    vm_states.BUILDING: {
        'default': 'BUILD',
    },
    vm_states.STOPPED: {
        'default': 'SHUTOFF',    
    },
    vm_states.RESIZED: {
        'default': 'VERIFY_RESIZE',
    },
    vm_states.PAUSED: {
        'default': 'PAUSED',
    },
    vm_states.SUSPENDED: {
        'default': 'SUSPENDED',
    },
    vm_states.RESCUED: {
        'default': 'RESCUE',
    },
    vm_states.ERROR: {
        'default': 'ERROR',
    },
    vm_states.DELETED: {
        'default': 'DELETED',
    },
    vm_states.SOFT_DELETED: {
        'default': 'SOFT_DELETED',
    },
    vm_states.SHELVED: {
        'default': 'SHELVED',
    },
    vm_states.SHELVED_OFFLOADED: {
        'default': 'SHELVED_OFFLOADED',
    },
}

def status_from_state(vm_state, task_state='default'):
    """Given vm_state and task_state, return a status string."""
    task_map = _STATE_MAP.get(vm_state, dict(default='UNKNOWN'))
    status = task_map.get(task_state, task_map['default'])
    if status == "UNKNOWN":
        LOG.error(_("status is UNKNOWN from vm_state=%(vm_state)s "
                    "task_state=%(task_state)s. Bad upgrade or db "
                    "corrupted?"),
                  {'vm_state': vm_state, 'task_state': task_state})
    return status
