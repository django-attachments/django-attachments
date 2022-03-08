from django.conf import settings

import os.path


def site_based(attachment, filename):
    site_name = getattr(settings, "SITE_NAME", 'default')
    model_string = '%s_%s' % (
        attachment.content_type.model.lower(),
        attachment.content_type.pk,
    )
    return os.path.join(
        'attachments',
        site_name,
        model_string,
        str(attachment.content_object.pk),
        filename
    )


def by_app(attachment, filename):
    """
    Default for barTC's scheme on github. Thanks bartTC
    """
    model_string = '%s_%s' % (
        attachment.content_type.app_label,
        attachment.content_type.model.lower()
    )
    return os.path.join(
        'attachments',
        model_string,
        str(attachment.content_object.pk),
        filename
    )


def one_folder(attachment, filename):
    return os.path.join('attachments', filename)
