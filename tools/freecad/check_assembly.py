# Interference check of cad/Tiller.FCStd over the steering travel.
#   "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" tools/freecad/check_assembly.py
# At each angle the handle, shaft, rotor and bearings turn by theta, the pot gear by
# -theta * z_gear / z_pot, and the roller arm and roller by the angle the cam gives.
import os
import sys
import math
import numpy as np
import FreeCAD as App

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NO_BUILD = True
src = open(os.path.join(HERE, 'build_mechanism.py'), encoding='utf-8').read()
g = {'__file__': os.path.join(HERE, 'build_mechanism.py'), 'NO_BUILD': True, '__name__': 'lib'}
exec(src, g)
L, cam, CAD = g['L'], g['cam'], g['CAD']

doc = App.openDocument(os.path.join(CAD, 'Tiller.FCStd'))
links = {o.Name: o for o in doc.Objects if o.TypeId == 'App::Link'}
for o in links.values():
    o.LinkedObject.Document.recompute()
SKIP = {'Spring'}                                  # drawn straight, it compresses in reality
TURN = {'Handle', 'Shaft', 'Rotor', 'ButtonBase', 'ButtonCap'}
ARM = {'RollerArm', 'Roller'}
# pairs that touch by design: report them separately, as contact
CONTACT = {frozenset(p) for p in [('Shaft', 'Handle'), ('Shaft', 'BearingUpper'), ('Shaft', 'BearingLower'),
                                 ('Chassis', 'BearingUpper'), ('Chassis', 'BearingLower'),
                                 ('Rotor', 'BearingLower'), ('Rotor', 'Shaft'), ('RollerArm', 'Roller'),
                                 ('RollerArm', 'Chassis'), ('Chassis', 'Deck'), ('Deck', 'Pot'),
                                 ('PotGear', 'Pot'), ('Rotor', 'PotGear'), ('Rotor', 'Roller'),
                                 ('Chassis', 'Bumper1'), ('Chassis', 'Bumper2'), ('Rotor', 'Bumper1'),
                                 ('Rotor', 'Bumper2'), ('RollerArm', 'Deck'), ('SpringCup', 'Chassis'),
                                 ('Chassis', 'StopSpacer1'), ('Chassis', 'StopSpacer2'), ('Deck', 'StopSpacer1'),
                                 ('Deck', 'StopSpacer2'), ('Bumper1', 'StopSpacer1'), ('Bumper2', 'StopSpacer2'),
                                 ('CaseShell', 'Chassis'), ('CaseShell', 'ScaleDisc'), ('CaseShell', 'CaseBottom')] +
           [('CaseBottom', 'Foot%d' % k) for k in range(1, 5)] +
           [('Handle', 'ButtonBase'), ('ButtonBase', 'ButtonCap')]}

syn = cam.synth()


def beta_at(th_deg):
    return float(np.interp(math.radians(th_deg), syn['th'], syn['beta']))


# the mechanism is drawn in its own frame and turned by mech_rot in the case
R = App.Rotation(App.Vector(0, 0, 1), L['mech_rot'])


def shapes_at(th):
    out = {}
    piv = R.multVec(App.Vector(L['pivot_x'], L['pivot_y'], 0))
    pot = R.multVec(App.Vector(L['pot_x'], 0, 0))
    for n, o in links.items():
        if n in SKIP:
            continue
        s = o.LinkedObject.Shape.copy()
        s = s.transformGeometry(o.Placement.toMatrix()) if not o.Placement.isIdentity() else s
        if n in TURN or n.startswith('Bearing'):
            s.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), th)
        elif n in ARM:
            s.rotate(piv, App.Vector(0, 0, 1), -math.degrees(beta_at(th)))
        elif n == 'PotGear':                  # the pot body stays; its shaft is round
            s.rotate(pot, App.Vector(0, 0, 1), -th * L['z_gear'] / L['z_pot'])
        out[n] = s
    return out


report = []
for th in range(-75, 76, 15):
    S = shapes_at(th)
    names = sorted(S)
    hits = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = S[a], S[b]
            if not A.BoundBox.intersect(B.BoundBox):
                continue
            v = A.common(B).Volume
            if v > 0.05:
                kind = 'contact' if frozenset((a, b)) in CONTACT else 'CLASH'
                hits.append((kind, a, b, round(v, 2)))
    # roller to cam: gap (positive) or overlap
    dist = S['Roller'].distToShape(S['Rotor'])[0]
    bump = min(S['Rotor'].distToShape(S[b])[0] for b in ('Bumper1', 'Bumper2'))
    mesh = S['Rotor'].distToShape(S['PotGear'])[0]
    print('theta %4d  beta %5.2f deg  roller-cam %.3f  lug-bumper %.2f  gear mesh %.3f'
          % (th, math.degrees(beta_at(th)), dist, bump, mesh))
    for h in hits:
        print('   ', *h)
