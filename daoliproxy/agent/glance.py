import itertools

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy.agent import base

import glanceclient as glance_client

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


def glanceclient(request, version='1'):
    url = base.url_for(request.catalog, 'image')
    LOG.debug('glanceclient connection created using token "%s" and url "%s"' %
              (request.auth_token, url))
    return glance_client.Client(version, url, token=request.auth_token,
                                insecure=False, cacert=None)

def image_list_detailed(request, marker=None, filters=None, paginate=False):
    limit = 1000
    page_size = 20

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker

    images_iter = glanceclient(request).images.list(page_size=request_size,
                                                    limit=limit,
                                                    **kwargs)

    has_more_data = False
    if paginate:
        images = list(itertools.islice(images_iter, request_size))
        if len(images) > page_size:
            images.pop(-1)
            has_more_data = True
    else:
        images = list(images_iter)

    return (images, has_more_data)
