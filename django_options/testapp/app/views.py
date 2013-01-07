from django.views.generic import TemplateView
from django_options import update_option, delete_option, get_option
from django_options.decorators import with_options


def loader(name=''):
    def wrapped(request):
#        logger.debug(name + ' View load options')
        key = name + '_view_prompted_value'
        update_option(key, "Loaded by %s" % name.title().replace('_',' '))
    return wrapped
def unloader(name=''):
    def wrapped(request, response):
#        logger.debug(name + ' View UNload options')
        key = name + '_view_prompted_value'
        delete_option(key)
    return wrapped


class TestView(TemplateView):
    template_name= 'index.html'

    @with_options(loader('method_decorator'), unloader('method_decorator'))
    def dispatch(self, request, *args, **kwargs):
        return super(TestView,self).dispatch(request, *args, **kwargs)

def _test_view(request):
    from django.shortcuts import render_to_response
    return render_to_response('index.html')
test_view = with_options(loader('function'), unloader('function'))(_test_view)

@with_options(loader('decorated_function'), unloader('decorated_function'))
def decorated_test_view(request):
    return _test_view(request)