from django.db import models
from django.contrib.sites.models import Site
from picklefield import PickledObjectField
from .managers import OptionManager


class Option(models.Model):

    site = models.ForeignKey(Site, related_name='options')

    key= models.CharField(max_length=255)
    value= PickledObjectField(null=True, default=True)
    autoload=models.BooleanField(default=False)

    updated_at=models.DateTimeField(auto_now=True)
    created_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField(blank=True, null=True)

    # override default manager
    objects = OptionManager()
    all = models.Manager()
    on_site = objects

    class Meta:
        unique_together = ('site', 'key',)



