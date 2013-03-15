# -*- coding: utf-8 -*-s
from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .options import OptionsPageCollector, BaseOptionsPage
from .models import Option


def option(field, **kwargs):
    setattr(field, 'is_option', True)
    option_key = kwargs.get('option_key', None)
    if option_key and isinstance(option_key, basestring):
        setattr(field, 'option_key', option_key)
    return field

class OptionsPage(BaseOptionsPage):
    pass


#################################
# Initialize admin pages system #
#################################
admin_pages = OptionsPageCollector(admin.site)



##########################################################
# Extends django.contrib.sites admin page for model Site #
##########################################################
if getattr(settings, 'OPTIONS_CONTRIB_SITE', True) and 'django.contrib.sites' in settings.INSTALLED_APPS:
    from django.contrib.sites.admin import SiteAdmin
    from django.contrib.sites.models import Site
    from django.core.urlresolvers import reverse

    class ExtendedSiteAdmin(SiteAdmin):
        def show_site_options_url(self, obj):
            url = reverse('admin:%s_%s_changelist' %(Option._meta.app_label,  Option._meta.module_name) )
            return '<a href="%s?site__name=%s">%s(%d)</a>' % (url,
                    obj.name, _('Show Options'),
                    Option.all.filter(site__id__exact=obj.pk).count())
        show_site_options_url.allow_tags = True
        show_site_options_url.short_description = _('Show site options url')

        list_display = SiteAdmin.list_display + ('show_site_options_url',)

    admin.site.unregister(Site)
    admin.site.register(Site, ExtendedSiteAdmin)


####################
# Model for option #
####################
class OptionAdmin(admin.ModelAdmin):

    def site_name(self, obj):
        return obj.site.name
    site_name.short_description = _('Site name')

    list_display = ('key', 'value', 'site_name', 'autoload', 'created_at', 'updated_at', 'expires_at')
    list_filter = ('site__name', 'autoload')
    list_select_related = True
    ordering = ['-updated_at']
    search_fields = ['key',]

    def get_urls(self):
        from django.conf.urls import patterns, url

        return patterns('',
            url( admin_pages.url_pattern(r'^(?P<page_code>[\w\.\-_]+)/$'),
                admin_pages.view_wrap(admin_pages.as_view(), self.admin_site),
                name='options-page'),
            url( admin_pages.url_pattern(r'^(?P<page_code>[\w\.\-_]+)/history/$'),
                admin_pages.view_wrap(admin_pages.as_history_view(), self.admin_site),
                name='options-page-history'),
        ) + super(OptionAdmin,self).get_urls()



####################################
# Add actions to OptionAdmin class #
####################################

def make_autoload_on(modeladmin, request, queryset): queryset.update(autoload=True)
make_autoload_on.short_description = _("Autoload selected options")

def make_autoload_off(modeladmin, request, queryset): queryset.update(autoload=False)
make_autoload_off.short_description = _("Not Autoload selected options")

OptionAdmin.actions = [make_autoload_on, make_autoload_off]



######################################
# Register OptionAdmin to admin site #
######################################
admin.site.register(Option, OptionAdmin)
