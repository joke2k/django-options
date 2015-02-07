import copy
from django.contrib.sites.managers import CurrentSiteManager
from django.conf import settings
from django.db import IntegrityError
from .signals import option_value_changed

class OptionManager(CurrentSiteManager):
    """ Option API """

#    all_options = None
#    not_options = {}
#    single_options = {}
#    site_id = None

    def __init__(self, **kwargs):
        self.clear()
        self.site_id = kwargs.pop('site_id',None)
        self.__is_validated = False
        super(OptionManager, self).__init__(**kwargs)

    def get_queryset(self):
        # monkey patch for CurrentSiteManage
        # that allows to change site_id
        if not self.site_id:
            return super(OptionManager, self).get_query_set()
        return super(CurrentSiteManager, self).get_query_set().filter(**{self.__field_name + '__id__exact': self.site_id})

    get_query_set = get_queryset

    def clear(self):
        self.all_options = None
        self.not_options = {}
        self.single_options = {}

    def get_site_id(self):
        return self.site_id or settings.SITE_ID

    def fetch_all_options(self):
        """
        Loads and caches all autoloaded options, if available or all options.
        """
        if self.all_options is None:

            all_options_db = self.get_query_set().filter(autoload=True).values()

            if not any(all_options_db):
                # try to load all
                all_options_db = self.get_query_set().all().values()

            self.all_options = {}

            # store not decoded values
            for opt in all_options_db:
                self.all_options[opt['key']] = opt['value']

        return self.all_options

    def get_option(self, key, default= None):
        """
        Retrieve option value based on name of option.

        If the option does not exist or does not have a value, then the return value
        will be false.

        If the option was serialized then it will be unserialized when it is returned.

        :param key option Name of option to retrieve. Expected to not be SQL-escaped.
        :param default Optional. Default value to return if the option does not exist.
        :return mixed Value set for the option or None if not exists.
        """

        # clean key option
        key = key.strip()
        if not key: return None

        # already misses?
        if key in self.not_options: return default

        self.fetch_all_options()

        if key in self.single_options:
            value = self.single_options[key]

        elif key in self.all_options:
            value = self.get_query_set().model( value=self.all_options[key] ).value
            # to prevent double decoding
            self.single_options[key] = value

        else:
            try:
                opt = self.get_query_set().get( key=key )
                # already deserialized
                value = opt.value
                # remember that
                self.single_options[ key ] = value

            except self.get_query_set().model.DoesNotExist:
                self.not_options[key] = True
                return default

        # maybe deserialize json
        return value


    def update_option(self, key, new_value, **kwargs):
        """
        Update the value of an option that was already added.

        You do not need to serialize values. If the value needs to be serialized, then
        it will be serialized before it is inserted into the database. Remember,
        resources can not be serialized or added as an option.

        If the option does not exist, then the option will be added with the option
        value, but you will not be able to set whether it is autoloaded. If you want
        to set whether an option is autoloaded, then you need to use the add_option().

        :param key string models. Option name. Expected to not be SQL-escaped.
        :param new_value mixed models.Option value. Expected to not be SQL-escaped.
        :return bool False if value was not updated and true if value was updated.
        """

        # clean key option
        key = key.strip()
        if not key: return None

        new_value = copy.deepcopy( new_value )

        old_value = self.get_option( key )

        # If the new and old values are the same, no need to update.
        if new_value == old_value:
            return False

        # if option not exists, he creates as the deal
        if old_value is None:
            return self.add_option( key, new_value, **kwargs )

        # clean for old entries in not_options
        if key in self.not_options:
            del self.not_options[key]

        # update caches if needed
        if key in self.single_options:
            self.single_options[key] = new_value
        if key in self.all_options:
            #self.all_options[key] = new_value
            del self.all_options[key]

        option_value_changed.send(self, old_value=old_value, new_value=new_value, option=key)

        return self.get_query_set().filter(key=key).update(value=new_value) == 1


    def add_option(self, key, value, autoload=True):
        """
        Add a new option.

        You do not need to serialize values. If the value needs to be serialized, then
        it will be serialized before it is inserted into the database. Remember,
        resources can not be serialized or added as an option.

        You can create options without values and then update the values later.
        Existing options will not be updated and checks are performed to ensure that you
        aren't adding a protected system option. Care should be taken to not name
        options the same as the ones which are protected.

        :param key str Name of option to add. Expected to not be SQL-escaped.
        :param value mixed models.Optional. models.Option value, can be anything. Expected to not be SQL-escaped.
        :param autoload bool Optional. Default is enabled. Whether to load the option when system starts up.
        :return bool False if option was not added and true if option was added.
        """

        # clean key option
        key = key.strip()
        if not key: return None

        value = copy.deepcopy( value )

        all_options = self.fetch_all_options()

        # Make sure the option doesn't already exist.
        if key in all_options:
            return False
        # check the 'not_options' cache before we ask for a db query
        if key not in self.not_options:
            if not self.get_option( key ) is None:
                return False

        try:
            option = self.get_query_set().create(key=key, site_id=self.get_site_id(), value=value, autoload=autoload)
        except IntegrityError:
            return False

#        option, created = self.get_query_set().get_or_create(key=key, site_id= self.get_site_id(), defaults={
#            'value': value,
#            'autoload': autoload,
#        })
#        if not created:
#            return False

        if key in self.not_options:
            del self.not_options[key]

        if autoload:
            all_options[key] = option.value
        else:
            self.single_options[key] = option.value

        option_value_changed.send(self, old_value=None, new_value=option.value, option=option.key)

        return True


    def delete_option(self, key):
        """
        Removes option by name. Prevents removal of protected options.
        """

        # clean key option
        key = key.strip()
        if not key: return None

        OptionQuery = self.get_query_set()

        try:
            opt = OptionQuery.get( key=key )

            # clean caches
            if opt.autoload and self.all_options and key in self.all_options:
                del self.all_options[key]
            if key in self.single_options:
                del self.single_options[key]

            opt.delete()

        except OptionQuery.model().DoesNotExist:
            return False

        option_value_changed.send(self, old_value=opt.value, new_value=None, option=opt.key)

        return True

