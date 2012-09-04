# -*- coding: utf-8 -*-
# xsams_hitran_functions.py
# Christian Hill
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# v0.1 3/9/12
# Methods for writing the functions of an XSAMS document resulting from
# a query of the HITRAN database.

def xsams_functions():
    """
    Yields Functions for the XSAMS document - these are hard-coded.
    """

    yield '<Functions>'
    yield xsams_function_FgammaL()
    yield xsams_function_Fdelta()
    yield '</Functions>'

def xsams_function_FgammaL():
    """
    Return the XSAMS XML for the FgammaL function, which calculates the air-
    broadened Lorentzian HWHM from its reference values, gammaL_ref at a
    specified pressure, p, and temperature, T, using the temperature
    exponent, n.

    """

    return """
<Function functionID="FgammaL">
    <Comments>
        This function gives the pressure- and temperature-dependence of the
        Lorentzian component of the pressure-broadened line width (HWHM)
    </Comments>
    <Expression computerLanguage="Fortran">
        gammaL_ref * p * (296./T)**n
    </Expression>
    <Y name="gammaL" units="1/cm"/>
    <Arguments>
        <Argument name="T" units="K">
            <Description>The absolute temperature, in K</Description>
        </Argument>
        <Argument name="p" units="atm">
            <Description>The partial pressure of the broadening species,
                         in atm</Description>
        </Argument>
    </Arguments>
    <Parameters>
        <Parameter name="gammaL_ref" units="1/cm">
            <Description>The Lorentzian HWHM of the line, broadened at
                         Tref = 296 K and broadening species partial pressure
                         pref = 1atm</Description>
        </Parameter>
        <Parameter name="n" units="unitless">
            <Description>
                The temperature exponent of the gammaL function
            </Description>
        </Parameter>
    </Parameters>
</Function>
    """

def xsams_function_Fdelta():
    """
    Return the XSAMS XML for the Fdelta function, which calculates the air-
    broadened pressure shift from its reference values, delta_ref at a
    specified pressure, p.

    """

    return """
<Function functionID="Fdelta">
    <Comments>
        This function gives the pressure-dependence of the absorption line
        wavenumber shift: nu = nu_ref + (delta).(p/pref)
    </Comments>
    <Expression computerLanguage="Fortran">
        delta_ref * p
    </Expression>
    <Y name="delta" units="1/cm"/>
    <Arguments>
        <Argument name="p" units="atm">
            <Description>The pressure of the shifting environment,
                         in atm</Description>
        </Argument>
    </Arguments>
    <Parameters>
        <Parameter name="delta_ref" units="1/cm">
            <Description>The pressure-shift of the absorption line at
                         pref = 1 atm</Description>
        </Parameter>
    </Parameters>
</Function>
    """
