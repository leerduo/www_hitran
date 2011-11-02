# -*- coding: utf-8 -*-
from datetime import datetime
from hitrancia.models import CollisionPair

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

class CIASearchForm:
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

            if post_data.get('Tmin') == '':
                self.Tmin = None
            else:
                self.Tmin = float(post_data.get('Tmin'))
            if self.Tmin < 0.:
                # negative Tmin is silly but OK
                self.Tmin = None
            if post_data.get('Tmax') == '':
                self.Tmax = None
            else:
                self.Tmax = float(post_data.get('Tmax'))

            self.datestamp = datetime.strptime(post_data.get('date'),
                    '%Y-%m-%d').date()
        except ValueError:
            return

        if self.numin is not None and self.numax is not None and\
                self.numin > self.numax:
            # numin must be <= numax
            self.error_msg = '<p class="error_msg">Wavenumber/wavelength'\
                'minimum must not be greater than maximum</p>'
            return

        if self.Tmin is not None and self.Tmax is not None and\
                self.Tmin > self.Tmax:
            # Tmin must be <= Tmax
            self.error_msg = '<p class="error_msg">Temperature'\
                ' minimum must not be greater than maximum</p>'
            return

        selected_pairIDs = post_data.getlist('collision_pair')
        if not selected_pairIDs:
            # no collision pairs selected!
            self.error_msg = '<p class="error_msg">No collision pairs'\
                             ' selected</p>'
            return
        
        self.collision_pair_ids = list(selected_pairIDs)
        self.collision_pairs = CollisionPair.objects.filter(
                                    pk__in=selected_pairIDs)
        self.output_formats = post_data.getlist('output_format')
        if not self.output_formats:
            # no output formats selected!
            self.error_msg = '<p class="error_msg">No output format'\
                             ' specified</p>'
            return

        self.error_msg = ''
        self.valid = True
        return

    def is_valid(self):
        if self.valid:
            return True, ''
        return False, self.error_msg



