#!/usr/bin/env python
# -*- coding: utf-8 -*-
# load_cia_species.py

# Christian Hill, 6/10/11

import MySQLdb
from HITRAN_configs import *

conn = MySQLdb.connect(host='localhost', user=username, db='minihitran',
                       passwd=password)
cursor = conn.cursor()

# "molecule" H
command = 'INSERT INTO hitranmeta_molecule (molecID, molecID_str, InChI, InChIKey, stoichiometric_formula, ordinary_formula, ordinary_formula_html, common_name) VALUES (1001, "H", "InChI=1S/H", "YZCKVEUIGOORGS-UHFFAOYSA-N", "H", "H", "H", "Hydrogen")'
#cursor.execute(command)

# "molecule" He
command = 'INSERT INTO hitranmeta_molecule (molecID, molecID_str, InChI, InChIKey, stoichiometric_formula, ordinary_formula, ordinary_formula_html, common_name) VALUES (1002, "He", "InChI=1S/He", "SWQJXJOGLNCZEY-UHFFAOYSA-N", "He", "He", "He", "Helium")'
#cursor.execute(command)

# "molecule" Ar
command = 'INSERT INTO hitranmeta_molecule (molecID, molecID_str, InChI, InChIKey, stoichiometric_formula, ordinary_formula, ordinary_formula_html, common_name) VALUES (1018, "Ar", "InChI=1S/Ar", "XKRFYHLGVUSROY-UHFFAOYSA-N", "Ar", "Ar", "Ar", "Argon")'
#cursor.execute(command)

# molecule H2
command = 'INSERT INTO hitranmeta_molecule (molecID, molecID_str, InChI, InChIKey, stoichiometric_formula, ordinary_formula, ordinary_formula_html, common_name) VALUES (2000, "H2", "InChI=1S/H2/h1H", "UFHFLCQGNIYNRP-UHFFFAOYSA-N", "H2", "H2", "H<sub>2</sub>", "Molecular Hydrogen")'
#cursor.execute(command)

# iso 1H
command = 'INSERT INTO hitranmeta_iso (isoID, isoID_str, InChI_explicit, InChIKey_explicit, InChI, InChIKey, molecule_id, iso_name, iso_name_html) VALUES (1, "H_1", "InChI=1S/H/i1+0", "YZCKVEUIGOORGS-IGMARMGPSA-N", "InChI=1S/H", "YZCKVEUIGOORGS-UHFFAOYSA-N", 1001, "H", "H")'
#cursor.execute(command)

# iso 4He
command = 'INSERT INTO hitranmeta_iso (isoID, isoID_str, InChI_explicit, InChIKey_explicit, InChI, InChIKey, molecule_id, iso_name, iso_name_html) VALUES (1, "He_1", "InChI=1S/He/i1+0", "SWQJXJOGLNCZEY-IGMARMGPSA-N", "InChI=1S/He", "SWQJXJOGLNCZEY-UHFFAOYSA-N", 1002, "He", "He")'
#cursor.execute(command)

# iso (1H)2
command = 'INSERT INTO hitranmeta_iso (isoID, isoID_str, InChI_explicit, InChIKey_explicit, InChI, InChIKey, molecule_id, iso_name, iso_name_html, case_id) VALUES (1, "H2_1", "InChI=1S/H2/h1H/i1+0H", "UFHFLCQGNIYNRP-HXFQMGJMSA-N", "InChI=1S/H2/h1H", "UFHFLCQGNIYNRP-UHFFFAOYSA-N", 2000, "H2", "H<sub>2</sub>", 1)'
#cursor.execute(command)

# iso 40Ar
command = 'INSERT INTO hitranmeta_iso (isoID, isoID_str, InChI_explicit, InChIKey_explicit, InChI, InChIKey, molecule_id, iso_name, iso_name_html) VALUES (1, "Ar_1", "InChI=1S/Ar/i1+0", "XKRFYHLGVUSROY-IGMARMGPSA-N", "InChI=1S/Ar", "XKRFYHLGVUSROY-UHFFAOYSA-N", 1018, "Ar", "Ar")'
#cursor.execute(command)

conn.commit()
