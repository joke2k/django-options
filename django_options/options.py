from functools import update_wrapper
from django import forms
from django.conf import settings
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from . import models, signals
from .formset import AdminForm
from .helpers import HierarchicalClass
from .const import *


class OptionsPageCollector():

    def __init__(self, admin_site):
        self.pages = []
        self.admin_site =admin_site

    def register(self, pageView):

        if pageView in self.pages: return

        # prepare form classes
        form_classes = pageView.form_class_list[:]
        if pageView.form_class:
            form_classes.insert(0,pageView.form_class)
        if not form_classes:
            # autoload inner OptionForm classes
            from django_options.forms import OptionsForm
            form_classes = OptionsForm.nested_classes_in(pageView)

        setattr(pageView,'form_class_list',form_classes)

        if pageView.parent:
            page = self.get_page(pageView.parent.code)
            if not page:
                raise ImproperlyConfigured('Cannot register a page "%s" with un-registered page "%s"' % (pageView.code, pageView.parent.code))
            page.addChild(pageView)
        else:
            self.pages.append( pageView )

        # auto register nested PageAdmin classes
        for nestedView in BaseOptionsPage.nested_classes_in(pageView):
            setattr(nestedView, 'parent', pageView)
            self.register( nestedView )


    def get_page(self, code):
        for page in self.pages:
            if page.code == code:
                return page
            elif code.startswith( page.code + SEPARATOR ):
                return page.getChild( code )
        return None

    def as_view(self,**initkwargs):

        @staff_member_required
        def view(request, *args, **kwargs):
            pageView = self.get_page(kwargs.get('page_code'))(**initkwargs)
            if hasattr(pageView, 'get') and not hasattr(pageView, 'head'):
                pageView.head = pageView.get

            return pageView.dispatch(request, *args, **kwargs)

        return view

    def as_history_view(self):

        @staff_member_required
        def view(request, page_code):
            """The 'history' admin view for this model."""
            from django.contrib.admin.models import LogEntry
            from django.template.response import TemplateResponse
            from django.db.models import Q
            model = models.Option
            action_list = LogEntry.objects.filter(
                content_type__id__exact = ContentType.objects.get_for_model(model).id
            ).select_related().order_by('action_time')
            full_page_code = PREFIX + page_code
            if request.GET.get('full',False):
                action_list = action_list.filter(Q(object_id= full_page_code ) | Q(object_id__startswith= full_page_code + SEPARATOR))
            else:
                action_list = action_list.filter(object_id = full_page_code)

            # If no history was found, see whether this object even exists.
            obj = self.get_page(page_code)
            context = {
                'title': _('Options changes history'),
                'action_list': action_list,
                'current_page': obj,
                'is_full_history': request.GET.get('full',False)
            }

            return TemplateResponse(request, 'admin/options_page_history.html', context)

        return view

    def url_pattern(self, url):
        if url[0] == '^':
            return url[0] + PREFIX_URL_PATTERN + url[1:]
        return PREFIX_URL_PATTERN + url

    def view_wrap(self, view, admin_site):
        def wrapper(*args, **kwargs):
            return admin_site.admin_view(view)(*args, **kwargs)
        return update_wrapper(wrapper, view)


class BaseOptionsPage(FormView, HierarchicalClass):

    template_name = 'admin/options_page.html'
    form_class = None
    form_class_list = []
    do_not_call_in_templates = True

    def __init__(self, **kwargs):
        super(BaseOptionsPage,self).__init__(**kwargs)

        form_list_from_class = self.__class__.form_class_list[:]

        self.form_class_list = []

        for form_class in form_list_from_class:
            self.addForm(form_class)


    @classmethod
    def full_title(cls):
        if not hasattr(cls,'parent') or not cls.parent:
            return cls.title
        return cls.parent.full_title() + TITLE_SEPARATOR + (cls.title or cls.code.title())

    def get_context_data(self, **kwargs):
        context = super(BaseOptionsPage, self).get_context_data(**kwargs)
        #        context['options_page_list'] = option_pages.pages
        context['current_page'] = self.__class__

        return context

    def get(self, request, *args, **kwargs):
        """
        Override to allow multiple form
        """
        context = {
            'sections': [],
            'media': self.media
        }

        for form_class in self.form_class_list:
            form_instance = form_class()
            adminForm = AdminForm(
                form_instance,
                form_instance.get_optionsets()
            )
            context['sections'].append(adminForm)
            context['media'] += adminForm.media

        return self.render_to_response(self.get_context_data(**context))


    def log_form_saved(self,form , actions):
        """
        Logging with contrib LogEntry model, useful information
        to check latest changes of options form.

        :return: message of log
        """
        def make_list(elements):
            if not elements: return ''

            copy_elements = elements[:]
            last = copy_elements.pop()

            if not copy_elements: return last
            return _("%(elements)s and %(last)s") % { 'elements': ", ".join(copy_elements), 'last': last }

        list_dict = lambda x: {'element_list': make_list(actions[x]) }

        message = []
        if actions['added']:
            message.append(_("%(element_list)s is added.") % list_dict('added'))

        if actions['edited']:
            message.append(_("%(element_list)s is edited.") % list_dict('edited'))

        if actions['deleted']:
            message.append(_("%(element_list)s is deleted.") % list_dict('deleted'))

        message = _("%(option_page)s: %(actions)s") % {
            'option_page': force_unicode(form.full_title()),
            'actions': " ".join(message)
        }


        from django.contrib.admin.models import LogEntry, CHANGE

        LogEntry.objects.log_action(
            user_id         = self.request.user.pk,
            content_type_id = ContentType.objects.get_for_model(models.Option).pk,
            object_id       = PREFIX + self.get_code(),
            object_repr     = force_unicode(form.full_title()),
            action_flag     = CHANGE,
            change_message  = message
        )

        return message


    def form_valid(self, form):
        """
        Save a form and log results
        """
        actions= {
            'added' : [],
            'edited' : [],
            'deleted' : []
        }

        def collect_change_messages(sender, **kwargs):
            option = kwargs.pop('option')
            new_value = kwargs.pop('new_value')
            old_value = kwargs.pop('old_value')

            if old_value is None:
                actions['added'].append(option)
            elif new_value is None:
                actions['deleted'].append(option)
            elif old_value != new_value:
                actions['edited'].append(option)

        signals.option_value_changed.connect(collect_change_messages)

        form.save()

        signals.option_value_changed.disconnect(collect_change_messages)

        from django.contrib import messages

        if actions['added'] or actions['edited'] or actions['deleted']:
            messages.success(self.request, self.log_form_saved(form, actions))
        else:
            messages.warning(self.request, _("Not option changes"))

        self.success_url = reverse('admin:options-page', kwargs={'page_code':self.get_code()})
        return super(BaseOptionsPage, self).form_valid(form)


    def form_invalid(self, form):
        """
        Prepare context for admin form errors
        """
        sections = []
        media = self.media
        for form_class in self.form_class_list:
            form_instance = form_class() if not isinstance(form, form_class) else form
            adminForm = AdminForm(
                form_instance,
                form_instance.get_optionsets()
            )
            sections.append(adminForm)
            media += adminForm.media

        context = {
            'sections': sections,
            'media': media
        }

        from django.contrib import messages
        messages.error(self.request, _("Check form errors"))

        return self.render_to_response(self.get_context_data(**context))

    def get_form_class(self):
        """
        Override to allow single form submit
        """
        request_code = self.request.POST.get(REQUEST_CODE_KEY)

        assert request_code.startswith( self.get_code() ), "OptionsForm has invalid code"

        for form in self.form_class_list:
            if form.get_code() == request_code:
                return form

        return None

    def addForm(self, form):
        form.page = self
        self.form_class_list.append(form)


    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js',
            'admin/RelatedObjectLookups.js',
            'jquery%s.js' % extra,
            'jquery.init.js'
        ]
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])

