# -*- coding: utf-8 -*-
from datetime import datetime
from hitranmeta.models import Molecule

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

def convert_to_torr(num, units):
    """
    Convert the quantity num from units to Torr. If num is None, return
    None instead.

    """

    if num is None or units == 'Torr':
        return num
    if units == 'Pa':
        return num / 101325. * 760.
    elif units == 'atm':
        return num / 760.
    elif units == 'bar':
        return num / 1.01325 * 760.
    elif units == 'mbar':
        return num / 1013.25 * 760.
    else:
        print 'unrecognised units: %s' % units
        return None

class XscSearchForm:
    def __init__(self, post_data):
        self.valid = False
        self.error_msg = '<p class="error_msg">Unspecified error<p>'
        try:
            # wavenumber, numin and numax
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

            # temperature, Tmin and Tmax
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

            # pressure, pmin and pmax
            self.p_units = post_data.get('pmin_units')
            if post_data.get('pmin') == '':
                self.pmin = None
            else:
                self.pmin = float(post_data.get('pmin'))
            if self.pmin < 0.:
                # negative pmin is silly but OK
                self.pmin = None
            if post_data.get('pmax') == '':
                self.pmax = None
            else:
                self.pmax = float(post_data.get('pmax'))
            self.pmin = convert_to_torr(self.pmin, self.p_units)
            self.pmax = convert_to_torr(self.pmax, self.p_units)

            if post_data.get('min_sigmax').strip() == '':
                self.min_sigmax = None
            else:
                self.min_sigmax = float(post_data.get('min_sigmax'))

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

        if self.pmin is not None and self.pmax is not None and\
                self.pmin > self.pmax:
            # pmin must be <= pmax
            self.error_msg = '<p class="error_msg">Pressure'\
                ' minimum must not be greater than maximum</p>'
            return

        selected_molecIDs = post_data.getlist('molecule')
        if not selected_molecIDs:
            # no molecules selected!
            self.error_msg = '<p class="error_msg">No molecules'\
                             ' selected</p>'
            return
        
        self.molecule_ids = list(selected_molecIDs)
        self.molecules = Molecule.objects.filter(
                                    pk__in=selected_molecIDs)
        #self.output_formats = post_data.getlist('output_format')
        #if not self.output_formats:
        #    # no output formats selected!
        #    self.error_msg = '<p class="error_msg">No output format'\
        #                     ' specified</p>'
        #    return
        self.output_formats = ['xsc',]

        self.error_msg = ''
        self.valid = True
        return

    def is_valid(self):
        if self.valid:
            return True, ''
        return False, self.error_msg
