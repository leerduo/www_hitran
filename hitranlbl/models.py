from django.db import models
import datetime
from hitranmeta.models import Iso, Case

class Qns(models.Model):
    case = models.ForeignKey('hitranmeta.case')
    state = models.ForeignKey('State')
    qn_name = models.CharField(max_length=20)
    qn_val = models.CharField(max_length=10)
    qn_attr = models.CharField(max_length=50, blank=True, null=True)
    xml = models.CharField(max_length=500)
    
    class Meta:
        app_label = 'hitranlbl'

class State(models.Model):
    iso = models.ForeignKey('hitranmeta.iso')
    energy = models.FloatField(blank=True, null=True)
    g = models.IntegerField(blank=True, null=True)
    nucspin_label = models.CharField(max_length=1, blank=True, null=True)
    s_qns = models.CharField(max_length=500, blank=True, null=True)
    qns_xml = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'hitranlbl'

class Trans(models.Model):
    iso = models.ForeignKey('hitranmeta.iso')
    statep = models.ForeignKey('State', related_name='trans_upper_set')
    statepp = models.ForeignKey('State', related_name='trans_lower_set')
    nu = models.FloatField()
    Sw = models.FloatField()
    A = models.FloatField()
    multipole = models.CharField(max_length=2, blank=True, null=True)
    Elower = models.FloatField(blank=True, null=True)
    gp = models.IntegerField(blank=True, null=True)
    gpp = models.IntegerField(blank=True, null=True)
    valid_from = models.DateField()
    # the default is for this data 'never' to expire:
    valid_to = models.DateField(default=datetime.date(
            year=3000, month=1, day=1))
    par_line = models.CharField(max_length=160, blank=True, null=True)
    
    class Meta:
        app_label = 'hitranlbl'

class Prm(models.Model):
    trans = models.ForeignKey('Trans')
    name = models.CharField(max_length=20)
    val = models.FloatField()
    err = models.FloatField(blank=True, null=True)
    ref = models.ForeignKey('hitranmeta.ref', blank=True, null=True)
    source = models.ForeignKey('hitranmeta.source', blank=True, null=True)
    method = models.IntegerField(blank=True, null=True)
    
    class Meta:
        app_label = 'hitranlbl'
