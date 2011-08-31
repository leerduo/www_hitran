#!/usr/bin/env python
# -*- coding: utf-8 -*-
# delete_molecule.py

# Christian Hill, 30/8/11
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# A script to delete a molecule from the hitranlbl database tables

import sys
import MySQLdb
from HITRAN_configs import *

conn = MySQLdb.connect(host='localhost', user=username, db=dbname,
                       passwd=password)
cursor = conn.cursor()

try:
    molec_id = int(sys.argv[1])
except:
    print 'usage is:'
    print '%s <molec_id>' % sys.argv[0]
    sys.exit(1)

command = 'SELECT id FROM hitranmeta_iso WHERE molecule_id=%d' % molec_id
cursor.execute(command)
isoIDs = [int(x[0]) for x in cursor.fetchall()]
print isoIDs
s_isoIDs = '(%s)' % (', '.join(['%d' % isoID for isoID in isoIDs]))

command = 'DELETE FROM hitranmeta_prm WHERE trans_id IN (SELECT id FROM'\
          ' hitranlbl_trans WHERE iso_id IN %s)' % (s_isoIDs)
print command
command = 'DELETE FROM hitranmeta_qns WHERE state_id IN (SELECT id FROM'\
          ' hitranlbl_state WHERE iso_id IN %s)' % (s_isoIDs)
print command
command = 'DELETE FROM hitranmeta_trans WHERE iso_id in %s' % (s_isoIDs)
print command
command = 'DELETE FROM hitranmeta_state WHERE iso_id in %s' % (s_isoIDs)
print command
