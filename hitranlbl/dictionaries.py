# -*- coding: utf-8 -*-
from caseless_dict import CaselessDict

returnables_list = [
'XSAMSVersion',
'SchemaLocation',
'SourceID',
'SourceAuthorName',
'SourceTitle',
'SourcePageBegin',
'SourcePageEnd',
'SourceVolume',
'SourceYear',
'SourceCategory',
'SourceComments',
'RadTransID',
'RadTransComments',
'RadTransUpperStateRef',
'RadTransLowerStateRef',
'RadTransWavenumber',
'RadTransWavenumberUnit',
'RadTransWavenumberRef',
'RadTransWavenumberAccuracy',
'RadTransProbabilityA',
'RadTransProbabilityAUnit',
'RadTransProbabilityARef',
'RadTransProbabilityAAccuracy',
'RadTransProbabilityMultipoleValue',
'MoleculeChemicalName',
'MoleculeOrdinaryStructuralFormula',
'MoleculeStoichiometricFormula',
'MoleculeIonCharge',
'MoleculeID',
'MoleculeInchi',
'MoleculeInchiKey',
'MoleculeSpeciesID',
'MoleculeComment',
'MoleculeStructure',
'MoleculeStateID',
'MoleculeStateMolecularSpeciesID',
'MoleculeStateEnergy',
'MoleculeStateEnergyUnit',
'MoleculeStateEnergyOrigin',
'MoleculeStateTotalStatisticalWeight',
'MoleculeStateNuclearSpinIsomer',
'MoleculeStateQuantumNumbers',
'MoleculeQnStateID',
'MoleculeQnCase',
'MoleculeQnLabel',
'MoleculeQnValue',
'MoleculeQnAttribute',
'MoleculeQNElecStateLabel',
'MoleculeQnXML',
'EnvironmentID',
'EnvironmentTemperature',
'EnvironmentTemperatureUnit',
'EnvironmentTotalPressure',
'EnvironmentTotalPressureUnit',
'EnvironmentSpecies',
'EnvironmentSpeciesName',
]
RETURNABLES = {}
for returnable in returnables_list:
    RETURNABLES[returnable] = 'dummy'

restrictable_types = CaselessDict({
'MoleculeChemicalName': str,
'MoleculeStoichiometricFormula': str,
'MoleculeInchiKey': str,
'InchiKey': str,
'RadTransWavenumber': float,
'RadTransWavelength': float,
'RadTransProbabilityA': float,
})
RESTRICTABLES = {}
for restrictable in restrictable_types:
    RESTRICTABLES[restrictable] = 'dummy'

requestables_list = [
'Environments',
'Molecules',
'RadiativeTransitions',
'RadiativeCrossSections',
]
REQUESTABLES = {}
for requestable in requestables_list:
    REQUESTABLES[requestable] = 'dummy'

EXAMPLE_QUERIES = {
"SELECT * WHERE (RadTransWavelength >= 10000.0 AND RadTransWavelength <= 100000.0) AND ((InchiKey IN ('DXHPZXWIPWDXHJ-VQEHIDDOSA-N','DXHPZXWIPWDXHJ-HQMMCQRPSA-N','DXHPZXWIPWDXHJ-UHFFFAOYSA-N')))": '(12C)(32S), (12C)(34S), (12C)(33S) lines between 10000 and 100000 Angstroms',

"SELECT ALL WHERE RadTransWavenumber>6000. AND RadTransWavenumber<6100. AND (MoleculeChemicalName in ('H2O', 'Ammonia') OR MoleculeStoichiometricFormula='HOCl')": 'H2O, NH3 and HOCl lines between 6000 and 6100 cm-1',
}

# the full URL to use these queries is:
# "vamdc.mssl.ucl.ac.uk/node/hitran/tap/sync/?REQUEST=doQuery&LANG=VSS2&FORMAT=XSAMS&QUERY=<query>"
