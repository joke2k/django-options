
class TestOptionsLoader(object):

    @classmethod
    def load_options(cls, request):
        from django_options import add_option, get_option
        add_option('options_loader_prompted_value','This value is loaded and initialized in load_options() class method')

    @classmethod
    def unload_options(cls, request, response):
        from django_options import get_option, delete_option
        delete_option('options_loader_prompted_value')