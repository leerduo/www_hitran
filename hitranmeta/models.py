from django.db import models
import datetime

class Molecule(models.Model):
    molecID = models.IntegerField(primary_key=True, unique=True)
    molecID_str = models.CharField(max_length=40)
    InChI = models.CharField(max_length=200, unique=True)
    InChIKey = models.CharField(max_length=27, unique=True)
    # canonical stoichiometric formula with atoms in increasing order of
    # atomic mass:
    stoichiometric_formula = models.CharField(max_length=40)
    # ordinary formula for display and search:
    ordinary_formula = models.CharField(max_length=40)
    ordinary_formula_html = models.CharField(max_length=200)
    # the single most common name used to refer to this species:
    common_name = models.CharField(max_length=100, null=True, blank=True)
    # CML representation of the species, with no isotope information
    cml = models.TextField(null=True, blank=True)
    class Meta:
        app_label='hitranmeta'

class MoleculeName(models.Model):
    name = models.CharField(max_length=100)
    molecule = models.ForeignKey('Molecule')
    class Meta:
        app_label='hitranmeta'

class Iso(models.Model):
    isoID = models.IntegerField()
    isoID_str = models.CharField(max_length=50)
    InChI_explicit = models.CharField(max_length=200, null=True, blank=True,
                                      unique=True)
    InChIKey_explicit = models.CharField(max_length=27, null=True, blank=True,
                                         unique=True)
    InChI = models.CharField(max_length=200, unique=True)
    InChIKey = models.CharField(max_length=27, unique=True)
    molecule = models.ForeignKey('Molecule')
    iso_name = models.CharField(max_length=100)
    iso_name_html = models.CharField(max_length=500)
    abundance = models.FloatField(null=True, blank=True)
    afgl_code = models.CharField(max_length=10, null=True, blank=True)
    # CML representation of the species, with all isotopeNumbers
    # specified explicitly:
    cml_explicit = models.TextField(null=True, blank=True)
    # CML representation of the species with only the essential (ie
    # not maximum abundance, apart from Br) isotopeNumbers specified:
    cml = models.TextField(null=True, blank=True)
    case = models.ForeignKey('Case', null=True, blank=True)
    class Meta:
        app_label='hitranmeta'

class Case(models.Model):
    case_prefix = models.CharField(max_length=10, unique=True)
    case_description = models.CharField(max_length=50)
    class Meta:
        app_label='hitranmeta'

class Ref(models.Model):
    # unique ID for this reference
    refID = models.CharField(max_length=100)
    # reference type (e.g. 'article', 'private communication')
    ref_type = models.CharField(max_length=50, )
    # a list of the authors' names in a string as:
    # 'A.N. Other, B.-C. Person Jr., Ch. Someone-Someone, N.M.L. Haw Haw'
    authors = models.TextField(null=True, blank=True)
    # the article, book, or thesis title
    title = models.TextField(null=True, blank=True)
    # the title as HTML
    title_html = models.TextField(null=True, blank=True)
    # the journal name
    journal = models.CharField(max_length=500, null=True, blank=True)
    # the volume (which may be a string)
    volume = models.CharField(max_length=10, null=True, blank=True)
    # the first page (which may be a string e.g. 'L123')
    page_start = models.CharField(max_length=10, null=True, blank=True)
    # the last page
    page_end = models.CharField(max_length=10, null=True, blank=True)
    # the year of publication, creation, or communication
    year = models.IntegerField(null=True, blank=True)
    # the institution name, if relevant and available
    institution = models.CharField(max_length=500, null=True, blank=True)
    # a note, perhaps containing cross-references of ref_id inside
    # square brackets
    note = models.TextField(null=True, blank=True)
    # the note as HTML
    note_html = models.TextField(null=True, blank=True)
    # the Digital Object Identifier, if available
    doi = models.CharField(max_length=100, null=True, blank=True)
    # a string of HTML to be output on websites citing this reference
    cited_as_html = models.TextField()
    # a URL to the source, if available
    url = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.refID

    class Meta:
        app_label='hitranmeta'

class PartitionFunction(models.Model):
    # the isotopologue that this partition function belongs to
    iso = models.ForeignKey('Iso')
    # the minimum and maximum temperatures for which Q is given
    Tmin = models.FloatField()
    Tmax = models.FloatField()
    # the temperature grid spacing
    dT = models.FloatField()
    # the number of points in the partition function table
    n = models.IntegerField()
    valid_from = models.DateField()
    # the default is for this data 'never' to expire:
    valid_to = models.DateField(default=datetime.date(
            year=3000, month=1, day=1))
    filename = models.CharField(max_length=100)
    class Meta:
        app_label='hitranmeta'

class OutputField(models.Model):
    # parameter name as a valid Python attribute name
    name = models.CharField(max_length=20)
    # parameter name in HTML format
    name_html = models.CharField(max_length=100)
    # Python/C format string
    cfmt = models.CharField(max_length=10)
    # FORTRAN format string
    ffmt = models.CharField(max_length=10)
    # text description of parameter
    desc = models.TextField()
    # HTML description of parameter
    desc_html = models.TextField()
    # the default string to output if the parameter doesn't evaluate
    default = models.CharField(max_length=50)
    # Python casting method, 'int', 'float', 'str', etc.
    prm_type = models.CharField(max_length=20)
    # evaluation string for output after query
    eval_str = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label='hitranmeta'

class OutputCollection(models.Model):
    # collection name
    name = models.CharField(max_length=50)
    output_field = models.ManyToManyField(OutputField)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label='hitranmeta'
    
