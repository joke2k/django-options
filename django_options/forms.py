from django import forms
from django.conf import settings
from django.contrib.admin.helpers import Fieldset

from . import update_option, get_option, delete_option
from .const import REQUEST_CODE_KEY, SEPARATOR, TITLE_SEPARATOR
from .helpers import AdminElement


class OptionsForm(forms.Form, AdminElement):

    page = None
    not_options = None
    optionsets = None
    options = None
    readonly_fields=None

    def _get_key(self, key):
        if hasattr(self.fields[key], 'option_key'):
            return self.fields[key].option_key
        return key

    def __init__(self, *args, **kwargs):
        super(OptionsForm, self).__init__(*args, **kwargs)

        self.not_options = kwargs.pop('not_options',self.not_options) or ()
        self.readonly_fields = kwargs.pop('readonly_fields',self.readonly_fields) or ()

        for key in self.get_option_fields():

            value = get_option( self._get_key(key) )

            if key in self.initial and value == self.initial[key]:
                continue

            # all options has initial value
            self.initial[key] = value
            if self.initial[key] and isinstance(self.fields[key], forms.FileField):

                from django.core.files.storage import default_storage
                from django.db.models.fields.files import FieldFile
                self.initial[key] = FieldFile(None, type('StumbField',(object,),{'storage': default_storage}), self.initial[key] )

        self.fields[REQUEST_CODE_KEY] = forms.CharField(widget=forms.HiddenInput, max_length=255, initial= self.get_code() )

    @classmethod
    def full_title(cls):
        return cls.page.full_title() + TITLE_SEPARATOR + (cls.title or cls.code.title())

    def save(self):
        results = []
        for key in self.get_option_fields():
            # save all options
            value = self.cleaned_data[key]

            if isinstance(self.fields[key], forms.FileField):
                import os
                from django.core.files.storage import default_storage


                if value is False:
                    default_storage.delete( get_option( self._get_key(key) ) )
                    delete_option( self._get_key(key) )
#                    results.append((key,delete_option(key)))
                    continue
                elif value is None:
                    continue

                if get_option( self._get_key(key) ) == value.name:
                    continue

                path = os.path.join( u'site-images-%s' % unicode(settings.SITE_ID) , value.name )
                default_storage.save( path, value )
                value = path

            update_option( self._get_key(key) , value)
#            results.append((key,update_option(key, value)))
#        return dict(results)


    def get_option_fields(self):
        for key, field in self.fields.items():
            if key in self.not_options: continue
            elif not getattr(field, 'is_option', False): continue
            yield key


    def __iter__(self):
        for name, options in self.get_optionsets():
            yield Fieldset(self, name, readonly_fields=self.readonly_fields, **options )

    def get_optionsets(self):
        "Hook for specifying fieldsets for the add form."
        if self.declared_optionsets:
            return self.declared_optionsets
        return [(None, {'fields': self.base_fields.keys() })]

    def _declared_optionsets(self):
        if self.optionsets:
            return self.optionsets
        elif self.options:
            return [(None, {'fields': self.options})]
        return None
    declared_optionsets = property(_declared_optionsets)

    def _media(self):
        media = None
        for fs in self:
            if not media:
                media = fs.media
            else:
                media = media + fs.media
        return media
    media = property(_media)

    @classmethod
    def get_code(cls, separator=SEPARATOR):
        code = super(OptionsForm, cls).get_code()
        return cls.page.get_code() + separator + code

    def hidden_fields(self):
        """
        Returns a list of all the BoundField objects that are hidden fields.
        Useful for manual form layout in templates.
        """
        return [self[field] for field in self.fields.keys() if self[field].is_hidden]

    def visible_fields(self):
        """
        Returns a list of BoundField objects that aren't hidden fields.
        The opposite of the hidden_fields() method.
        """
        return [self[field] for field in self.fields.keys() if not self[field].is_hidden]

