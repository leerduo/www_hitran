#!/usr/bin/env python
# -*- coding: utf-8 -*-
# get_latex_sources.py

import MySQLdb
from HITRAN_configs import dbname, username, password

conn = MySQLdb.connect(db=dbname, user=username, passwd=password)
cursor = conn.cursor()
command = 'SELECT id, title_latex FROM hitranmeta_source WHERE title_latex IS NOT NULL'
cursor.execute(command)

fo = open('all_sources.tex', 'w')
print >>fo, '\documentclass[a4paper]{article} \pagestyle{empty}'
print >>fo, r'\begin{document}'
print >>fo, r'\begin{itemize}'
for row in cursor.fetchall():
    id = row[0]; title_latex = row[1]
    print >>fo, '\item %d. %s' % (id, title_latex)
conn.close()
print >>fo, r'\end{itemize}'
print >>fo, r'\end{document}'
fo.close()

