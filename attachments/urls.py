from django.conf.urls import url
from django.contrib import admin

import attachments.views

admin.autodiscover()

urlpatterns = (
    url(
        r'^(?P<content_type>\d+)/(?P<object_id>\d+)/$',
        attachments.views.list_attachments,
        name='attachment_list',
    ),
    url(
        r'^(?P<content_type>\d+)/(?P<object_id>\d+)/new/$',
        attachments.views.new_attachment,
        name='attachment_new',
    ),
    url(
        r'^(?P<attachment_id>\d+)/edit/$',
        attachments.views.edit_attachment,
        name='attachment_edit',
    ),
    url(
        r'^(?P<attachment_id>\d+)/delete/$',
        attachments.views.delete_attachment,
        name='attachment_delete',
    ),
)
