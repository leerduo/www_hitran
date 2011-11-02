from django.db import models
import datetime
from hitranmeta.models import Molecule

class Xsc(models.Model):
    molecule = models.ForeignKey('hitranmeta.molecule')
    numin = models.FloatField()
    numax = models.FloatField()
    n = models.IntegerField()
    T = models.FloatField()
    p = models.FloatField()
    sigmax = models.FloatField()
    res = models.FloatField(blank=True, null=True)
    res_units = models.CharField(max_length=10) # cm-1 or mA for milliAngstroms
    broadener = models.CharField(max_length=10, blank=True, null=True)
    ref = models.ForeignKey('hitranmeta.ref', blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    valid_from = models.DateField()
    # the default is for this data 'never' to expire:
    valid_to = models.DateField(default=datetime.date(
            year=3000, month=1, day=1))
    filename = models.CharField(max_length=100)
    class Meta:
        app_label = 'hitranxsc'

    @classmethod
    def parse_meta(self, molec_id, line):
        """
        Parse the meta data for this absorption cross section from its
        header line.

        """

        stripped_line = line.strip()
        if not stripped_line:
            return None
        xsc = Xsc()
        xsc.molecule = Molecule.objects.filter(pk=molec_id).get()

        try:
            ordinary_formula = line[:20]
            xsc.numin = float(line[20:30])
            xsc.numax = float(line[30:40])
            xsc.n = int(line[40:47])
            xsc.T = float(line[47:54])
            xsc.p = float(line[54:60])
            xsc.sigmax = float(line[60:70])
            xsc.res = float(line[70:75])
            xsc.res_units = 'cm-1'      # XXX IR cross sections only, for now
            common_name = line[75:90]
            # characters 90-94 are 'not currently used'
            xsc.broadener = line[94:97]
            ref = float(line[97:100])
            return xsc

        except Exception, e:
            print 'parse error in parse_meta'
            print e
            print 'The bad line was:'
            print line
            raise       # for debugging

 
