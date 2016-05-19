"""
URL patterns for Daolicloud Dashboard.
"""

from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls.static import static
from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import horizon

from openstack_dashboard import views
from openstack_dashboard.auth import views as auth_views

urlpatterns = patterns('openstack_dashboard.views',
    url(r'^$', 'splash', name='splash'),
    url(r"^index/$", "index", name='index'),
    url(r"^login/$", "login", name='login'),
    url(r"^logout/$", 'logout', name='logout'),
    url(r"^register/$", 'register', name='register'),
    url(r"^jump/$", 'jump', name='jump'),
    url(r"^check_only/$", 'checkdata', name='checkdata'),
    url(r'^message/$', auth_views.message, name='message'),
    url(r"^getpassword/$", auth_views.GetPasswordView.as_view(),
                           name='getpassword'),
    url(r"^passwordreset/$", auth_views.ResetPasswordView.as_view(),
                             name='passwordreset'),
    url(r'', include(horizon.urls)),
)

# Development static app and project media serving using the staticfiles app.
urlpatterns += staticfiles_urlpatterns()

# Convenience function for serving user-uploaded media during
# development. Only active if DEBUG==True and the URL prefix is a local
# path. Production media should NOT be served by Django.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^500/$', 'django.views.defaults.server_error')
    )
