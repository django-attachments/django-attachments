from contextlib import contextmanager
from datetime import datetime
from tempfile import NamedTemporaryFile

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.urls import reverse
from django.db import models
from django.test import TestCase
from django.utils.encoding import force_str

from attachments.models import Attachment, get_attachment_dir


User = get_user_model()


class TestModel(models.Model):
    """
    This model is simply used by this application's test suite as a model to
    which to attach files.
    """
    name = models.CharField(max_length=32)
    date = models.DateTimeField(default=datetime.now)


class TestAttachmentCopying(TestCase):
    def setUp(self):
        self.bob = User.objects.create(username="bob")
        self.bob.set_password('pw')
        self.bob.save()
        assert self.client.login(username='bob', password='pw')

        self.content_type = ContentType.objects.get_for_model(TestModel)
        self.tm = TestModel.objects.create(name="Test1")
        self.tm2 = TestModel.objects.create(name="Test2")

    @contextmanager
    def open(self, text=None):
        if text is None:
            text = 'some test text'
        with NamedTemporaryFile('w+') as f:
            f.write(text)
            f.flush()
            f.seek(0)
            yield File(f)

    def create_attachment(self, obj, **kwargs):
        att1 = Attachment.objects.create_for_object(obj, **kwargs)
        with self.open() as f:
            att1.file.save('models.py', f)
        return att1

    def test_deep_copying(self):
        """
        Test that doing a deep copy of a file actually attempt to create a
        second version of a file.
        """
        att1 = self.create_attachment(
            self.tm,
            attached_by=self.bob,
            title="Something",
            summary="Something",
        )

        att1.copy(self.tm2, deepcopy=True)

        # Ensure the saved_copy uses its proper file path
        attachments = Attachment.objects.attachments_for_object(self.tm2)
        for attachment in attachments:
            self.assertEqual(
                attachment.file.name,
                get_attachment_dir(
                    attachment,
                    attachment.file_name(),
                ),
            )

    def test_view_smoke_test(self):
        url = reverse(
            'attachment_list',
            kwargs={
                'content_type': self.content_type.pk,
                'object_id': self.tm.pk,
            },
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_delete_attachment(self):
        attachment = self.create_attachment(
            self.tm,
            attached_by=self.bob,
            title="Something",
            summary="Something",
        )
        url = reverse(
            'attachment_delete',
            kwargs={
                'attachment_id': attachment.pk,
            },
        )
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        with self.assertRaises(Attachment.DoesNotExist):
            Attachment.objects.get(pk=attachment.pk)

    def test_GET_create_attachment(self):
        url = reverse(
            'attachment_new',
            kwargs={
                'content_type': self.content_type.pk,
                'object_id': self.tm.pk,
            },
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_GET_edit_attachment(self):
        attachment = self.create_attachment(
            self.tm,
            attached_by=self.bob,
            title="Something",
            summary="Something",
        )
        url = reverse(
            'attachment_edit',
            kwargs={
                'attachment_id': attachment.pk,
            },
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_text_of_attachment_is_title(self):
        attachment = self.create_attachment(
            self.tm,
            attached_by=self.bob,
            title='Foo bar title',
        )
        self.assertEqual(force_str(attachment), 'Foo bar title')
