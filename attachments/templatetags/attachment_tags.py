from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from attachments.models import Attachment


def get_contenttype_kwargs(content_object):
    """
    Gets the basic kwargs necessary for almost all of the following tags.
    """
    kwargs = {
        'content_type': ContentType.objects.get_for_model(content_object).id,
        'object_id': getattr(
            content_object,
            'pk',
            getattr(content_object, 'id'),
        ),
    }
    return kwargs


def new_attachment_url(content_object):
    kwargs = get_contenttype_kwargs(content_object)
    return reverse('attachment_new', kwargs=kwargs)


class ObjectAttachmentsNode(template.Node):
    def __init__(self, content_object, context_name, order_by):
        self.content_object = template.Variable(content_object)
        self.context_name = context_name
        self.order_by = order_by

    def render(self, context):
        content_object = self.content_object.resolve(context)
        attachments = Attachment.objects.attachments_for_object(content_object)
        if self.order_by:
            attachments = attachments.order_by(self.order_by)
        context[self.context_name] = attachments
        return ''


def do_get_attachments(parser, token):
    bits = token.contents.split()
    error_string = "%r tag must be of format {%% get_attachments for OBJECT as CONTEXT_VARIABLE %%}" % bits[0]  # noqa
    order_by = None
    if len(bits) == 5:
        try:
            tag, word_for, content_object, word_as, context_name = bits
        except ValueError:
            raise template.TemplateSyntaxError(error_string)
    elif len(bits) == 7:
        tag, word_for, content_object, word_as, context_name, word_order_by, order_by = bits  # noqa
    else:
        raise template.TemplateSyntaxError(error_string)
    return ObjectAttachmentsNode(content_object, context_name, order_by)


register = template.Library()
register.simple_tag(new_attachment_url)
register.tag('get_attachments', do_get_attachments)
