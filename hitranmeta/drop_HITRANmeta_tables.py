#!/usr/bin/env python
# -*- coding: utf-8 -*-
# drop_HITRANmeta_tables.py

# Christian Hill, 19/8/11
import MySQLdb
from HITRAN_configs import *

conn = MySQLdb.connect(host="localhost", user=username,
                       db=dbname, passwd=password)
cursor = conn.cursor()

# table names, in the order they have to be dropped:
tables = ['hitranmeta_moleculename', 'hitranmeta_iso',
          'hitranmeta_molecule', 'hitranmeta_case']

for table in tables:
    cursor.execute('DROP TABLE %s' % table)
conn.commit()
conn.close()
