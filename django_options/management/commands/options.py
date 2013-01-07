from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.utils.encoding import force_unicode
#from json_field.fields import JSONDecoder
from ...api import *
from ...utils.prettytable import PrettyTable

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-l','--list', action='store_true', dest='list', default=False, help='Show list of options'),
        make_option('-p','--page', action='store', dest='page', type=int, default=1, help='Page of list of options'),
        make_option('--per-page', action='store', dest='per-page', type=int, default=25, help='Option shown in a Page of list of options'),
        make_option('-o','--order', action='store', dest='order', default='pk', help='Order by field. with "-" is reverse'),

        make_option('-a','--add', action='store', dest='value_to_add', default=None, help='Add an option'),
        make_option('-u','--update', action='store', dest='value_to_update', default=None, help='Set an option'),
        make_option('--execute', action='store_true', dest='execute', default=False, help='Execute python function to generate value to add or update'),
        make_option('--eval', action='store_true', dest='eval', default=False, help='Evaluate value to add or update'),
        make_option('--json', action='store_true', dest='json', default=False, help='JSON value provided to add or update'),
        make_option('-d','--delete', action='store_true', dest='delete', default=False, help='Delete option with key provided'),
    )

    def handle(self, *args, **options):

        if not len(args) or options['list']:

            page = options.get('page')
            per_page = options.get('per-page')
            ordered_by = [x.strip() for x in options.get('order').split(',')]
            self.show_options_list( Option.objects.all().order_by(*ordered_by), page, per_page )
            return

        option_key = args[0].strip()

        if options['value_to_add']:
            value, action = self.read_value(options['value_to_add'], *args[1:], **options)
            if not add_option( option_key, value ):
                raise CommandError("Cannot add '%s' option, already exists" % option_key)
            self.stdout.write('Add %s: %s %s' % ( option_key, value, action) )
        elif options['value_to_update']:
            value, action = self.read_value(options['value_to_update'], *args[1:], **options)
            if not update_option( option_key, value ):
                raise CommandError("Cannot update '%s' option with '%s'" % (option_key,value))
            self.stdout.write('Update %s: %s %s' % ( option_key, value, action ) )
        elif options['delete']:
            if len(args) > 1: raise CommandError('Too much arguments: %s' % args)
            if not delete_option( option_key ):
                raise CommandError("Cannot delete '%s' option" % option_key)
            self.stdout.write('Delete %s' % option_key )
        else:
            self.show_option_value( option_key )

    def show_options_list(self, list, page=1, per_page=25):

        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(list, per_page) # Show 25 options per page

        try:
            options = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            options = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            options = paginator.page(paginator.num_pages)

        x = PrettyTable(["Site", "Option", "Last change", "Created at", "Value", "Autoload"])
        x.align["Option"] = "l"
        x.align["Value"] = "l"

        for opt in options:
            x.add_row([opt.site.pk, opt.key, opt.updated_at.strftime("%Y-%m-%d %H:%M:%S"), opt.created_at.strftime("%Y-%m-%d %H:%M:%S"), force_unicode(opt.value), opt.autoload])

        self.stdout.write(u"\n%s" % x)

        if page and paginator.num_pages > 1:
            self.stdout.write(u'\nPage %s of %s' % (page,paginator.num_pages))

    def show_option_value(self, option_key):
        opt = Option.objects.get(key=option_key)

        self.show_options_list([opt])

    #        self.stdout.write('\n# {key}\t{value}\t\t{updated_at}\t{created_at}'.format(
    #            key= opt.key, value= opt.get_value_json(), updated_at=opt.updated_at.strftime("%Y-%m-%d %H:%M:%S"), created_at=opt.created_at.strftime("%Y-%m-%d %H:%M:%S")
    #        ))

    def read_value(self, value, *args, **options):

        action = ''

        if options['eval']:
            action = 'evaluated from "%s"' % value
            value = eval(value,{},{})
        elif options['execute']:
            from importlib import import_module
            action = 'executed from "%s"' % value
            module_name = value.split('.')
            func_name = module_name.pop()
            module_name = ".".join(module_name)
            try:
                mod = import_module( module_name )
                if func_name not in dir(mod):
                    raise CommandError('Cannot find function "%s" in module "%s"' % (func_name,module_name))
            except ImportError:
                raise CommandError('Cannot find module "%s"' % module_name)

            value = getattr(mod, func_name)(*args)
        elif options['json']:
            import json
#            value = json.loads( value, cls=JSONDecoder)
            action = 'json > %s' % value
            value = json.loads( value )

        return value, action
