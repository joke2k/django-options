from django.core.exceptions import ImproperlyConfigured
from .const import SEPARATOR

class AdminElement(object):
    code = ''
    title = ''
    description = ''

    @classmethod
    def get_code(cls):
        if not cls.code:
            raise ImproperlyConfigured(
                "AdminElement requires either a definition of "
                "'code' or an implementation of 'get_code()'")
        return cls.code

    @classmethod
    def nested_classes_in(cls, class_type):
        classes = []
        for nested in dir(class_type):
            if nested.startswith('_'): continue
            elif nested == 'parent': continue # avoid recursion
            elif not isinstance(getattr(class_type,nested), type): continue
            elif not issubclass(getattr(class_type,nested), cls): continue
            classes.append( getattr(class_type,nested) )
        return classes


class HierarchicalClass(AdminElement):

    parent = None

    @classmethod
    def root(cls):
        if cls.is_root(): return cls
        return cls.parent.root()

    @classmethod
    def has_parent(cls):
        return hasattr(cls,'parent') and cls.parent

    @classmethod
    def is_root(cls): return not cls.has_parent()

    @classmethod
    def parents(cls):
        if not cls.has_parent():
            return []
        return [cls.parent] + cls.parent.parents()

    @classmethod
    def addChild(cls, page):
        if not hasattr(cls, 'children'):
            cls.children = []
        cls.children.append(page)

    @classmethod
    def getChild(cls, code):
        if not hasattr(cls, 'children'):
            return None
        for child in getattr(cls,'children', []):
            child_code = child.get_code()
            if child_code == code:
                return child
            elif code.startswith( child_code + SEPARATOR ):
                return child.getChild( code )
        return None

    @classmethod
    def get_code(cls, separator=SEPARATOR):
        code = super(HierarchicalClass, cls).get_code()
        if not cls.parent: return code
        return cls.parent.get_code(separator) + separator + code


