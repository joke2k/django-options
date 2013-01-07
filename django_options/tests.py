
#from django.utils.unittest import TestCase

from django.test import TestCase
from .models import Option

class OptionManagerTestCase(TestCase):

    def setUp(self):
        self.o = Option.objects
        self.o.clear()
        # delete all from all sites
        Option.all.all().delete()

    def test_adding_options(self):
        with self.assertNumQueries(2):
            self.assertEqual( self.o.fetch_all_options(), {} )
        with self.assertNumQueries(0):
            self.assertEqual( self.o.fetch_all_options(), {} )
        with self.assertNumQueries(2):
            self.assertTrue( self.o.add_option('key','value') )

    def test_value_type_consistency(self):
    #        from datetime import datetime
    #        value_types = [0,1,None,False,[],{},[1,2,3],{'a':1,'b':2},datetime(2012,11,1,23,30,15),{'float':2.15,'subdict':{'date': datetime(2012,11,1,23,30,15)}}]
        value_types = [0,1,None,False,[],{},[1,2,3],{'a':1,'b':2}]

        with self.assertNumQueries( len(value_types)*2 + 2 ) :
            # add options
            for i, obj in enumerate(value_types):
                self.assertTrue( self.o.add_option("key_%s" % i, obj) )

        self.o.clear()
        with self.assertNumQueries( 1 ) :
            # add options
            for i, obj in enumerate(value_types):
                self.assertEqual(obj, self.o.get_option("key_%s" % i,'##NOTFOUND##'))


    def test_not_existing_option(self):
        """Options that not exists"""
        self.assertIsNone(self.o.get_option('foo'))
        self.assertEqual(self.o.get_option('foo','bar'), 'bar')
        self.assertIsNone(self.o.get_option('foo'))
        self.assertIn('foo',self.o.not_options)
        self.assertNotIn('foo',self.o.all_options)
        self.assertNotIn('foo',self.o.single_options)

    def test_option_creation(self):
        """Testing add_option and update_option to manage options"""
        self.assertTrue(self.o.add_option('foo','bar'))
        # cannot add an option with same key
        self.assertFalse(self.o.add_option('foo','brbr'))
        # but we can update
        self.assertTrue(self.o.update_option('foo','rab'))
        # only changing the value
        self.assertFalse(self.o.update_option('foo','rab'))
        # even if this option not exists
        self.assertTrue(self.o.update_option('oof','rab', autoload=False))

        # check values
        self.assertEqual(self.o.get_option('foo'),'rab')
        self.assertEqual(self.o.get_option('oof'),'rab')

        # check caches
        self.assertNotIn('foo',self.o.not_options)
        self.assertNotIn('foo',self.o.all_options)
        self.assertIn('foo',self.o.single_options)
        self.assertNotIn('oof',self.o.not_options)
        self.assertNotIn('oof',self.o.all_options)
        self.assertIn('oof',self.o.single_options)

    def test_option_deleting(self):
        """Testing delete_option"""
        self.assertTrue(self.o.add_option('foo','bar'))
        self.assertTrue(self.o.delete_option('foo'))
        # already deleted or not existent option
        self.assertFalse(self.o.delete_option('foo'))

    def test_autoloading(self):
        """One option can be autoloaded with first fetch_all_options"""
        self.assertTrue( self.o.add_option('one', 'yes', autoload=True) )
        self.assertTrue( self.o.add_option('two', 'yes', autoload=True) )
        self.assertTrue( self.o.add_option('three', 'yes', autoload=False) )

        self.assertIn( 'one', self.o.all_options )
        self.assertIn( 'two', self.o.all_options )
        self.assertNotIn( 'three', self.o.all_options )
        # but it's cached in default group
        self.assertIn( 'three', self.o.single_options )

        self.o.clear()
        # reload all
        all_options = self.o.fetch_all_options()
        self.assertIn( 'one', all_options )
        self.assertIn( 'two', all_options )
        self.assertNotIn( 'three', all_options )

    def test_option_cache(self):
        """ Testing the integration between cache and options"""
        with self.assertNumQueries(2):
            # two because there's not autoloaded options
            # then fetch all
            self.o.fetch_all_options()

        with self.assertNumQueries(0):
            # again, we have nothing..
            self.o.fetch_all_options()

        with self.assertNumQueries(2):
            # add an autoloaded option
            self.assertTrue( self.o.add_option('cache','on') )

        # clearing for repeat with new autoloads
        self.o.clear()

        with self.assertNumQueries(1):
            # this time we found one autoload
            self.o.fetch_all_options()

        with self.assertNumQueries(0):
            # not queries
            self.assertIsNotNone( self.o.get_option('cache') )
            # no query, it is cached on not_options
            self.assertEqual( self.o.get_option('cache') , 'on')
            # cannot update with same value
            self.assertFalse( self.o.update_option('cache', 'on'))

        # clearing for repeat with new autoloads
        Option.all.all().delete()
        self.o.clear()
        self.assertEqual(Option.all.count(), 0)

        with self.assertNumQueries(     4     ):
            self.assertTrue( self.o.add_option('key', 'value') )

        # clearing for repeat with new autoloads
        Option.all.all().delete()
        self.o.clear()
        self.assertEqual(Option.all.count(), 0)
        k = 100
        #                               DOUBLE (check if exists)
        with self.assertNumQueries(     (k*2) +2     ):
            for i in range(0,k):
                self.assertTrue( self.o.add_option('key_%s' % i, k) )

        # clearing for repeat with new autoloads
        self.o.clear()
        #                             JUST (autoloads)
        with self.assertNumQueries(     1     ):
            self.assertIsNone( self.o.all_options)
            self.assertEquals( len(self.o.fetch_all_options()), k )
            for i in range(0,k):
                self.assertIn( 'key_%s' % i, self.o.all_options )
                self.assertEqual( self.o.get_option('key_%s' % i),  k )

        self.assertEqual( len(self.o.all_options) , k )


    def test_pickle_do_only_one_conversion_for_key(self):
        # define a decorator for encoder and decoder functions
        counters = {
            'dbsafe_decode': 0,
            'dbsafe_encode': 0,
            '_dbsafe_decode': 0,
            '_dbsafe_encode': 0,
        }
        def counter(F):
            def wrapper(*args, **kwargs):
                try:
                    value = F(*args, **kwargs)
                    counters[F.__name__] += 1
                except Exception, e:
                    counters['_' + F.__name__] += 1
                    raise e
                return value
            return wrapper

        # prepare environment for test
        from picklefield import fields
        old_decode = fields.dbsafe_decode
        fields.dbsafe_decode = counter(fields.dbsafe_decode)
        old_encode = fields.dbsafe_encode
        fields.dbsafe_encode = counter(fields.dbsafe_encode)

        self.assertTrue(self.o.add_option('foo','ciao'))
        self.assertEqual( 1, Option.all.count())
        # do not decode python string 'ciao'
        self.assertEqual( 0, counters['dbsafe_decode'] )
        # one encoding for save
        self.assertEqual(  1, counters['dbsafe_encode'] )

        self.assertEqual('ciao', self.o.get_option('foo') )
        # no decoding because manager caches already loaded (or inserted/updated) options
        self.assertEqual( 0, counters['dbsafe_decode'] )
        # no other saves
        self.assertEqual(  1, counters['dbsafe_encode'] )

        self.assertFalse(self.o.add_option('foo','ciao'))
        self.assertFalse(self.o.update_option('foo','ciao'))
        self.assertEqual('ciao', self.o.get_option('foo') )
        # neither
        self.assertEqual( 0, counters['dbsafe_decode'] )
        # neither
        self.assertEqual(  1, counters['dbsafe_encode'] )

        self.assertTrue(self.o.add_option('bar','oaic'))
        # neither
        self.assertEqual( 0, counters['dbsafe_decode'] )
        # the second here!
        self.assertEqual(  2, counters['dbsafe_encode'] )

        self.o.clear()
        self.assertEqual('ciao', self.o.get_option('foo') )
        self.assertEqual('ciao', self.o.get_option('foo') )
        self.assertEqual('ciao', self.o.get_option('foo') )
        self.assertEqual('oaic', self.o.get_option('bar') )
        self.assertEqual('oaic', self.o.get_option('bar') )
        self.assertEqual('oaic', self.o.get_option('bar') )
        self.assertEqual('oaic', self.o.get_option('bar') )
        # the others 2
        self.assertEqual( 2, counters['dbsafe_decode'] )
        # neither
        self.assertEqual(  2, counters['dbsafe_encode'] )

        # restore environment
        fields.dbsafe_decode = old_decode
        fields.dbsafe_encode = old_encode

    def test_api(self):
        import django_options.api as API

        self.assertEqual(API.get_option('foo'), None)
        self.assertFalse(API.has_option('foo'))
        self.assertTrue(API.add_option('foo','foo'))
        self.assertEqual(API.get_option('foo'), 'foo')
        self.assertTrue(API.has_option('foo'))

        self.assertTrue(API.update_option('foo','bar'))
        self.assertEqual(API.get_option('foo'), 'bar')
        self.assertTrue(API.has_option('foo'))

        # equality and disequality tests
        self.assertFalse(API.option_is('foo','foo'))
        self.assertTrue(API.option_is('foo','bar'))

        self.assertTrue(API.option_not_is('foo','foo'))
        self.assertFalse(API.option_not_is('foo','bar'))

        #test symbolic link option
        self.assertTrue(API.add_option('key','link'))
        self.assertTrue(API.add_option('link',1))
        self.assertEqual(API.symbolic_option('key'), 1)









