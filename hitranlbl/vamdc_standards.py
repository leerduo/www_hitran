# -*- coding: utf-8 -*-
# vamdc_standards.py
from string import lower

STANDARDS_VERSION = '1.0'

HEADERS = ['COUNT-SOURCES',
           'COUNT-ATOMS',
           'COUNT-MOLECULES',
           'COUNT-SPECIES',
           'COUNT-STATES',
           'COUNT-COLLISIONS',
           'COUNT-RADIATIVE',
           'COUNT-NONRADIATIVE',
           'TRUNCATED',
           'APPROX-SIZE',
          ]

REQUESTABLES = map(lower, ['AtomStates',
                           'Atoms',
                           'Collisions',
                           'Environments',
                           'Functions',
                           'Methods',
                           'MoleculeBasisStates',
                           'MoleculeQuantumNumbers',
                           'MoleculeStates',
                           'Molecules',
                           'NonRadiativeTransitions',
                           'Particles',
                           'Processes',
                           'RadiativeCrossSections',
                           'RadiativeTransitions',
                           'Solids',
                           'Sources',
                           'Species',
                           'States'
                          ])

