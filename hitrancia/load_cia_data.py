#!/usr/bin/env python
# -*- coding: utf-8 -*-
# load_cia_data.py

# Christian Hill, 14/10/11
# Load up metadata to the hitrancia_cia table and place the corresponding
# text table files in the results/cia directory

import os
import sys
import glob
import datetime
import xn_utils

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
cia_path = os.path.join(HOME, 'research/HITRAN/HITRAN2008/updates/CIA/')
sys.path.append(cia_path)
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

ciaresults_path = os.path.join(hitran_path, 'results/cia')

import hitranmeta.models
from models import CIA

def check_nugrid(nugrid):
    """ Check that the nu grid is regularly-spaced """
    dnuset = []
    for i in range(1, len(nugrid)):
        this_dnu = nugrid[i] - nugrid[i-1]
        newdnu = True
        for dnu in dnuset:
            if xn_utils.feq(dnu, this_dnu, 1.e-5):
                newdnu = False
                break
        if newdnu:
            dnuset.append(this_dnu)
    return dnuset

def check_single_error(s_err_list):
    """ Determine if the error list consists of only one distinct value """
    s_err = s_err_list[0]
    for x in s_err_list:
        if x is None:
            return False
        if s_err != x:
            return False
    return True

def integrity_check(exp1, exp2):
    s_check = 'checking that %s == %s:' % (exp1, exp2)
    check = False
    if eval('xn_utils.feq(%s, %s)' % (exp1, exp2)):
        check = True
    return s_check, check

try:
    collision_pair = sys.argv[1]
    species1, species2 = collision_pair.split('-')
except:
    print 'usage is:'
    print '%s <species 1>-<species 2>' % sys.argv[0]
    sys.exit(1)

filenames = []
filenames.extend(glob.glob(os.path.join(cia_path,'Main-Folder/%s/*.cia'
                                    % collision_pair)))
filenames.extend(glob.glob(os.path.join(cia_path, 'Alternate-Folder/%s/*.cia'
                                    % collision_pair)))

nT = 0
for filename in filenames:
    print filename
    mod_date = datetime.date.fromtimestamp(os.path.getmtime(
                    filename)).isoformat()
    has_errors = False
    fi = open(filename, 'r')
    while fi:
        header = fi.readline()
        cia = CIA.parse_meta(header)
        if not cia:
            break
        nT += 1
        cia.valid_from = mod_date
        if cia.desc == 'Normal':
            modifier = '_norm'
        elif cia.desc == 'Equilibrium':
            modifier = '_eq'
        else:
            modifier = ''
        filestem =  '%s-%s_%.1fK_%d-%d%s' % (species1, species2, cia.T,
                        int(round(cia.numin)), int(round(cia.numax)), modifier)
        cia.filename = '%s.cia' % filestem
        print filestem
        cia_name = os.path.join(ciaresults_path, cia.filename)
        cia_out = open(cia_name, 'w')
        print >>cia_out, header.strip()
        nugrid = []; alpha = []; s_err = []
        for i in range(cia.n):
            line = fi.readline()
            nugrid.append(float(line[:10]))
            alpha.append(float(line[10:21]))
            try:
                this_err = line[21:].strip()
                if not this_err:
                    s_err.append(None)
                else:
                    s_err.append(line[21:].strip('\n'))
                    has_errors = True
            except ValueError:
                s_err.append(None)
            print >>cia_out, line.strip('\n')
        cia_out.close()
        if not has_errors:
            s_err = []
        s_check, check = integrity_check('cia.numin', 'nugrid[0]')
        s_check, check = integrity_check('cia.numax', 'nugrid[cia.n-1]')
        s_check, check = integrity_check('cia.alphamax', 'max(alpha)')
        dnu_vals = check_nugrid(nugrid)
        if len(dnu_vals) == 1:
            if dnu_vals[0]:
                cia.dnu = dnu_vals[0]
        else:
            nugrid_name = os.path.join(ciaresults_path, '%s.nu' % filestem)
            xn_utils.write_list(nugrid_name, nugrid)
        alpha_name = os.path.join(ciaresults_path, '%s.alpha' % filestem)
        xn_utils.write_list(alpha_name, alpha, '%10.3e')
        if has_errors:
            if check_single_error(s_err):
                cia.error = float(s_err[0])
                print 'single error value:', s_err[0]
            else:
                print 'multi-valued error list'
                err_name = os.path.join(ciaresults_path, '%s.err' % filestem)
                xn_utils.write_list(err_name, s_err)
        #cia.save()
    fi.close()        
    print 'number of temperature points =',nT

