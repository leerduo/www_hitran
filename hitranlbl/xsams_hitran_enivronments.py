# -*- coding: utf-8 -*-
# xsams_hitran_environments.py
# Christian Hill
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# v0.1 3/9/12
# Methods for writing the environments of an XSAMS document resulting from
# a query of the HITRAN database.

def xsams_environments():
    """
    Yields Environments for the XSAMS document - these are hard-coded.
    """

    yield '<Environments>'
    yield xsams_environment_refT()
    yield xsams_environment_refpT()
    yield xsams_environment_air_broadening()
    yield xsams_environment_self_broadening()
    yield '</Environments>'

def xsams_environment_refT():
    """
    Return the XSAMS XML for the reference temperature environment for HITRAN,
    296 K.

    """

    return """
    <!-- the HITRAN reference temperature, 296 K -->
    <Environment envID="EHITRAN_refT">
        <Temperature>
            <Value units="K">296.</Value>
        </Temperature>
    </Environment>
    """
def xsams_environment_refpT():
    """
    Return the XSAMS XML for the reference temperature and pressure environment
     for HITRAN, 296 K and 1 atm.

    """

    return """
    <!-- the HITRAN reference pressure and temperature, 1 atm and 296 K -->
    <Environment envID="EHITRAN_refpT">
        <Temperature>
            <Value units="K">296.</Value>
        </Temperature>
        <TotalPressure>
            <Value units="atm">1.</Value>
        </TotalPressure>  
    </Environment>
    """

def xsams_environment_air_broadening():
    """
    Return the XSAMS XML for the air-broadening reference environment for
    HITRAN: taken to be 79% N2, 21% O2 at 296 K and total pressure 1 atm.

    """

    return """<!-- the HITRAN air-broadening reference conditions -->
    <Environment envID="Eair-broadening-ref-env">
        <Temperature>
            <Value units="K">296.</Value>
        </Temperature>
        <TotalPressure>
            <Value units="atm">1.</Value>
        </TotalPressure>
        <Composition>
            <Species name="N2">
                <MoleFraction>
                    <Value units="unitless">0.79</Value>
                </MoleFraction>
            </Species>
            <Species name="O2">
                <MoleFraction>
                    <Value units="unitless">0.21</Value>
                </MoleFraction>
            </Species>
        </Composition>
    </Environment>
    """

def xsams_environment_self_broadening():
    """
    Return the XSAMS XML for the self-broadening reference environment for
    HITRAN: so we don't need to repeat the species reference for every self-
    broadened species, we set Species="self" and hope MLD doesn't notice...

    """

    return """<!-- the HITRAN self-broadening reference conditions -->
    <Environment envID="Eself-broadening-ref-env">
        <Temperature>
            <Value units="K">296.</Value>
        </Temperature>
        <TotalPressure>
            <Value units="atm">1.</Value>
        </TotalPressure>
        <Composition>
            <Species name="self">
                <MoleFraction>
                    <Value units="unitless">1.</Value>
                </MoleFraction>
            </Species>
        </Composition>
    </Environment>
    """

