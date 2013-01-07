from .models import Option

def get_option(key, default=None): return Option.objects.get_option(key,default)
def add_option(key, value, autoload=True): return Option.objects.add_option(key,value,autoload=autoload)
def update_option(key, value, autoload=True): return Option.objects.update_option(key,value,autoload=autoload)
def delete_option(key): return Option.objects.delete_option(key)
def option_cache_reset(): Option.objects.clear()

# advanced api, not included in OptionManager and maybe experimental
def option_is(key, expected_value): return get_option(key) == expected_value
def option_not_is(key, expected_value): return get_option(key) != expected_value
def has_option(key): return option_not_is(key, None)
def symbolic_option(key, default=None):
    """
    update_option('foo','bar')
    update_option('bar',1)
    symbolic_option('foo')
    > 1
    """
    link_key = get_option(key)
    if link_key is None: return default
    if not isinstance(link_key,basestring):
        raise AttributeError('Invalid link_key type "%s" for symbolic_option' % type(link_key))
    return get_option(link_key, default)
