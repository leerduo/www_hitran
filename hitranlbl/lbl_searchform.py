# -*- coding: utf-8 -*-
from datetime import datetime

def convert_to_wavenumber(self, num, units):
        """
        Convert the quantity num from units to cm-1. If num is zero and
        we attempt to divide by it, return None instead.

        """

        if from_units == 'cm-1':
            return num
        try:
            if from_units == 'A':
                num = 1.e8/num
            elif from_units == 'nm':
                num = 1.e7/num
            elif from_units == 'um':
                num = 1.e4/num
            elif from_units == 'Hz':
                num /= 2.99792458e10
            elif from_units == 'kHz':
                num /= 2.99792458e7
            elif from_units == 'MHz':
                num /= 2.99792458e4
            elif from_units == 'GHz':
                num /= 29.9792458
            elif from_units == 'THz':
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
            self.numax = float(post_data.get('numax'))
            self.nu_units = post_data.get('numin_units')

            self.numin = convert_to_wavenumber(self.numin, self.nu_units)
            self.numin = convert_to_wavenumber(self.numin, self.nu_units)

            if post_data.get('Swmin') == '':
                self.Swmin = None
            else:
                self.Swmin = float(post_data.get('Swmin'))
            if self.Swmin < 0.:
                # negative Swmin is silly but OK
                self.Swmin = None
            self.output_collection = post_data.getlist('output_collection')
            self.datestamp = datetime.strptime(post_data.get('date'),
                    '%Y-%m-%d').date()
        except ValueError:
            return
        if self.numin > self.numax:
            # numin must be <= numax
            self.error_msg = '<p class="error_msg">Wavenumber/wavelength'
                'minimum must not be greater than maximum</p>'
            return

        selected_molecIDs = post_data.getlist('molecule')
        if not selected_molecIDs:
            # no molecules selected!
            self.error_msg = '<p class="error_msg">No molecules selected</p>'
            return
        # make sure the selected_molecIDs are integers
        for molecID in selected_molecIDs:
            try:
                dummy = int(molecID)
            except ValueError:
                self.error_msg = '<p class="error_msg">Invalid molecule ID'\
                    ' specified</p>'
                return
        self.selected_molecIDs = selected_molecIDs

        self.error_msg = ''
        self.valid = True
        return

    def is_valid(self):
        if self.valid:
            return True, ''
        return False, self.error_msg


