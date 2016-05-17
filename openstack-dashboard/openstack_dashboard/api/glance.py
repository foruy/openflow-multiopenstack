from __future__ import absolute_import

import itertools
import logging

from django.conf import settings
import six.moves.urllib.parse as urlparse

import glanceclient as glance_client

from horizon.utils import functions as utils

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)

def glanceclient(request):
    o = urlparse.urlparse(base.url_for(request, 'image'))
    url = "://".join((o.scheme, o.netloc))
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('glanceclient connection created using token "%s" and url "%s"'
              % (request.token.id, url))
    return glance_client.Client('1', url, token=request.token.id,
                                insecure=insecure, cacert=cacert)


def image_list_detailed(request, req, marker=None, filters=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker

    images_iter = glanceclient(req).images.list(page_size=request_size,
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
