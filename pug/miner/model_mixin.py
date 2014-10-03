from pug.nlp.db import representation
from django.db import models

class RepresentationMixin(models.Model):
    """Produce a meaningful string representation of a model with `str(model.objects.all[0])`."""
    __unicode__ = representation

    class Meta:
        abstract = True


class DateMixin(models.Model):
    """Add updated and created fields that auto-populate to create a ORM-level transaction log for auditing (though not a full log, just 2 events)."""
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
