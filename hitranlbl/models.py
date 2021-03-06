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

    def str_rep(self):
        """
        A helper function to return a string representation of the state

        """
        try:
            s_g = '%5d' % self.g
        except TypeError:
            # degeneracy undefined (self.g is None)
            s_g = ' '*5
        try:
            s_E = '%10.4f' % self.energy
        except TypeError:
            # energy undefined (self.energy is None)
            s_E = ' '*10
        return '%4d %s %s %s' % (self.iso.id, s_E,
                                     s_g, self.s_qns)

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
    band = models.CharField(max_length=40, blank=True, null=True)
    
    class Meta:
        app_label = 'hitranlbl'

# Generic parameter model, not tied to any particular Parameter table
class Prm(object):
    def __init__(self, trans_id, val, err, ierr, source_id):
        self.trans_id = trans_id
        self.val = val
        self.err = err
        self.ierr = ierr
        self.source_id = source_id
