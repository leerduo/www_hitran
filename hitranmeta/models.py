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

    source_id = models.IntegerField(null=True, blank=True)

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


#########################
class SourceMethod(models.Model):
    method_name = models.CharField(max_length=32)
    def __unicode__(self):
        return self.method_name
    class Meta:
        app_label = 'hitranmeta'

class SourceType(models.Model):
    source_type = models.CharField(max_length=50)
    def __unicode__(self):
        return self.source_type
    class Meta:
        app_label = 'hitranmeta'

class Source(models.Model):
    # unique ID for this reference
    refID = models.CharField(max_length=100)
    # reference type (e.g. 'article', 'private communication')
    source_type = models.ForeignKey('SourceType')
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
    # method: e.g. 'experimental', 'theory', 'extrapolation', 'guess'
    method = models.ForeignKey('SourceMethod')
    # article number, used instead of page number for e.g. J. Chem. Phys. papers
    article_number = models.CharField(max_length=16, null=True, blank=True)
    # source_list refers to a table giving the one-to-many relationship for a
    # Source note which cites (possibly more than one) sources
    source_list = models.ManyToManyField('Source', symmetrical=False,
                                         null=True, blank=True)
    
    def __unicode__(self):
        if self.source_type.source_type == 'article':
            return '%d: %s: %s, %s' % (self.id, self.refID, self.authors,
                                       self.title)
        elif self.source_type.source_type in ('note', 'private communication'):
            return '%d: %s: %s, %s' % (self.id, self.refID, self.authors,
                                       self.note)
        else:
            return '%d: %s: %s, %s' % (self.id, self.refID, self.authors,
                                       self.title)

    class Meta:
        app_label='hitranmeta'

    def html(self):
        source_type = self.source_type.source_type
        if source_type == 'article':
            return self.html_article()
        if source_type == 'note':
            return self.html_note_full()
        if source_type == 'private communication':
            return self.html_private_communication()
        if source_type == 'proceedings':
            return self.html_proceedings()
        if source_type == 'thesis':
            return self.html_thesis()
        if source_type == 'database':
            return self.html_database()
        if source_type == 'unpublished data':
            return self.html_unpublished_data()
        return 'undefined %s' % source_type

    def html_article(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        if self.title_html:
            s_title = '"%s"' %  self.title_html
        else:
            s_title = '[unknown title]'
        s_journal = self.journal
        if not s_journal:
            s_journal = 'unknown journal'
        if self.volume:
            s_volume = ' <strong>%s</strong>' % self.volume
        else:
            s_volume = ''
        s_pages = self.page_start
        if s_pages:
            if self.page_end:
                s_pages = ', %s-%s' % (s_pages, self.page_end)
        else:
            s_pages = ''
        s_year = ''
        if self.year:
            s_year = ' (%s)' % (str(self.year))

        s = '%s, %s, <em>%s</em>%s%s%s'\
                % (s_authors, s_title, s_journal, s_volume,
                   s_pages, s_year)
        return s

    def html_note(self):
        s_note = self.note_html
        return 'NOTE: %s' % s_note
        
    def html_note_full(self):
        s_note = self.note_html
        s_sublist = []
        for source in self.source_list.all():
            s_sublist.append('<li>%d. %s</li>' % (source.id, source.html()))
        s = '%s\n<ul>\n%s</ul>' % (s_note, '\n'.join(s_sublist))
        return s

    def html_private_communication(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s = '%s%s, private communication%s' % (s_authors, s_note, s_year)
        return s
        
    def html_proceedings(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        # for proceedings, the event details (e.g. conference venue and dates)
        # are stored in note and note_html
        s_event = ''
        if self.note_html:
            s_event = ', %s' % self.note_html
        s = '%s%s%s' % (s_authors, s_title, s_event)
        return s

    def html_thesis(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_institution = self.institution
        if not s_institution:
            s_institution = '[unknown institution]'
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s = '%s%s%s, %s%s' % (s_authors, s_title, s_note, s_institution, s_year)
        return s

    def html_database(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s = '%s%s%s, database' % (s_authors, s_title, s_note)
        return s

    def html_unpublished_data(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s = '%s%s%s, unpublished data%s' % (s_authors, s_title, s_note, s_year)
        return s
