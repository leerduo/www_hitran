from django.db import models
import datetime
from hitranmeta.models import Molecule

class CollisionPair(models.Model):
    molecule1 = models.ForeignKey('hitranmeta.molecule',
                                  related_name='cia_cp_molecule1_set')
    molecule2 = models.ForeignKey('hitranmeta.molecule',
                                  related_name='cia_cp_molecule2_set')
    #    self.pair_name = '%s-%s'\
    #        % (molecule1.ordinary_formula, molecule2.ordinary_formula)
    #    self.pair_name_html = '%s-%s'\
   #        % (molecule1.ordinary_formula_html,molecule2.ordinary_formula_html)
    #   self.pairIDs_str = '%d-%d' % (molecule1.molecID, molecule2.molecID)
    class Meta:
        db_table = 'hitrancia_collision_pair'
        app_label = 'hitrancia'

    def pair_name(self):
        return '%s-%s' % (self.molecule1.ordinary_formula,
                          self.molecule2.ordinary_formula)
    def pair_name_html(self):
        return '%s-%s' % (self.molecule1.ordinary_formula_html,
                          self.molecule2.ordinary_formula_html)

class CIA(models.Model):
    T = models.FloatField()
    numin = models.FloatField()
    numax = models.FloatField()
    # if dnu is a single value, the wavenumber grid is regularly-spaced;
    # if it is NULL, then pull the nu grid from a file
    dnu = models.FloatField(blank=True, null=True)
    alphamax = models.FloatField()
    # if error is a single value, it applies to all alpha in this series;
    # if it is NULL, then pull the errors from a file
    error = models.FloatField(blank=True, null=True)
    has_error_file = models.BooleanField()
    n = models.IntegerField()
    res = models.FloatField(blank=True, null=True)
    molecule1 = models.ForeignKey('hitranmeta.molecule',
                                  related_name='cia_molecule1_set')
    molecule2 = models.ForeignKey('hitranmeta.molecule',
                                  related_name='cia_molecule2_set')
    collision_pair = models.ForeignKey(CollisionPair)
    #ref = models.ForeignKey('hitranmeta.ref', blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    valid_from = models.DateField()
    # the default is for this data 'never' to expire:
    valid_to = models.DateField(default=datetime.date(
            year=3000, month=1, day=1))
    filename = models.CharField(max_length=100)
    class Meta:
        app_label = 'hitrancia'

    @classmethod
    def parse_meta(self, line):
        """
        Parse the meta data for this collision-induced absorption cross
        section from its header line.

        """

        if not line:
            return None
        cia = CIA()
        try:
            species1, species2 = [x.strip() for x in line[:20].split('-')]
            cia.molecule1 = Molecule.objects.filter(ordinary_formula=species1)\
                            .get()
            cia.molecule2 = Molecule.objects.filter(ordinary_formula=species2)\
                            .get()
            cia.numin = float(line[20:30])
            cia.numax = float(line[30:40])
            cia.n = int(line[40:47])
            cia.T = float(line[47:54])
            cia.alphamax = float(line[54:64])
            cia.res = float(line[64:70])
            cia.desc = line[70:97].strip()
            ref = int(line[97:])
            return cia
        
        except Exception, e:
            print 'parse error in parse_meta'
            print e
            print 'The bad line was:'
            print line
            raise       # for debugging
