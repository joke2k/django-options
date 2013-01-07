from django import template
from ..const import SEPARATOR, PREFIX, TITLE_SEPARATOR

register = template.Library()


@register.assignment_tag
def get_admin_log(limit, user=None, page=None):

    from django.db.models import Q
    from django_options import Option
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType

    # initialize queryset with content type filter
    queryset = LogEntry.objects.filter(
        content_type__id__exact=ContentType.objects.get_for_model(Option).pk
    )

    if user:
        queryset = queryset.filter(user__id__exact=user.pk)

    if page:
        page_code = PREFIX + page.get_code()
        queryset = queryset.filter( Q(object_id= page_code ) | Q(object_id__startswith= page_code + SEPARATOR) )

    return queryset.select_related('content_type', 'user')[:limit]


@register.assignment_tag
def options_pages():
    from django_options.admin import admin_pages
    return admin_pages.pages

@register.filter
def sub_pages_only(title, page):
    full_title = (page.parent if page.parent else page).full_title()
    return title.replace(full_title + TITLE_SEPARATOR,'')
