# Check of the PEDALS DISC button (bought self-locking switch) in its three positions.
#   "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" tools/freecad/check_button.py
# Button frame (origin on the recess axis). The cap is glued on the switch head and moves with it:
# off (+travel), latched (as drawn), pushed home (-overtravel). The switch body and pins are fixed;
# its block, neck and head move with the cap. Overlaps above 0.01 mm3 are reported.
import os
import FreeCAD as App

HERE = os.path.dirname(os.path.abspath(__file__))
g = {'__file__': os.path.join(HERE, 'build_mechanism.py'), 'NO_BUILD': True, '__name__': 'lib'}
exec(open(g['__file__'], encoding='utf-8').read(), g)
B, CAD = g['B'], g['CAD']
V = App.Vector

docs = {n: App.openDocument(os.path.join(CAD, n + '.FCStd')) for n in ('ButtonBase', 'ButtonCap', 'Handle')}
base = docs['ButtonBase'].getObject('ButtonBase').Shape
cap = docs['ButtonCap'].getObject('ButtonCap').Shape
handle = docs['Handle'].getObject('Handle').Shape.copy()
handle.translate(V(-B['x'], -B['y'], 0))
import Part


def box(cx, cy, z0, wx, wy, h):
    return Part.makeBox(wx, wy, h, V(cx - wx / 2, cy - wy / 2, z0))


# the switch from its measurements (the Switch body in ButtonBase.FCStd is the same, fused in one)
z0, top = B['sw_bot'], B['sw_bot'] + B['sw_on']
pins = [box(px * (B['sw'] / 2 - B['sw_pin_in'][0]), py * (B['sw'] / 2 - B['sw_pin_in'][1]), z0 - B['sw_pin_l'],
            0.5, 0.3, B['sw_pin_l']) for px in (-1, 0, 1) for py in (-1, 1)]
sw_fixed = box(0, 0, z0, B['sw'], B['sw'], B['sw']).multiFuse(pins)
blk = B['sw_block']
sw_move = box(0, 0, z0 + B['sw'], blk[0], blk[0], top - blk[1] - z0 - B['sw']).multiFuse([
    box(0, 0, top - blk[1], *(B['sw_neck'] if B['head_long_x'] else B['sw_neck'][::-1]), blk[1] - B['sw_head'][2]),
    box(0, 0, top - B['sw_head'][2], *(B['sw_head'][:2] if B['head_long_x'] else B['sw_head'][1::-1]),
        B['sw_head'][2])])

# contacts by design: switch body in its cup and on the ledges, the head glued in the socket
CONTACT = {frozenset(p) for p in [('ButtonBase', 'SwitchBody'), ('ButtonCap', 'SwitchHead'), ('Handle', 'ButtonBase'),
                                 ('SwitchBody', 'SwitchHead')]}
bad = 0
for name, z in (('off (up)', B['travel']), ('latched', 0.0), ('pushed home', -B['overtravel'])):
    S = {'ButtonBase': base, 'Handle': handle, 'SwitchBody': sw_fixed,
         'ButtonCap': cap.copy(), 'SwitchHead': sw_move.copy()}
    S['ButtonCap'].translate(V(0, 0, z)); S['SwitchHead'].translate(V(0, 0, z))
    out = []
    names = sorted(S)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not S[a].BoundBox.intersect(S[b].BoundBox):
                continue
            v = S[a].common(S[b]).Volume
            if v > 0.01 and frozenset((a, b)) not in CONTACT:
                out.append('%s/%s %.2f' % (a, b, v)); bad += 1
    boss_gap = S['ButtonCap'].distToShape(sw_fixed)[0]
    skirt = B['skirt_bot'] + z - B['floor'] - B['disc_t']
    sleeve = B['sleeve_bot'] + z - B['floor'] - B['disc_t']
    guide = B['sw_bot'] + B['cup_h'] - B['sleeve_bot'] - z
    ped_gap = S['ButtonCap'].distToShape(base)[0]
    print('%-12s cap %+5.2f  cap to switch body %.2f  skirt / sleeve above the disc %.2f / %.2f  sleeve on the '
          'pedestal %.2f  cap to base %.2f  %s'
          % (name, z, boss_gap, skirt, sleeve, guide, ped_gap, ' '.join(out) or 'ok'))
print('overlaps:', bad)
# the designed contacts must be touching, not overlapping
print('switch body and pins into the base %.3f mm3, head into the cap %.3f mm3' % (
    base.common(sw_fixed).Volume, cap.common(sw_move).Volume))
