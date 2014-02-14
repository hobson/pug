from pug.nlp.db import representation

class RepresentationMixin(object):
    """Produce a meaningful string representation of a model with `str(model.objects.all[0])`."""
    __unicode__ = representation
