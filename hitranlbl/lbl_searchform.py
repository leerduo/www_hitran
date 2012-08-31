# -*- coding: utf-8 -*-
from datetime import datetime

def convert_to_wavenumber(num, units):
        """
        Convert the quantity num from units to cm-1. If num None or zero and
        we attempt to divide by it, return None instead.

        """

        if num is None or units == 'cm-1':
            return num
        try:
            if units == 'A':
                num = 1.e8/num
            elif units == 'nm':
                num = 1.e7/num
            elif units == 'um':
                num = 1.e4/num
            elif units == 'Hz':
                num /= 2.99792458e10
            elif units == 'kHz':
                num /= 2.99792458e7
            elif units == 'MHz':
                num /= 2.99792458e4
            elif units == 'GHz':
                num /= 29.9792458
            elif units == 'THz':
                num /= 2.99792458e-2
            else:
                print 'unrecognised units: %s' % units
                return None
        except ZeroDivisionError:
            return None
        return num

class LblSearchForm:
    def __init__(self, post_data):
        self.valid = False
        self.error_msg = '<p class="error_msg">Unspecified error<p>'

        try:
            if post_data.get('numin') == '':
                self.numin = None
            else:
                self.numin = float(post_data.get('numin'))
            if post_data.get('numax') == '':
                self.numax = None
            else:
                self.numax = float(post_data.get('numax'))
            self.nu_units = post_data.get('numin_units')

            self.numin = convert_to_wavenumber(self.numin, self.nu_units)
            self.numax = convert_to_wavenumber(self.numax, self.nu_units)
            if self.nu_units in ('A', 'nm', 'um'):
                self.numin, self.numax = self.numax, self.numin

            self.Swmin = None
            self.Amin = None
            self.intens_thresh_type = post_data.get('intens_thresh_type')
            intens_min = post_data.get('intens_min')
            if intens_min != '':
                if self.intens_thresh_type == 'Sw':
                    self.Swmin = float(intens_min)
                elif self.intens_thresh_type == 'A':
                        self.Amin = float(intens_min)

            # negative intensity thresholds are silly but OK
            if self.Swmin <= 0.:
                self.Swmin = None
            if self.Amin <= 0.:
                self.Amin = None

            self.output_collection_index = int(
                    post_data.get('output_collection'))
            self.valid_on = datetime.strptime(post_data.get('valid_on'),
                    '%Y-%m-%d').date()
        except ValueError:
            self.error_msg = '<p class="error_msg">Invalid search terms</p>'
            return
        if self.numin is not None and self.numax is not None and\
                self.numin > self.numax:
            # numin must be <= numax
            self.error_msg = '<p class="error_msg">Wavenumber/wavelength'\
                'minimum must not be greater than maximum</p>'
            return

        #selected_molecIDs = post_data.getlist('molecule')
        #if not selected_molecIDs:
        #    # no molecules selected!
        #    self.error_msg = '<p class="error_msg">No molecules selected</p>'
        #    return
        # make sure the selected_molecIDs are integers
        #for molecID in selected_molecIDs:
        #    try:
        #        dummy = int(molecID)
        #    except ValueError:
        #        self.error_msg = '<p class="error_msg">Invalid molecule ID'\
        #            ' specified</p>'
        #        return
        #self.selected_molecIDs = selected_molecIDs

        selected_isoIDs = post_data.getlist('iso')
        if not selected_isoIDs:
            # no isotopologues selected!
            self.error_msg = '<p class="error_msg">No isotopologues selected'\
                             '</p>'
            return
        # make sure the selected_isoIDs are integers
        for isoID in selected_isoIDs:
            try:
                dummy = int(isoID)
            except ValueError:
                self.error_msg = '<p class="error_msg">Invalid isotopologue'\
                                 'ID specified</p>'
                return
        self.selected_isoIDs = selected_isoIDs
            

        # don't allow any shenanigans with the default entries or field
        # separators
        default_entries = {'whitespace': ' ', 'asterisk': '*',
                           'minus1': '-1', 'hash': '#'}
        field_separators = {'none': '', 'tab': '\t', 'space': ' ',
                            'comma': ',', 'semicolon': ';', 'colon': ':'}
        try:
            self.default_entry = default_entries[post_data.get(
                                                    'default_entry')]
        except KeyError:
            self.error_msg = '<p class="error_msg">Invalid default entry</p>'
            return
        try:
            self.field_separator = field_separators[post_data.get(
                                                        'field_separator')]
        except KeyError:
            self.error_msg = '<p class="error_msg">Invalid field separator</p>'
            return

        output_sources = post_data.getlist('output_sources')
        self.output_html_sources = self.output_bibtex_sources = False
        if 'html' in output_sources:
            self.output_html_sources = True
        if 'bibtex' in output_sources:
            self.output_bibtex_sources =  True
        self.output_sources = self.output_html_sources\
                            | self.output_bibtex_sources

        output_states = post_data.get('output_states')
        self.output_states = False
        if output_states:
            self.output_states = True

        self.error_msg = ''
        self.valid = True
        return

    def is_valid(self):
        if self.valid:
            return True, ''
        return False, self.error_msg


