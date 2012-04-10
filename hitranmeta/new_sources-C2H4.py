#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sources.py

# Christian Hill, 4/3/12
import MySQLdb
from HITRAN_configs import *

conn = MySQLdb.connect(host="localhost", user=username,
                       db=dbname, passwd=password)
cursor = conn.cursor()

molecule = 'C2H4'
mapping = {}
mapping['nu'] = [
    (1,560), (2,561), (3,562)
]
mapping['S'] = [
    (1,564), (2,566), (3,562)
]
mapping['gamma_air'] = [
    (1,567), (2,562)
]
mapping['gamma_self'] = [
    (0,1), (1,562)
]
mapping['n_air'] = [
    (0,1), (1,567)
]
mapping['delta_air'] = [
    (0,1),
]

for prm in mapping:
    for (irefID, src_id) in mapping[prm]:
        refID = '%s-%s-%d' % (molecule, prm, irefID)
        print refID,'-->',src_id
        command = 'UPDATE hitranmeta_ref SET source_id=%d WHERE refID="%s"'\
                        % (src_id, refID)
        print command
        cursor.execute(command)
        command = 'UPDATE hitranlbl_prm SET source_id=%d WHERE ref_id IN'\
                  ' (SELECT id FROM hitranmeta_ref WHERE refID="%s")'\
                        % (src_id, refID)
        print command
        cursor.execute(command)

conn.commit()
conn.close()


