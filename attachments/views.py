import json

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core import serializers

from attachments.models import Attachment
from attachments.forms import AttachmentForm, AttachmentEditForm


@login_required
def new_attachment(
    request,
    content_type,
    object_id,
    template_name='attachments/new_attachment.html',
    form_cls=AttachmentForm,
    redirect=lambda object, attachment: object.get_absolute_url(),
):
    object_type = get_object_or_404(ContentType, id=int(content_type))
    try:
        object = object_type.get_object_for_this_type(pk=int(object_id))
    except object_type.DoesNotExist:
        raise Http404
    if request.method == "POST":
        attachment_form = form_cls(request.POST, request.FILES)
        if attachment_form.is_valid():
            attachment = attachment_form.save(content_object=object,
                                              commit=False)
            attachment.attached_by = request.user
            attachment.save()
            if callable(redirect):
                return HttpResponseRedirect(redirect(object, attachment))
            else:
                return HttpResponseRedirect(redirect)
    else:
        attachment_form = form_cls()

    return render_to_response(template_name, {
        "form": attachment_form,
        "object": object
    }, context_instance=RequestContext(request))


@login_required
def edit_attachment(
    request,
    attachment_id,
    template_name='attachments/edit_attachment.html',
    form_cls=AttachmentEditForm,
    redirect=lambda object, attachment: object.get_absolute_url(),
):
    attachment = get_object_or_404(Attachment, pk=attachment_id)

    if request.method == "POST":
        attachment_form = form_cls(request.POST, request.FILES,
                                   instance=attachment)
        if attachment_form.is_valid():
            attachment = attachment_form.save(commit=False)
            attachment.attached_by = request.user
            attachment.save()
            if callable(redirect):
                return HttpResponseRedirect(redirect(object, attachment))
            else:
                return HttpResponseRedirect(redirect)
    else:
        attachment_form = form_cls(instance=attachment)

    return render_to_response(template_name, {
        "form": attachment_form,
    }, context_instance=RequestContext(request))


@login_required
def delete_attachment(request, attachment_id, redirect=None):
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if request.method == "POST":
        attachment.delete()

    if redirect:
        if callable(redirect):
            return HttpResponseRedirect(redirect(object, attachment))
        else:
            return HttpResponseRedirect(redirect)
    else:
        message = {'success': True}
        content = json.dumps(message, ensure_ascii=False)
        return HttpResponse(content, content_type='application/json')


@login_required
def list_attachments(request, content_type, object_id, order_by=None,
                     template_name='attachments/list_attachments.html'):
    object_type = get_object_or_404(ContentType, id=int(content_type))
    try:
        object = object_type.get_object_for_this_type(pk=int(object_id))
    except object_type.DoesNotExist:
        raise Http404

    attachments = Attachment.objects.attachments_for_object(object)

    if order_by:
        attachments = attachments.order_by(*order_by)

    data = serializers.serialize('json', attachments)
    return HttpResponse(data, content_type='application/json')
