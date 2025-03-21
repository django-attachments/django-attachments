from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from attachments.models import Attachment


class AttachmentForm(forms.ModelForm):

    def save(self, content_object, *args, **kwargs):
        self.instance.content_type = ContentType.objects.get_for_model(
            content_object)
        self.instance.object_id = content_object.pk

        return super(AttachmentForm, self).save(*args, **kwargs)

    class Meta:
        model = Attachment
        exclude = ('content_type', 'object_id', 'attached_by')


class AttachmentEditForm(forms.ModelForm):
    file = forms.FileField(required=False, label=_("file"))

    def clean_file(self):
        """
        Don't delete the old file if our edit doesn't upload a new one.
        """
        file = self.cleaned_data['file']
        if not file:
            file = self.instance.file

        return file

    class Meta:
        model = Attachment
        exclude = ('content_type', 'object_id', 'attached_by')
