def g_ns_H2O_1(qn_dict):
    """ H2(16O), H2(18O) """
    try:
        Ka = int(qn_dict['Ka'])
        Kc = int(qn_dict['Kc'])
        v3 = int(qn_dict['v3'])
    except KeyError:
        return None
    if (Ka+Kc+v3)%2:
        # ortho-H2O
        return 3
    # para-H2O
    return 1

def g_ns_H2O_3(qn_dict):
    """ H2(17O) """
    g_ns = g_ns_H2O_1(qn_dict)
    if g_ns:
        return 6 * g_ns
    return g_ns

g_ns_Td_XH4 = {'A1': 5, 'A2': 5, 'E': 2, 'F1': 3, 'F2': 3}
def g_ns_CH4_1(qn_dict):
    """ (12C)H4 """
    try:
        rovibSym = qn_dict['rovibSym']
    except KeyError:
        return None
    return g_ns_Td_XH4.get(rovibSym)

def g_ns_CH4_2(qn_dict):
    """ (13C)H4 """
    g_ns = g_ns_CH4_1(qn_dict)
    if g_ns:
        return 2 * g_ns
    return g_ns

def g_ns_XH3(qn_dict):
    K = qn_dict.get('K')
    if K is None:
        return None
    K = int(K)
    l = int(qn_dict.get('l', 0))
    if l == 0:
        if K == 0 or K % 3:
            return 2
        return 4
    elif l > 0:
        if K-1 > 0 and not (K-1) % 3:
            return 4
        return 2
    elif l < 0:
        if not (K+1) % 3:
            return 4
        return 2 
    return None

def g_ns_NH3_1(qn_dict):
    g_ns = g_ns_XH3(qn_dict)
    if g_ns:
        return 3 * g_ns
    return None

def g_ns_NH3_2(qn_dict):
    g_ns = g_ns_XH3(qn_dict)
    if g_ns:
        return 2 * g_ns
    return None

def g_ns_CH3Cl_1(qn_dict):
    # g_ns = 4 for all K (Gamma_rve = A1, A2, E)
    try:
        v4 = int(qn_dict['v4'])
        if v4>0:
            g_ns *= 4   # XXX
    except KeyError:
        pass
    try:
        v5 = int(qn_dict['v5'])
        if v5>0:
            g_ns *= 4   # XXX
    except KeyError:
        pass
    try:
        v6 = int(qn_dict['v6'])
        if v6>0:
            g_ns *= 4   # XXX
    except KeyError:
        pass
    return 4 * g_ns

def g_ns_CH3CN_1(qn_dict):
    g_ns = 1
    try:
        rovibSym = qn_dict['rovibSym']
        if rovibSym == 'E' or rovibSym == 'A1' or rovibSym == 'A2':
            g_ns *= 4
    except KeyError:
        return None
    return 3 *  g_ns


def g_ns_N2_1(qn_dict):
    J = qn_dict.get('J')
    if J is None:
        return None
    J = int(J)
    if J % 2:
        # odd-J must have I = 1 and g_ns = 3
        return 3
    # even-J have I = 0 and 2 and g_ns = 6
    return 6

def g_ns_CH2O_1(qn_dict):
    try:
        v1 = int(qn_dict['v1'])
        v2 = int(qn_dict['v2'])
        v3 = int(qn_dict['v3'])
        v4 = int(qn_dict['v4'])
        v5 = int(qn_dict['v5'])
        v6 = int(qn_dict['v6'])
        Ka = int(qn_dict['Ka'])
        Kc = int(qn_dict['Kc'])
    except KeyError:
        return None
    if Kc % 2:
        if Ka % 2:
            sym='B'
        else:
            sym='A'
    else:
        if Ka % 2:
            sym='B'
        else:
            sym='A'
    if (v4+v5+v6) % 2:
        if sym=='A':
            sym='B'
        else:
            sym='A'
    if sym=='A': return 1
    return 3

def g_ns_H2O2_1(qn_dict):
    try:
        Kc = int(qn_dict['Kc'])
    except KeyError:
        return None
    v6 = int(qn_dict['v6'],0)
    if v6 > 1:
        # don't know about states with more than one quantum of nu6
        return None
    symA = True
    if Kc % 2:
        symA = False
    if v6 == 1:
        symA = not symA
    if symA:
        return 1
    return 3

def g_ns_C2H2_1(qn_dict):
    try:
        vibInv = qn_dict['vibInv']
        syma = False
        if qn_dict['parity'] == '-':
            syma = True
        if vibInv == 'u':
            syma = not syma
        if syma: return 3
        return 1
    except KeyError:
        return None
 
def g_ns_PH3_1(qn_dict):
    g_ns = g_ns_XH3(qn_dict)
    if g_ns:
        return 2 * g_ns
    return None

def g_ns_C2H4_1(qn_dict):
    try:
        Ka = int(qn_dict['Ka'])
        Kc = int(qn_dict['Kc'])
    except KeyError:
        return None
    if Ka % 2 or Kc % 2:
        return 3
    return 7

def g_ns_C2H4_2(qn_dict):
    try:
        Ka = int(qn_dict['Ka'])
    except KeyError:
        return None
    symA = True
    if Ka % 2:
        symA = False
    if int(qn_dict.get('v9', 0)) == 1:
        symA = symA
    if symA:
        return 10
    return 6

def g_ns_CH3OH_1(qn_dict):
    try:
        rovibSym = qn_dict['rovibSym']
    except KeyError:
        return None
    if rovibSym in ('A-', 'A+'):
        return 4
    if rovibSym in ('E1', 'E2'):
        return 8
    return None

g_ns_dict = {}
g_ns_dict['H2(16O)'] = g_ns_H2O_1
g_ns_dict['H2(18O)'] = g_ns_H2O_1
g_ns_dict['H2(17O)'] = g_ns_H2O_3
g_ns_dict['HD(16O)'] = 6        # I(H)=1/5, I(D)=1
g_ns_dict['HD(18O)'] = 6        # I(H)=1/5, I(D)=1
g_ns_dict['HD(17O)'] = 36       # I(H)=1/5, I(D)=1, I(17O)=5/2

g_ns_dict['(16O)2'] = 1         # I(16O)=0
g_ns_dict['(16O)(18O)'] = 1     # I(16O)=I(18O)=0
g_ns_dict['(16O)(17O)'] = 6     # I(16O)=0, I(17O)=5/2

g_ns_dict['(12C)(16O)2'] = 1
g_ns_dict['(13C)(16O)2'] = 2
g_ns_dict['(16O)(12C)(18O)'] = 1
g_ns_dict['(16O)(12C)(17O)'] = 6
g_ns_dict['(16O)(13C)(18O)'] = 2
g_ns_dict['(16O)(13C)(17O)'] = 12
g_ns_dict['(12C)(18O)2'] = 1
g_ns_dict['(17O)(12C)(18O)'] = 6
g_ns_dict['(13C)(18O)2'] = 2

g_ns_dict['(16O)3'] = 1
g_ns_dict['(16O)(16O)(18O)'] = 1
g_ns_dict['(16O)(18O)(16O)'] = 1
g_ns_dict['(16O)(16O)(17O)'] = 6
g_ns_dict['(16O)(17O)(16O)'] = 6

g_ns_dict['(14N)2(16O)'] = 9
g_ns_dict['(14N)(15N)(16O)'] = 6
g_ns_dict['(15N)(14N)(16O)'] = 6
g_ns_dict['(14N)2(18O)'] = 9
g_ns_dict['(14N)2(17O)'] = 54

g_ns_dict['(12C)(16O)'] = 1
g_ns_dict['(13C)(16O)'] = 2
g_ns_dict['(12C)(18O)'] = 1
g_ns_dict['(12C)(17O)'] = 6
g_ns_dict['(13C)(18O)'] = 2
g_ns_dict['(13C)(17O)'] = 12

g_ns_dict['(12C)H4'] = g_ns_CH4_1
g_ns_dict['(13C)H4'] = g_ns_CH4_2
g_ns_dict['(12C)H3D'] = 12  # ? XXX
g_ns_dict['(13C)H3D'] = 24  # ? XXX

g_ns_dict['(14N)(16O)'] = 3
g_ns_dict['(15N)(16O)'] = 2
g_ns_dict['(14N)(18O)'] = 3

g_ns_dict['(32S)(16O)2'] = 1
g_ns_dict['(34S)(16O)2'] = 1

g_ns_dict['(14N)(16O)2'] = 3

g_ns_dict['(14N)H3'] = g_ns_NH3_1
g_ns_dict['(15N)H3'] = g_ns_NH3_2

g_ns_dict['H(14N)(16O)3'] = 6

g_ns_dict['(16O)H'] = 2
g_ns_dict['(18O)H'] = 2
g_ns_dict['(16O)D'] = 3

g_ns_dict['H(19F)'] = 4

g_ns_dict['H(35Cl)'] = 8
g_ns_dict['H(37Cl)'] = 8

g_ns_dict['H(79Br)'] = 8
g_ns_dict['H(81Br)'] = 8

g_ns_dict['H(127I)'] = 12

g_ns_dict['(35Cl)(16O)'] = 4
g_ns_dict['(37Cl)(16O)'] = 4

g_ns_dict['(16O)(12C)(32S)'] = 1
g_ns_dict['(16O)(12C)(34S)'] = 1
g_ns_dict['(16O)(13C)(32S)'] = 2
g_ns_dict['(16O)(12C)(33S)'] = 4
g_ns_dict['(18O)(12C)(32S)'] = 1

g_ns_dict['H2(12C)(16O)'] = g_ns_CH2O_1
g_ns_dict['H2(13C)(16O)'] = lambda(qn_dict): 2 * g_ns_CH2O_1(qn_dict)
g_ns_dict['H2(12C)(18O)'] = g_ns_CH2O_1

g_ns_dict['H(16O)(35Cl)'] = 8
g_ns_dict['H(16O)(37Cl)'] = 8

g_ns_dict['(14N)2'] = g_ns_N2_1

g_ns_dict['H(12C)(14N)'] = 6
g_ns_dict['H(13C)(14N)'] = 12
g_ns_dict['H(12C)(15N)'] = 4

g_ns_dict['(12C)H3(35Cl)'] = g_ns_CH3Cl_1
g_ns_dict['(12C)H3(37Cl)'] = g_ns_CH3Cl_1

g_ns_dict['H2(16O)2'] = g_ns_H2O2_1

g_ns_dict['(12C)2H2'] = g_ns_C2H2_1
g_ns_dict['(12C)(13C)H2'] = 8

g_ns_dict['(31P)H3'] = g_ns_PH3_1

g_ns_dict['(12C)(16O)(19F)2'] = g_ns_CH2O_1

g_ns_dict['(12C)2H4'] = g_ns_C2H4_1
g_ns_dict['(12C)H2(13C)H2'] = g_ns_C2H4_2

g_ns_dict['(12C)H3(79Br)'] = g_ns_CH3Cl_1
g_ns_dict['(12C)H3(81Br)'] = g_ns_CH3Cl_1

g_ns_dict['H2(32S)'] = g_ns_H2O_1
g_ns_dict['H2(34S)'] = g_ns_H2O_1
g_ns_dict['H2(33S)'] = lambda(qn_dict): 4 * g_ns_H2O_1(qn_dict)

g_ns_dict['H(12C)(16O)(16O)H'] = 4

g_ns_dict['H(16O)2'] = 2

g_ns_dict['(14N)(16O)+'] = 3

g_ns_dict['H(16O)(79Br)'] = 8
g_ns_dict['H(16O)(81Br)'] = 8

g_ns_dict['(12C)H3(16O)H'] = g_ns_CH3OH_1
g_ns_dict['(12C)H3(12C)(14N)'] = g_ns_CH3CN_1

def g_ns(iso, qn_dict):
    """
    Return the nuclear spin degeneracy for the state of a given isotopologue
    with a given set of quantum numbers, or None if it couldn't be deduced.

    """

    #return g_ns_dict[iso.iso_name](qn_dict)    
    g_ns_func = g_ns_dict.get(iso.iso_name)
    # g_ns_func could be a function ...
    if callable(g_ns_func):
        return g_ns_func(qn_dict)
    # ... or a constant (or None):
    return g_ns_func

