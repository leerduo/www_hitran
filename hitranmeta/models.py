from django.db import models
import re
import datetime

ref_patt = 'Ref\.\s\[(\d+)\]'
def i2chr(i):
    """
    Map i=(0,1,2,...,25) to 'a','b','c',...,'z';
    return '?' if 0>i or i>25

    """
    if i<0 or i>25:
        return '?'
    return chr(i+97)


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
    def __unicode__(self):
        return self.ordinary_formula

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
    def __unicode__(self):
        return self.iso_name

    class Meta:
        app_label='hitranmeta'

class NucSpins(models.Model):
    iso = models.ForeignKey('Iso')
    atom_label = models.CharField(max_length=3)
    I = models.FloatField()
    def __unicode__(self):
        return u'%s: I(%s)=%.1f' % (self.iso.iso_name, self.atom_label, self.I)

    class Meta:
        app_label='hitranmeta'

class Case(models.Model):
    case_prefix = models.CharField(max_length=10, unique=True)
    case_description = models.CharField(max_length=50)
    def __unicode__(self):
        return '%d: %s' % (self.id, self.case_prefix)

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
    output_fields = models.ManyToManyField(OutputField,
                                           through='OutputFieldOrder')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label='hitranmeta'

class OutputFieldOrder(models.Model):
    output_field = models.ForeignKey(OutputField)
    output_collection = models.ForeignKey(OutputCollection)
    position = models.IntegerField()

    def __unicode__(self):
        return '%s: %d. %s' % (self.output_collection.name, self.position,
                               self.output_field.name)

    class Meta:
        app_label='hitranmeta'
        ordering = ['position']

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

class RefsMap(models.Model):
    # RefsMap maps the refID in the HITRAN notation, <molec_name>-<prm>-##
    # to source_id the primary key of the Source table
    refID = models.CharField(max_length=100)
    source_id = models.IntegerField(null=False, blank=False)
    def __unicode__(self):
        return '%s -> %s' % (self.refID, self.source_id)

    class Meta:
        db_table = 'hitranmeta_refs_map'
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

    def html(self, sublist=False, s_refid=None):
        if s_refid is None:
            s_refid = str(self.id)
        source_type = self.source_type.source_type
        if source_type == 'article':
            return '%s. %s' % (s_refid, self.html_article())
        if source_type == 'note':
            return '%s. %s' % (s_refid, self.html_note(sublist))
        if source_type == 'private communication':
            return '%s. %s' % (s_refid, self.html_private_communication())
        if source_type == 'proceedings':
            return '%s. %s' % (s_refid, self.html_proceedings())
        if source_type == 'thesis':
            return '%s. %s' % (s_refid, self.html_thesis())
        if source_type == 'database':
            return '%s. %s' % (s_refid, self.html_database())
        if source_type == 'unpublished data':
            return '%s. %s' % (s_refid, self.html_unpublished_data())
        if source_type == 'report':
            return '%s. %s' % (s_refid, self.html_report())
        if source_type == 'in preparation':
            return '%s. %s' % (s_refid, self.html_in_preparation())
        if source_type == 'book':
            return '%s. %s' % (s_refid, self.html_book())
        return '%s. undefined %s' % (s_refid, source_type)

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

        s = '%s, %s, <em>%s</em>%s%s%s.'\
                % (s_authors, s_title, s_journal, s_volume,
                   s_pages, s_year)
        return s

    def html_note(self, sublist, relabel=True):
        if not sublist:
            # no additional sources relate to this note: just output its html
            return '%s.' % self.note_html

        s_note = '%s.' % self.note_html
        if relabel:
            # find all the strings 'Ref. [xxx]' in the note html
            s_allrefids = re.findall(ref_patt, self.note_html)
            # remove duplicates from s_allrefids, whilst preserving order
            seen = set(); seen_add = seen.add
            s_refids = [x for x in s_allrefids if x not in seen
                                                    and not seen_add(x)]
            # now replace the database id of each source reference with
            # a local id, formed as '<id>a', '<id>b', etc. where <id> is
            # the database id of this note
            for i,s_refid in enumerate(s_refids):
                s_note = s_note.replace('Ref. [%s]' % s_refid,
                                    'Ref. [%d%s]' % (self.id, i2chr(i)))
        s_sublist = []
        if relabel:
            for s_refid in s_refids:
                source = self.source_list.get(pk=int(s_refid))
                s_refid = '%d%s' % (self.id,
                                  i2chr(s_refids.index(str(source.id))))
                s_sublist.append('<li>%s</li>' % source.html(sublist=False,
                                                             s_refid=s_refid))
        else:
            for source in self.source_list.all():
                s_refid = str(source.id)
                # NB we don't want the sublist entries to have sublists!
                s_sublist.append('<li>%s</li>' % source.html(sublist=False,
                                                             s_refid=s_refid))
        s = '%s\n<ul>\n%s</ul>' % (s_note, '\n'.join(s_sublist))
        return s

    def html_private_communication(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_institution = ''
        if self.institution:
            s_institution = ', %s' % self.institution
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s_pc = '%s%s%s, private communication%s.' % (s_authors,
                                        s_institution, s_note, s_year)
        s_sublist = []
        for source in self.source_list.all():
            # we don't want the sublist entries to have sublists!
            s_sublist.append('<li>%s</li>' % source.html(sublist=False))
        s = '%s\n<ul>\n%s</ul>' % (s_pc, '\n'.join(s_sublist))
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
        s = '%s%s%s.' % (s_authors, s_title, s_event)
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
        s = '%s%s%s, thesis, %s%s.' % (s_authors, s_title, s_note,
                                       s_institution, s_year)
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
        s_url = ''
        if self.url:
            s_url = '<br/>url: <a href="%s">%s</a>' % (self.url, self.url)
        s = '%s%s%s, database.%s' % (s_authors, s_title, s_note, s_url)
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
        s = '%s%s%s, unpublished data%s.' % (s_authors, s_title, s_note,
                                             s_year)
        return s

    def html_report(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_institution = ''
        if self.institution:
            s_institution = ', %s' % self.institution
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s = '%s%s%s%s%s.' % (s_authors, s_title, s_note, s_institution, s_year)
        return s

    def html_in_preparation(self):
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
        s = '%s%s%s%s, in preparation.' % (s_authors, s_title, s_note, s_year)
        return s

    def html_book(self):
        s_authors = self.authors
        if not s_authors:
            s_authors = 'unknown authors'
        s_title = ''
        if self.title_html:
            s_title = ', "%s"' % self.title_html
        s_note = ''
        if self.note_html:
            s_note = ', %s' % self.note_html
        s_institution = ''
        if self.institution:
            s_institution = ', %s' % self.institution
        s_year = ''
        if self.year:
            s_year = ' (%d)' % self.year
        s = '%s%s%s%s%s.' % (s_authors, s_title, s_note, s_institution, s_year)
        return s
