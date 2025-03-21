from django.urls import re_path
from django.contrib import admin

import attachments.views

admin.autodiscover()

urlpatterns = (
    re_path(
        r'^(?P<content_type>\d+)/(?P<object_id>\d+)/$',
        attachments.views.list_attachments,
        name='attachment_list',
    ),
    re_path(
        r'^(?P<content_type>\d+)/(?P<object_id>\d+)/new/$',
        attachments.views.new_attachment,
        name='attachment_new',
    ),
    re_path(
        r'^(?P<attachment_id>\d+)/edit/$',
        attachments.views.edit_attachment,
        name='attachment_edit',
    ),
    re_path(
        r'^(?P<attachment_id>\d+)/delete/$',
        attachments.views.delete_attachment,
        name='attachment_delete',
    ),
)
