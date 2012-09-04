# -*- coding: utf-8 -*-
# xsams_hitran_broadening.py
# Christian Hill
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# v0.1 4/9/12
# Methods to yield the XSAMS XML for the Broadening tags resulting from
# a query of the HITRAN database

from xsams_utils import make_datatype_tag

def xsams_broadening_air(gamma_air_val, gamma_air_err, gamma_air_source_id,
                         n_air_val, n_air_err, n_air_source_id):
    """
    Yield the XSAMS XML for the air-broadening parameters of a transition
    in the HITRAN database.

    """

    if gamma_air_val is None:
        yield ''
        return

    yield '<Broadening envRef="Eair-broadening-ref-env" name="pressure">'
    yield '<Lineshape name="Lorentzian">'
    yield '<Comments>The temperature-dependent pressure broadening Lorentzian'\
                    ' lineshape</Comments>'
    yield '<LineshapeParameter name="gammaL">'
    yield '  <FitParameters functionRef="FgammaL">'
    yield '    <FitArgument name="T" units="K">'
    yield '      <LowerLimit>240</LowerLimit>'
    yield '      <UpperLimit>350</UpperLimit>'
    yield '    </FitArgument>'
    yield '    <FitArgument name="p" units="atm">'
    yield '      <LowerLimit>0.</LowerLimit>'
    yield '      <UpperLimit>1.2</UpperLimit>'
    yield '    </FitArgument>'
    
    yield make_datatype_tag('FitParameter', gamma_air_val, '1/cm',
                            gamma_air_err, None, [gamma_air_source_id,],
                            {'name': 'gammaL_ref'})
    yield make_datatype_tag('FitParameter', n_air_val, '1/cm',
                            n_air_err, None, [n_air_source_id,],
                            {'name': 'n'})

    yield '  </FitParameters>'
    yield '</LineshapeParameter>'
    yield '</Lineshape>'
    yield '</Broadening>'

def xsams_broadening_self(gamma_self_val,gamma_self_err,gamma_self_source_id):
    """
    Yield the XSAMS XML for the self-broadening parameters of a transition
    in the HITRAN database.

    """

    if gamma_self_val is None:
        yield ''
        return

    yield '<Broadening envRef="Eself-broadening-ref-env" name="pressure">'
    yield '<Lineshape name="Lorentzian">'
    yield make_datatype_tag('LineshapeParameter', gamma_self_val, '1/cm',
                            gamma_self_err, None, [gamma_self_source_id,],
                            {'name': 'gammaL'})
    yield '</Lineshape>'
    yield '</Broadening>'

def xsams_shifting_air(delta_air_val, delta_air_err, delta_air_source_id):
    """
    Yield the XSAMS XML for the air-induced shifting parameter of a transition
    in the HITRAN database.

    """

    if delta_air_val is None:
        yield ''
        return

    yield '<Shifting envRef="Eair-broadening-ref-env">'
    yield '<ShiftingParameter name="delta">'
    yield '<FitParameters functionRef="Fdelta">'
    yield '<FitArgument name="p" units="atm">'
    yield '<LowerLimit>0.</LowerLimit>'
    yield '<UpperLimit>1.2</UpperLimit>'
    yield '</FitArgument>'
    yield make_datatype_tag('FitParameter', delta_air_val, '1/cm',
                            delta_air_err, None, [delta_air_source_id,],
                            {'name': 'delta_ref'})
    yield '</FitParameters>'
    yield '</ShiftingParameter>'
    yield '</Shifting>'
