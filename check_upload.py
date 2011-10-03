#!/usr/bin/env python
# -*- coding: utf-8 -*-
# check_upload.py

# Christian Hill, 30/8/11
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# A script to check the uploaded transitions and states can regenerate the
# original .par line from which they were created.

import os
import sys

HOME = os.getenv('HOME')
sys.path.append(os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.join(HOME, 'research/HITRAN/pyHAWKS'))
from hitran_cases import *
from hitran_transition import HITRANTransition
from hitran_param import HITRANParam
from hitranmeta.models import Iso
from hitranlbl.models import Trans, Prm
import hitran_meta

molec_id = int(sys.argv[1])
isos = Iso.objects.filter(molecule__molecID=molec_id).all()
print len(isos),'isotopologues for molec', molec_id

transitions = Trans.objects.filter(iso__in=isos).all()
ntrans = len(transitions)
last_pc = 0
for i, trans in enumerate(transitions):
    prms = trans.prm_set
    #for prm_name in ('Sw', 'A', 'gamma_air', 'gamma_self', 'n_air',
    #                 'delta_air'):
    #    exec('trans.%s = prms.get(name="%s")' % (prm_name, prm_name))

    Ierr = trans.par_line[127:133]
    Iref = trans.par_line[133:145]

    this_trans = HITRANTransition()
    this_trans.par_line = trans.par_line
    this_trans.molec_id = molec_id
    this_trans.iso_id = trans.iso.isoID
    this_trans.nu = HITRANParam(val=prms.get(name="nu").val,
        ref=int(Iref[:2]), name='nu', ierr=int(Ierr[0]))

    this_trans.Sw = HITRANParam(val=prms.get(name="Sw").val,
        ref=int(Iref[2:4]), name='Sw', ierr=int(Ierr[1]), relative=True)
    this_trans.A = HITRANParam(val=prms.get(name="A").val,
        ref=int(Iref[2:4]), name='Sw', ierr=int(Ierr[1]), relative=True)
    this_trans.gamma_air = HITRANParam(val=prms.get(name="gamma_air").val,
                ref=int(Iref[4:6]), name='gamma_air', ierr=int(Ierr[2]),
                relative=True)
    try:
        this_trans.gamma_self = HITRANParam(
            val=prms.get(name="gamma_self").val,
            ref=int(Iref[6:8]), name='gamma_self', ierr=int(Ierr[3]),
            relative=True)
    except Prm.DoesNotExist:
        pass
    this_trans.n_air = HITRANParam(val=prms.get(name="n_air").val,
        ref=int(Iref[8:10]), name='n_air', ierr=int(Ierr[4]),
        relative=True)
    try:
        this_trans.delta_air = HITRANParam(val=prms.get(name="delta_air").val,
                    ref=int(Iref[10:12]), name='delta_air', ierr=int(Ierr[5]))
    except Prm.DoesNotExist:
        pass
    this_trans.Elower = trans.Elower
    this_trans.gp = trans.gp
    this_trans.gpp = trans.gpp
    this_trans.multipole = trans.multipole

    # grab the flag from the par_line
    this_trans.flag = trans.par_line[145]

    CaseClass = hitran_meta.get_case_class(this_trans.molec_id,
                                           this_trans.iso_id)
    this_trans.statep = CaseClass(molec_id=this_trans.molec_id,
                iso_id=this_trans.iso_id, E=trans.statep.energy,
                g=trans.statep.g, s_qns=trans.statep.s_qns)
    this_trans.statepp = CaseClass(molec_id=this_trans.molec_id,
                iso_id=this_trans.iso_id, E=trans.statepp.energy,
                g=trans.statepp.g, s_qns=trans.statepp.s_qns)
    this_trans.case_module = hitran_meta.get_case_module(this_trans.molec_id,
                        this_trans.iso_id)

    if not this_trans.validate_as_par():
        print this_trans.par_line,'\nfailed to validate! I produced:'
        print this_trans.get_par_str()
        sys.exit(1)
    i += 1
    this_pc = float(i)/ntrans * 100
    if int(this_pc) != last_pc:
        last_pc += 1
        print '%d%%' % last_pc
                
print ntrans,'transitions checked out OK!'

