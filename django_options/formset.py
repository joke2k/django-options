from django import forms
from django.conf import settings
from django.contrib.admin.helpers import normalize_fieldsets, AdminReadonlyField, AdminField
from django.contrib.admin.templatetags.admin_static import static
from django.utils.safestring import mark_safe

class AdminForm(object):
    def __init__(self, form, fieldsets, readonly_fields=None):
        self.form, self.fieldsets = form, normalize_fieldsets(fieldsets)
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for name, options in self.fieldsets:
            yield Fieldset(self.form, name,
                readonly_fields=self.readonly_fields,
                **options
            )

    def first_field(self):
        try:
            fieldset_name, fieldset_options = self.fieldsets[0]
            field_name = fieldset_options['fields'][0]
            if not isinstance(field_name, basestring):
                field_name = field_name[0]
            return self.form[field_name]
        except (KeyError, IndexError):
            pass
        try:
            return iter(self.form).next()
        except StopIteration:
            return None

    def _media(self):
        media = self.form.media
        for fs in self:
            media = media + fs.media
        return media
    media = property(_media)



class Fieldset(object):
    def __init__(self, form, name=None, readonly_fields=(), fields=(), classes=(),
                 description=None):
        self.form = form
        self._name, self.fields = name, fields
        self.classes = u' '.join(classes)
        self._description = description
        self.readonly_fields = readonly_fields

    @property
    def name(self):
        return self._name if self._name else self.form.title

    @property
    def description(self):
        return self._description if self._description else self.form.description

    def _media(self):
        if 'collapse' in self.classes:
            extra = '' if settings.DEBUG else '.min'
            js = ['jquery%s.js' % extra,
                  'jquery.init.js',
                  'collapse%s.js' % extra]
            return forms.Media(js=[static('admin/js/%s' % url) for url in js])
        return forms.Media()
    media = property(_media)

    def __iter__(self):
        for field in self.fields:
            yield Fieldline(self.form, field, self.readonly_fields)


class Fieldline(object):
    def __init__(self, form, field, readonly_fields=None, model_admin=None):
        self.form = form # A django.forms.Form instance
        if not hasattr(field, "__iter__"):
            self.fields = [field]
        else:
            self.fields = field
        self.model_admin = model_admin
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for i, field in enumerate(self.fields):
            if field in self.readonly_fields:
                yield SingleReadonlyField(self.form, field, is_first=(i == 0))
            else:
                yield SingleField(self.form, field, is_first=(i == 0))

    def errors(self):
        return mark_safe(u'\n'.join([self.form[f].errors.as_ul() for f in self.fields if f not in self.readonly_fields]).strip('\n'))


class SingleField(AdminField):
    pass
#    def __init__(self, form, field, is_first):
#        super(SingleField, self).__init__(form, field, is_first)
#        self.field = form[field] # A django.forms.BoundField instance
#        self.is_first = is_first # Whether this field is first on the line
#        self.is_checkbox = isinstance(self.field.field.widget, forms.CheckboxInput)


class SingleReadonlyField(AdminReadonlyField):
    def __init__(self, form, field, is_first):
        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        if callable(field):
            class_name = field.__name__ != '<lambda>' and field.__name__ or ''
        else:
            class_name = field
        self.field = {
            'name': class_name,
            'label': form[field].label,
            'field': field,
            'help_text': form[field].help_text
        }
        self.form = form
        self.is_first = is_first
        self.is_checkbox = False
        self.is_readonly = True

    def contents(self):
        return self.form[self.field]