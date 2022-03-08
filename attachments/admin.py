from django.contrib import admin
from attachments.models import Attachment


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file", "title", "summary", "attached_timestamp", "attached_by")  # noqa E501


admin.site.register(Attachment, AttachmentAdmin)
