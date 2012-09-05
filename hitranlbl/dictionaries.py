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
