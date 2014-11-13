from django.db import models

class Day(models.Model):
    day = models.IntegerField(help_text="Trading days since Jan 1, 1970", null=True, blank=True)
    close = models.FloatField(null=True, default=None)
    actual_close = models.FloatField(null=True, default=None, blank=True)
    volume = models.FloatField(null=True, default=None, blank=True)
    date = models.DateField(null=False)
    high = models.FloatField(null=True, default=None, blank=True)
    low = models.FloatField(null=True, default=None, blank=True)


