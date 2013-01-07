from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


class OptionsLoaderMiddleware(object):

    def __init__(self):
        # initialize OptionsLoaderMiddleware

        from django.conf import settings

        self.loaders = []

        for loader_path in getattr(settings, 'OPTIONS_LOADERS', getattr(settings, 'options_loaders', [])) :

            try:
                mw_module, mw_classname = loader_path.rsplit('.', 1)
            except ValueError:
                raise ImproperlyConfigured('%s isn\'t a options loader module' % loader_path)
            try:
                mod = import_module(mw_module)
            except ImportError, e:
                raise ImproperlyConfigured('Error importing options loader %s: "%s"' % (mw_module, e))
            try:
                mw_class = getattr(mod, mw_classname)
            except AttributeError:
                raise ImproperlyConfigured('Options loader module "%s" does not define a "%s" class' % (mw_module, mw_classname))

            assert hasattr(mw_class, 'load_options') or hasattr(mw_class, 'unload_options'), 'Class provided in OPTIONS_LOADERS "%s" has not load_options or unload_options class methods'

            self.loaders.append(mw_class)

    def process_request(self, request):

        for loader in self.loaders:

            load = getattr(loader, 'load_options', None)

            if not load: continue

            load(request)



    def process_response(self, request, response):

        for loader in self.loaders[::-1]:

            unload = getattr(loader, 'unload_options', None)

            if not unload: continue

            unload(request, response)

        return response



