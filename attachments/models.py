from __future__ import with_statement

import tempfile
import shutil

from six.moves.urllib.request import urlopen

from django.db import models, connection
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import python_2_unicode_compatible

import os.path
from datetime import datetime

from .directory_schemes import by_app
from .utils import get_callable_from_string, set_slug_field


qn = connection.ops.quote_name

# Get relative media path
try:
    ATTACHMENT_DIR = settings.ATTACHMENT_DIR
except Exception:
    ATTACHMENT_DIR = "attachments"


class AttachmentManager(models.Manager):
    """
    Methods borrowed from django-threadedcomments
    """

    def _generate_object_kwarg_dict(self, content_object, **kwargs):
        """
        Generates the most comment keyword arguments for a given
        ``content_object``.
        """
        kwargs['content_type'] = ContentType.objects.get_for_model(
            content_object,
        )
        try:
            kwargs['object_id'] = content_object.pk
        except AttributeError:
            kwargs['object_id'] = content_object.id
        return kwargs

    def create_for_object(self, content_object, **kwargs):
        """
        A simple wrapper around ``create`` for a given ``content_object``.
        """
        return self.create(
            **self._generate_object_kwarg_dict(content_object, **kwargs)
        )

    def attachments_for_object(
            self, content_object, file_name=None, title=None, **kwargs):
        """
        Prepopulates a QuerySet with all attachments related to the given
        ``content_object``.
        """
        query = self.filter(
            **self._generate_object_kwarg_dict(content_object, **kwargs)
        )
        if file_name:
            query = query.filter(file__iendswith=file_name)
        if title:
            query = query.filter(title=title)

        return query

    def _get_usage(
        self,
        model,
        counts=False,
        min_count=None,
        extra_joins=None,
        extra_criteria=None,
        params=None,
    ):
        """
        Perform the custom SQL query for ``usage_for_model`` and
        ``usage_for_queryset``.
        """
        if min_count is not None:
            counts = True

        model_table = qn(model._meta.db_table)
        model_pk = '%s.%s' % (model_table, qn(model._meta.pk.column))

        # Grab all of the attachment fields
        field_cols = [field.attname for field in self.model._meta.local_fields]
        quoted_field_cols = [qn(col) for col in field_cols]
        attachment = qn(self.model._meta.db_table)
        table_field_cols = [
            '%s.%s' % (attachment, col)
            for col in quoted_field_cols
        ]
        query = """
        SELECT DISTINCT %(fields)s%(count_sql)s
        FROM
            %(attachment)s
            INNER JOIN %(model)s
                ON %(attachment)s.object_id = %(model_pk)s
            %%s
        WHERE %(attachment)s.content_type_id = %(content_type_id)s
            %%s
        GROUP BY %(attachment)s.id
        %%s
        ORDER BY %(attachment)s.id ASC""" % {
            'fields': ', '.join(table_field_cols),
            'attachment': attachment,
            'count_sql': counts and (', COUNT(%s)' % model_pk) or '',
            'model': model_table,
            'model_pk': model_pk,
            'content_type_id': ContentType.objects.get_for_model(model).pk,
        }

        min_count_sql = ''
        if min_count is not None:
            min_count_sql = 'HAVING COUNT(%s) >= %%s' % model_pk
            params.append(min_count)

        cursor = connection.cursor()
        cursor.execute(
            query % (
                extra_joins,
                extra_criteria,
                min_count_sql,
            ),
            params,
        )
        attachments = []
        for row in cursor.fetchall():
            if counts:
                field_row = row[:-1]
            else:
                field_row = row
            result_tuple = zip(field_cols, field_row)
            result_dict = {}
            for col, val in result_tuple:
                result_dict[col] = val
            a = self.model(**result_dict)
            if counts:
                a.count = row[-1:]
            attachments.append(a)
        return attachments

    def usage_for_queryset(self, queryset, counts=False, min_count=None):
        """
        Obtain a list of tags associated with instances of a model
        contained in the given queryset.

        If ``counts`` is True, a ``count`` attribute will be added to
        each tag, indicating how many times it has been used against
        the Model class in question.

        If ``min_count`` is given, only tags which have a ``count``
        greater than or equal to ``min_count`` will be returned.
        Passing a value for ``min_count`` implies ``counts=True``.
        """

        extra_joins = ' '.join(queryset.query.get_from_clause()[0][1:])
        where, params = queryset.query.where.as_sql()
        if where:
            extra_criteria = 'AND %s' % where
        else:
            extra_criteria = ''
        return self._get_usage(
            queryset.model,
            counts,
            min_count,
            extra_joins,
            extra_criteria,
            params,
        )

    def copy_attachments(
        self,
        from_object,
        to_object,
        deepcopy=False,
        save_attachments=True,
    ):
        """
        Copy all of the attachments on from_object to to_object. The
        fields will be pointing at the same file unless deepcopy is False.
        """
        # First delete all of the attachments on the to_object
        old_attachments = self.attachments_for_object(to_object)
        old_attachments.delete()

        attachments = self.attachments_for_object(from_object)

        return [
            attachment.copy(
                to_object,
                deepcopy,
                save_attachments,
            )
            for attachment in attachments
        ]


def get_attachment_dir(instance, filename):
    """
    The attachment directory to store the file in.

    Builds the location based on the ATTACHMENT_STORAGE_DIR setting which
    is a callable (in the same string format as TEMPLATE_LOADERS) that
    takes an attachment and a filename and then returns a string.
    """
    if getattr(settings, 'ATTACHMENT_STORAGE_DIR', None):
        try:
            dir_builder = get_callable_from_string(
                settings.ATTACHMENT_STORAGE_DIR)
        except ImproperlyConfigured:
            # Callable didn't load correctly
            dir_builder = by_app
    else:
        dir_builder = by_app

    return dir_builder(instance, filename)


@python_2_unicode_compatible
class Attachment(models.Model):

    file = models.FileField(_("file"), upload_to=get_attachment_dir,
                            max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    attached_timestamp = models.DateTimeField(_("date attached"),
                                              default=datetime.now)
    title = models.CharField(_("title"), max_length=200, blank=True, null=True)
    slug = models.SlugField(_("slug"), editable=False)
    summary = models.TextField(_("summary"), blank=True, null=True)
    attached_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("attached by"),
        related_name="attachment_attached_by",
        editable=False,
        on_delete=models.CASCADE,
    )

    objects = AttachmentManager()

    class Meta:
        ordering = ['-attached_timestamp']
        get_latest_by = 'attached_timestamp'
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')

    def __str__(self):
        return self.title or self.file_name()

    def save(self, force_insert=False, force_update=False, **kwargs):
        set_slug_field(self, self.title)
        if not self.title:
            self.title = self.file_name()
        super(Attachment, self).save(force_insert, force_update)

    def file_url(self):
        return self.file.url

    def file_name(self):
        """
        Outputs just the file's name and extension without the full path.
        """
        return os.path.basename(self.file.name)

    def copy(self, to_object, deepcopy=False, save_attachment=True):
        """
        Create a copy of this attachment that's attached to to_object instead
        of the current content_object. If deepcopy is set to true, the file
        will be copied instead of both attachments pointing at the same file.

        Convoluted copying is needed in order for the upload_to function in the
        FileField to actually be evaluated properly.
        """
        copy = Attachment()

        copy.title = self.title
        copy.slug = self.slug
        copy.summary = self.summary
        copy.attached_by_id = self.attached_by_id

        # Modify the generic FK so that it points to the 'to_object'
        kwargs_dict = Attachment.objects._generate_object_kwarg_dict(to_object)
        for field, value in kwargs_dict.items():
            setattr(copy, field, value)

        # Handle empty files and shallow copies.
        if not deepcopy or not self.file:
            copy.file = self.file
            if save_attachment:
                copy.save()
            return copy

        try:
            path = self.file.path
        except NotImplementedError:
            # Not a local file, download it to copy it.
            # The file system backend doesn't support absolute paths. DL the
            # file.
            try:
                remote_f = urlopen(self.file.url)
            except IOError:
                # Possible S3 propogation delay problem. Give it another try
                remote_f = urlopen(self.file.url)
            local_f = tempfile.NamedTemporaryFile()
            shutil.copyfileobj(remote_f, local_f)
        else:
            local_f = open(path)

        new_file = File(local_f)
        new_file.seek(0)
        copy.file.save(self.file_name(), new_file, save=save_attachment)
        if save_attachment:
            copy.save()
        local_f.close()
        return copy
