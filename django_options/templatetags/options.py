from inspect import getargspec
from django.template import Library, base
from .. import get_option

register = Library()

def optional_assignment_tag(func=None, takes_context=None, name=None):
    """
    https://groups.google.com/forum/?fromgroups=#!topic/django-developers/E0XWFrkRMGc
    new template tags type
    """
    def dec(func):
        params, varargs, varkw, defaults = getargspec(func)

        class AssignmentNode(base.TagHelperNode):
            def __init__(self, takes_context, args, kwargs, target_var=None):
                super(AssignmentNode, self).__init__(takes_context, args, kwargs)
                self.target_var = target_var

            def render(self, context):
                resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
                output = func(*resolved_args, **resolved_kwargs)
                if self.target_var is None:
                    return output
                else:
                    context[self.target_var] = output
                return ''

        function_name = (name or
                         getattr(func, '_decorated_function', func).__name__)

        def compile_func(parser, token):
            bits = token.split_contents()[1:]
            if len(bits) < 2 or bits[-2] != 'as':
                target_var = None
            else:
                target_var = bits[-1]
                bits = bits[:-2]
            args, kwargs = base.parse_bits(parser, bits, params,
                varargs, varkw, defaults, takes_context, function_name)
            return AssignmentNode(takes_context, args, kwargs, target_var)

        compile_func.__doc__ = func.__doc__
        register.tag(function_name, compile_func)
        return func
    if func is None:
        # @register.assignment_tag(...)
        return dec
    elif callable(func):
        # @register.assignment_tag
        return dec(func)
    else:
        raise base.TemplateSyntaxError("Invalid arguments provided to assignment_tag")

@optional_assignment_tag(name='option')
def do_get_option( option_name, default=None ):
    """
    retrieve a option value by key
    uses:

        {% option "optionName" default as myvar %}
        {{ myvar }}

    or:
        {% option "optionName" %}
        {% option "optionName" "not found" %}

    """
    return get_option(option_name, default=default )


@register.filter(name='option')
def do_get_option_filter( option_name, default=None ):
    """
    retrieve a option value by key
    uses:

        {{ 'option_name'|option }}
        {{ 'option_name'|option:default }}
        {% if 'option_name'|option:False %} .. {% endif %}
        {% for element in 'option_name'|option:var_with_list %}{{ element }}\n{% endfor %}

    """
    return get_option( option_name, default=default )


@register.filter(name='or_option')
def do_or_option_filter( value, option_name ):
    """
    retrieve a option value by key if value is None
    uses:

        {{ myvalue|or_option:'option_name' }}

    """
    if not value:
        value = get_option(option_name)
    return value

