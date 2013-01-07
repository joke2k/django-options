from functools import wraps
from django.utils.decorators import decorator_from_middleware

def with_options(loader=None, unloader=None):
    """
    Prepare view execution with loader/unloader of options
    """

    def wrapper(F):
        class OptionLoader(object):
            def process_request(self, request):
                if loader: loader(request)
            def process_response(self, request, response):
                if unloader: unloader(request, response)
                return response

        return decorator_from_middleware(OptionLoader)(F)
    return wrapper

#    def inner_decoration(fn):
#        def wrapped(request, *args, **kwargs):
#            if loader: loader(request)
#            response= fn(request, *args, **kwargs)
#            if unloader: unloader(request, response)
#            return response
#        return wraps(fn)(wrapped)
#    return inner_decoration
