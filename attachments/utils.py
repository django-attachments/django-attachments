from django.template.defaultfilters import slugify
from django.core.exceptions import ImproperlyConfigured

import re


def set_slug_field(
        instance, value, slug_field_name='slug', slug_separator='-'):
    """
    Calculates a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    from http://www.djangosnippets.org/snippets/690/
    """

    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug. Chop its length down if we need to.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator=None):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
        value = re.sub('%s+' % re_sep, separator, value)
    return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)


def get_callable_from_string(path):
    """
    Gets a callable from a string representing an import
    (eg. django.template.loaders.filesystem.load_template_source).
    Adapted from django.template.loader.find_template_source
    """
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = __import__(module, globals(), locals(), [attr])
    except ImportError as e:
        raise ImproperlyConfigured(
            'Error importing callable %s: "%s"' % (module, e),
        )
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a "%s" callable' % (module, attr),
        )

    return func
