# Builds the tiller mechanism part files and the linked assembly (cad/*.FCStd).
#
# Run with FreeCAD's command line:
#   "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" tools/freecad/build_mechanism.py
#
# Assembly frame (docs/assembly.md): Z up along the steering axis, axis at X = Y = 0,
# Z = 0 on the top face of the case. Every part is drawn in this frame, except the
# handle (its own frame, linked at Z = HANDLE_Z) and the hardware (own axes).
# Each part file has a Params spreadsheet; the values below seed it.
import os
import sys
import math
import numpy as np
import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fcb
import cam
V = App.Vector

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CAD = os.path.join(ROOT, 'cad')
FONT = os.path.join(CAD, 'fonts', 'OpenBus.ttf').replace('\\', '/')    # as the glareshield legends

# ---------------------------------------------------------------- shared layout
L = dict(
    case_t=3.0,          # case top, Z 0 ... -3
    disc_t=3.0,          # scale disc on the case top, Z 0 ... +3
    handle_z=4.0,        # handle mounting face
    # bearings 6001Z
    brg_D=28.0, brg_d=12.0, brg_B=8.0,
    brg1_top=-3.5,       # upper bearing, top face
    brg2_top=-35.5,      # lower bearing, top face
    # shaft
    shaft_d=12.00,       # in the 6001 bores (measured 11.94): prints ~0.2 small; 11.85 and 11.95 too loose, 12.05 does not go in
    bore_d=7.0,          # wire channel
    flange_d=30.0, flange_t=4.0,
    shoulder_d=15.5, shoulder_h=2.0,   # rests on the upper inner race only
    shaft_end=-67.0,
    flat=5.0,            # D flat, distance from the axis
    flat_top=-44.0,
    screw_r=11.0,        # 3 x M3 handle screws
    # tower and chassis
    seat_d=28.15,        # bearing seats: FitTest 2026-11-01
    tower_od=36.0, tower_mid_d=22.0,
    plate_t=7.0,         # chassis plate, Z -3 ... -10
    deck_top=-70.0, deck_t=5.0,   # 5 (was 4 plus a 1 mm pot boss under it, 2026-11-06): flat bottom on the bed
    # rotor (cam + stop lug + gear)
    rotor_top=-43.5,
    cam_top=-45.0, cam_bot=-54.0,
    gear_top=-55.0, gear_bot=-61.0,
    hub_bot=-67.0, hub_d=24.0,
    rotor_bore=12.15, rotor_flat=5.1,
    lug_r_in=10.0, lug_r_out=40.0, lug_w=8.0,   # lug_r_in inside the cam back arc: one solid
    z_gear=36, z_pot=24, module=1.0,   # 36 : 24 -> the pot turns 225 deg for +-75
    # arm and roller 608ZZ
    pivot_x=31.0, pivot_y=-35.0,
    pin_d=10.0, arm_bore=10.3, arm_hub_d=18.0,
    arm_top=-41.5, arm_beam_bot=-44.5, arm_bot=-52.5,
    arm_w=10.0, tip_y=18.0,
    roller_D=22.0, roller_d=8.0, roller_B=7.0, roller_top=-45.3,
    roller_pin_d=7.95, pin_shoulder_d=10.0,
    # spring
    # the spring in hand (2026-11-09): wire 1.05, OD 9.96, ID 7.8, free 40.3, 7 active coils, closed ends;
    # 2.5 kg at 25 mm long -> k 1.6. Preloaded to 30.0 (16.5 N), 21.65 at the stops (29.9 N)
    spring_z=-47.0, spring_od=10.0, spring_id=7.8, spring_L0=40.3, spring_k=1.6,
    spring_preload=10.3,
    cup_t=5.0, cup_socket_d=3.4, cup_socket_l=2.0,   # SpringCup; the screw tip sits in the socket
    # (user 2026-11-08: 5 thick, 3 solid under the tip, PETG 100 % infill)
    spigot_l=4.0,
    spring_post_x=80.0, spring_post_d=16.0,   # M3 preload screw through the post, nut trapped in its front face
    # stops
    stop_r=36.0, bumper_d=14.0, stop_post_d=10.0, th_max=75.0,
    # potentiometer B10K in hand (measured 2026-11-04): M7 bushing 6.75 x 6.5, knurled split shaft
    # 5.83 over the knurls (5.6 first read; 5.82-5.83 measured 2026-11-06) x 13.3 above the bushing, slot 1.1-1.2 x 11; frame 17.25 (Y) x 10.9 (X),
    # 9 from the frame top to the can bottom; pins (pitch 4) to -X, 4.5-5 under the frame top, 5 out
    # of the small board; anti-rotation tab at +Y, 1.3 radial x 2.3, inner edge 4 from the thread
    pot_x=-30.0, pot_body_d=16.8, pot_body_h=9.0, pot_bush_d=6.75, pot_bush_h=6.5,
    pot_shaft_d=5.83, pot_shaft_l=13.3, pot_frame_x=10.9, pot_frame_y=17.25,
    pot_tab_r=8.05, pot_tab_x=2.3, pot_tab_y=1.3, pot_tab_h=2.0,
    pot_nut_d=12.5, pot_nut_depth=1.5,   # recess on the deck top for washer 11.35 and nut 9.9 x 2
    # inserts: M3 heat-set, pilot drawn oversize (holes print 0.15-0.2 small on the P1S)
    ins_d=3.9, ins_l=6.0,     # FitTest 2026-11-01 (PETG)
    ins_d_pla=4.0,            # case parts in PLA: FitTestPLA 2026-11-01
    board_gap=23.0,           # RP2040 cradle rails, board 22.85: FitTestPLA 2026-11-01
    case_screw=25.0,     # chassis to case top, 4 at (+-25, +-25) in the mechanism frame
    # case (PLA): drawn in the case frame; the mechanism is turned by mech_rot about Z inside it
    mech_rot=34.0,       # the spring end goes to the back-right corner; shaft and handle are not turned
    case_in=157.0, case_wall=3.0, case_r=6.0,   # inner square side, wall, outer corner radius
    case_h=93.0,         # shell from Z 0 down to -93 (pot pins end at -88)
    bottom_t=3.0,
    col_d=8.0, col_c=74.5,                      # corner columns, M3 inserts for the bottom
    top_hole=18.0,       # shaft shoulder (15.5) through the case top and the scale disc
    disc_d=110.0,        # scale disc (was 92: the numbers go outside the screw heads)
    csk_d=6.9,           # countersink for M3 ISO 10642
    foot_d=16.0, foot_t=4.0, foot_c=62.0,       # TPU feet, 1 mm in a recess
    # RP2040 cradle: board along Y, USB-C through the back wall (+Y)
    cradle_x=-55.0, board_l=53.3, board_w=22.85, board_t=1.6,
    rib_h=8.0,           # board bottom above the floor: solder joints under the long edges
    usb_w=15.0, usb_h=8.0,                      # wall window for the plug overmold
)
# PEDALS DISC push-push button, in the handle recess. Button frame: origin on the recess axis,
# Z as in the handle frame; drawn latched (cap top flush with the handle top).
B = dict(
    x=-2.79, y=6.86,          # recess axis in the handle frame
    floor=12.8,               # recess floor (was 20): 2.6 above the flange inserts
    top=31.4, travel=5.0,     # cap top latched (flush) and how much higher it stands up
    cap_d=29.5, cap_t=2.0, band=5.5,     # band: the wide top ring; 5.5 (was 2.5, user 2026-11-05) hides the gap in the recess
    skirt_r=(11.8, 13.2),
    disc_d=30.2, disc_t=1.5,
    spigot_d=7.0, well_d=5.2, spigot_bot=11.2, well_floor=0.8,
    pin_d=3.0, pin_top=25.0,
    tube_r=(2.6, 4.0),
    collar_r=(13.9, 15.1),
    # PEDAL DISC legend on the cap face, flush inlay leg_t deep (two 0.2 layers: the cap prints
    # face down). Letters leg_cap high, leg_track apart, their mid-height on two arcs of radius
    # leg_R through (0, +-leg_y): PEDAL bowed up, DISC bowed down. Reads from the seat (+Y up),
    # turned by leg_rot (deg, counter-clockwise from +Z).
    leg_t=0.4, leg_cap=5.0, leg_track=0.55, leg_y=10.5, leg_R=10.5, leg_rot=0.0,
)
LEGEND = (('PEDAL', 1), ('DISC', -1))     # word, +1 upper arc / -1 lower arc
LINK_TARGET = {'ButtonCap': 'ButtonCapAssembly',     # part files whose Tiller link is not the body
               'ButtonBase': 'ButtonBaseAssembly',
               'ScaleDisc': 'ScaleDiscAssembly'}
NO_STL = ('Switch', 'Bearing6001', 'Bearing608', 'Spring', 'Pot')   # bodies that stand for bought parts
GONE_LINKS = ('ButtonRotor', 'ButtonPen')             # Tiller links of parts no longer drawn
# Latch: a bought 7 x 7 self-locking switch (G-Switch, the user's), 2026-11-04. The printed pen rotor,
# the heart cam and the click-pen mechanism are gone (a pen long enough to latch does not fit the
# hub). The switch body sits in a square cup on a solid pedestal in the middle of the base; its pins
# and the solder joints are potted in the well under it (they are thin PCB pins: nothing may pull on
# them); the cap is glued on the switch head and moves with it. Measured by the user: body 7 x 7 x 7,
# 12.5 high off, 11.4 latched, 10.65 pushed home; head 3 x 2 x 1 on a 2.5 x 1.5 neck; 6 pins, about
# 3.7 long (from the photos), 0.9 in from the body edge on one side, 1.4 on the other.
B.update(
    skirt_bot=17.773, collar_top=24.373,
    sw=7.0, sw_off=12.5, sw_on=11.4, sw_push=10.65,       # switch body side, height off / latched / home
    sw_head=(3.0, 2.0, 1.0), sw_neck=(2.5, 1.5), sw_block=(4.0, 2.8),   # block: side, its top below the head top
    sw_pin_l=3.7, sw_pin_in=(1.4, 0.9),                   # pins: length; inset from the edge along X, along Y
    cup_wall=1.8, cup_h=4.0, cup_clear=0.15,              # square cup round the switch body
    socket=(3.2, 2.2), socket_in=1.0, socket_depth=2.5,   # head socket under the cap (into the plate socket_in)
    head_long_x=True,             # head long side along X (the pin rows); 2026-11-04, user: turned 90 deg so the
                                  # legend reads right with the switch as fitted (was along Y)
    boss_d=6.0,
    sleeve_clear=0.2, sleeve_wall=1.6, sleeve_bot=15.5,   # square sleeve under the cap round the base pedestal:
                                                          # the up-down guide (user 2026-11-05: the cap wobbled)
    wire_w=3.6, wire_depth=1.8,   # groove for the two wires (24 AWG silicone, ~1.5 outside) to the wire bore
    well_extra=1.8,               # the well goes on into the handle floor: 8.0 under the switch body for
                                  # pins, joints and the bend of the wires into the groove (0.8 above the insert)
)
B['travel'] = B['sw_off'] - B['sw_on']                 # how much higher the cap stands with the switch off
B['overtravel'] = B['sw_on'] - B['sw_push']
B['sw_bot'] = B['top'] - B['cap_t'] + B['socket_in'] - B['sw_on']     # switch body bottom (fixed)
B['boss_h'] = B['socket_depth'] - B['socket_in']
# the boss under the cap stays clear of the switch's own wide block, which moves with the head
assert B['sw_block'][1] - B['socket_depth'] >= 0.3 - 1e-9
assert B['skirt_bot'] - B['overtravel'] - (B['floor'] + B['disc_t']) >= 0.3
assert B['top'] - B['band'] - B['overtravel'] - B['collar_top'] >= 0.5     # band clear of the collar, pushed home
B['ped'] = B['sw'] + 2 * B['cup_clear'] + 2 * B['cup_wall']           # base pedestal side (10.9)
B['sleeve_in'] = B['ped'] + 2 * B['sleeve_clear']
B['sleeve_out'] = B['sleeve_in'] + 2 * B['sleeve_wall']
assert B['sleeve_bot'] - B['overtravel'] - (B['floor'] + B['disc_t']) >= 0.3
assert B['sleeve_out'] / 2 * 2 ** 0.5 <= B['skirt_r'][0] - 1.0         # sleeve corners clear of the skirt
cam.P['TH_PROFILE'] = 78.0          # the cam ends just past the stops
cam.P['RP0'] = L['pivot_x']
cam.P['ARM_ROLLER'] = -L['pivot_y']
cam.P['ARM_TIP'] = L['tip_y'] - L['pivot_y']
cam.P['R_ROLLER'] = L['roller_D'] / 2
cam.P['K'] = L['spring_k']
cam.P['F0'] = L['spring_k'] * L['spring_preload']
# cup back 1 mm short of the spring post front face, screw tip in the range the M3 x 25 covers
_cup_x0 = L['pivot_x'] + L['arm_w'] / 2 + L['spring_L0'] - L['spring_preload']
assert L['spring_post_x'] - L['spring_post_d'] / 2 - (_cup_x0 + L['cup_t']) >= 1.0 - 1e-9
assert 66.0 <= _cup_x0 + L['cup_t'] - L['cup_socket_l'] <= 71.0


def params(*keys, extra=()):
    return [(k, L[k], '') for k in keys] + list(extra)


def pitch_r(z):
    return L['module'] * z / 2


CENTRE_DIST = pitch_r(L['z_gear']) + pitch_r(L['z_pot'])   # 28 with 36 : 20


def stop_posts():
    """Centres of the two stop posts: the bumper touches the lug at +-th_max."""
    w, r0, r1 = L['lug_w'] / 2, L['lug_r_in'], L['lug_r_out']
    lug = [(-r0, -w), (-r1, -w), (-r1, w), (-r0, w)]
    rb = L['bumper_d'] / 2
    out = []
    for sgn in (1, -1):
        th = math.radians(sgn * L['th_max'])
        c, s = math.cos(th), math.sin(th)
        poly = [(c * x - s * y, s * x + c * y) for x, y in lug]
        best = None
        base = math.radians(180 + sgn * L['th_max'])   # lug centre line
        for k in range(1, 4000):
            a = base + sgn * math.radians(k * 0.01)
            p = (L['stop_r'] * math.cos(a), L['stop_r'] * math.sin(a))
            d = min(_seg_dist(p, poly[i], poly[(i + 1) % 4]) for i in range(4))
            if d >= rb:
                best = p; break
        out.append(best)
    return out


def _seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


STOPS = stop_posts()


# ---------------------------------------------------------------- parts
# Each part is a PartDesign Body named like its file, built from constrained sketches.
# XY sketches sit at a Z offset; pads grow up and pockets cut down unless reversed.
# YZ sketches (features along X) use sketch x = Y, sketch y = Z.
def polar(r_alias, angle):
    return ('%s * cos(%gdeg)' % (r_alias, angle), '%s * sin(%gdeg)' % (r_alias, angle))


ROT_C, ROT_S = 'cos($mech_rot * 1 deg)', 'sin($mech_rot * 1 deg)'


def to_mech(x, y):
    """Case-frame point (expressions) in the mechanism frame: turned by -mech_rot."""
    return ('(%s) * %s + (%s) * %s' % (x, ROT_C, y, ROT_S), '-(%s) * %s + (%s) * %s' % (x, ROT_S, y, ROT_C))


def to_case(x, y):
    """Mechanism-frame point (expressions) in the case frame: turned by +mech_rot."""
    return ('(%s) * %s - (%s) * %s' % (x, ROT_C, y, ROT_S), '(%s) * %s + (%s) * %s' % (x, ROT_S, y, ROT_C))


def case_square(half):
    """Corners of the case square of half-side `half`, in the mechanism frame."""
    return [to_mech('%s%s' % (sx, half), '%s%s' % (sy, half)) for sx, sy in (('', ''), ('-', ''), ('-', '-'), ('', '-'))]


def trim_to_case(d, z):
    """Cut everything outside the case (1 mm clearance) from the sketch plane down."""
    s = d.sketch('CaseTrimSketch', z)
    s.rect(-200, -200, 400, 400)
    s.polygon(case_square('($case_in / 2 - 1)'))
    d.pocket('CaseTrim', s, through=True)


CRADLE_ZONE = [('-$case_in', '$case_in / 2 - 0.9 - $board_l - 5'), ('$cradle_x + 17', '$case_in / 2 - 0.9 - $board_l - 5'),
               ('$cradle_x + 17', '$case_in'), ('-$case_in', '$case_in')]     # case frame: cradle + 3 mm


def post_points():
    """Deck screw points shared by the chassis posts and the deck: pivot, stops, spring post."""
    return [('$pivot_x', '$pivot_y'), ('$stop_x', '$stop_y'), ('$stop_x', '-$stop_y'), ('$spring_post_x', '$tip_y')]


STOP_PARAMS = [('stop_x', round(STOPS[0][0], 3), 'stop post centre, from the lug and bumper geometry'),
               ('stop_y', round(abs(STOPS[0][1]), 3), 'stop posts at +-stop_y')]
PLATE_PARAMS = [('plate_x0', -44.0, 'chassis and deck outline, trimmed to the case'), ('plate_y0', -46.0, ''),
                ('plate_l', 134.0, ''), ('plate_w', 88.0, '')]


def build_shaft():
    d = fcb.PDoc('Shaft', params('shaft_d', 'bore_d', 'flange_d', 'flange_t', 'shoulder_d', 'shoulder_h',
                                 'shaft_end', 'flat', 'flat_top', 'screw_r', 'handle_z', 'brg1_top',
                                 extra=[('screw_hole', 3.4, 'M3 clearance'),
                                        ('csk_d', 6.9, 'countersink for M3 ISO 10642 (head 6.72 max)'),
                                        ('shoulder_land', 0.5, 'straight part of the shoulder, then a 45 deg '
                                                               'cone so it prints flange down without supports')]))
    d.body('Shaft')
    s = d.sketch('ShaftSketch', '$shaft_end'); s.circle(0, 0, '$shaft_d')
    d.pad('ShaftPad', s, '$handle_z - $shaft_end')
    s = d.sketch('FlangeSketch', '$handle_z'); s.circle(0, 0, '$flange_d')
    d.pad('Flange', s, '$flange_t')
    s = d.sketch('ShoulderSketch', '$brg1_top'); s.circle(0, 0, '$shoulder_d')
    d.pad('Shoulder', s, '$shoulder_land')
    s = d.sketch('ShoulderConeSketch', '$brg1_top + $shoulder_land'); s.circle(0, 0, '$shoulder_d')
    cone = d.pad('ShoulderCone', s, '$shoulder_h - $shoulder_land')
    cone.TaperAngle = -45
    s = d.sketch('BoreSketch', '$handle_z + $flange_t'); s.circle(0, 0, '$bore_d')
    d.pocket('Bore', s, through=True)
    s = d.sketch('FlatSketch', '$flat_top'); s.rect('$flat', -10, 10, 20)
    d.pocket('Flat', s, through=True)
    # countersunk from below: the heads stay inside the flange, clear of the scale disc
    s = d.sketch('ScrewSketch', '$handle_z')
    for a in (90, 210, 330):
        s.circle(*polar('$screw_r', a), '$screw_hole')
    d.hole('ScrewHoles', s, '$screw_hole', '$flange_t', csk_d='$csk_d', reversed=True)
    return d.save(os.path.join(CAD, 'Shaft.FCStd'))


def build_chassis():
    d = fcb.PDoc('Chassis', params('case_t', 'plate_t', 'tower_od', 'tower_mid_d', 'seat_d', 'brg1_top',
                                   'brg2_top', 'brg_B', 'deck_top', 'pin_d', 'stop_post_d', 'spring_post_d',
                                   'spring_post_x', 'pivot_x', 'pivot_y', 'tip_y', 'spring_z', 'ins_d', 'ins_l',
                                   'case_screw', 'arm_top', 'mech_rot', 'case_in',
                                   extra=PLATE_PARAMS + STOP_PARAMS +
                                   [('nut_af', 5.8, 'M3 nut trap, across flats (nut 5.5)'),
                                    ('nut_t', 2.8, 'M3 nut trap depth from the post face (nut 2.4)'),
                                    ('screw_hole', 3.4, 'M3 clearance'),
                                    ('pivot_collar_d', 14.0, 'post above the arm hub')]))
    d.body('Chassis')
    s = d.sketch('PlateSketch', '-$case_t - $plate_t'); s.rect('$plate_x0', '$plate_y0', '$plate_l', '$plate_w')
    d.pad('Plate', s, '$plate_t')
    s = d.sketch('TowerSketch', '$brg2_top - $brg_B'); s.circle(0, 0, '$tower_od')
    d.pad('Tower', s, '-$case_t - ($brg2_top - $brg_B)')
    s = d.sketch('PivotCollarSketch', '$arm_top'); s.circle('$pivot_x', '$pivot_y', '$pivot_collar_d')
    d.pad('PivotCollar', s, '-$case_t - $arm_top')
    s = d.sketch('PivotPinSketch', '$deck_top'); s.circle('$pivot_x', '$pivot_y', '$pin_d')
    d.pad('PivotPin', s, '$arm_top - $deck_top')
    s = d.sketch('PostsSketch', '$deck_top')
    s.circle('$stop_x', '$stop_y', '$stop_post_d'); s.circle('$stop_x', '-$stop_y', '$stop_post_d')
    s.circle('$spring_post_x', '$tip_y', '$spring_post_d')
    d.pad('Posts', s, '-$case_t - $deck_top')
    s = d.sketch('SeatUpperSketch', '-$case_t'); s.circle(0, 0, '$seat_d')
    d.pocket('SeatUpper', s, '-$case_t - $brg1_top + $brg_B')
    s = d.sketch('MidBoreSketch', '-$case_t'); s.circle(0, 0, '$tower_mid_d')
    d.pocket('MidBore', s, through=True)
    s = d.sketch('SeatLowerSketch', '$brg2_top - $brg_B'); s.circle(0, 0, '$seat_d')
    d.pocket('SeatLower', s, '$brg_B', reversed=True)
    s = d.sketch('CaseInsertSketch', '-$case_t')
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        s.circle('%s$case_screw' % ('' if sx > 0 else '-'), '%s$case_screw' % ('' if sy > 0 else '-'), '$ins_d')
    d.pocket('CaseInserts', s, '$ins_l')
    s = d.sketch('DeckInsertSketch', '$deck_top')
    for px, py in post_points():
        s.circle(px, py, '$ins_d')
    d.pocket('DeckInserts', s, '$ins_l', reversed=True)
    # spring preload: an M3 from the back of the spring post (lock nut against the back face) through
    # a nut trapped in the front face; the spring pushes that nut into the bottom of its trap.
    # Hex with a corner up: its top prints as a 60 deg roof, no support
    s = d.sketch('SpringScrewSketch', '$spring_post_x - $spring_post_d / 2 - 1', plane='YZ')
    s.circle('$tip_y', '$spring_z', '$screw_hole')
    d.pocket('SpringScrew', s, '$spring_post_d + 2', reversed=True)
    s = d.sketch('SpringNutSketch', '$spring_post_x - $spring_post_d / 2 - 1', plane='YZ')
    s.polygon([('$tip_y + %.6f * $nut_af' % (math.cos(math.radians(90 + 60 * k)) / 3 ** 0.5),
                '$spring_z + %.6f * $nut_af' % (math.sin(math.radians(90 + 60 * k)) / 3 ** 0.5)) for k in range(6)])
    d.pocket('SpringNutTrap', s, '$nut_t + 1', reversed=True)
    trim_to_case(d, '-$case_t')
    return d.save(os.path.join(CAD, 'Chassis.FCStd'))


def cam_sketch(s):
    """Cam profile from cam.synth (a locked B-spline) closed by an arc behind it, inside the hub."""
    r = cam.synth()
    prof = r['prof']
    idx = np.linspace(0, len(prof) - 1, 161).round().astype(int)
    pts = [V(float(x), float(y), 0) for x, y in prof[idx]]
    bs = Part.BSplineCurve(); bs.interpolate(pts)
    rh = L['hub_d'] / 2 - 0.5
    a0 = math.atan2(pts[0].y, pts[0].x); a1 = math.atan2(pts[-1].y, pts[-1].x)
    p_start = V(rh * math.cos(a0), rh * math.sin(a0), 0); p_end = V(rh * math.cos(a1), rh * math.sin(a1), 0)
    # counter-clockwise from the profile start (about +84 deg) through 180 to its end (about -85 deg);
    # a clockwise arc gets its vertices swapped by the sketcher solver
    arc = Part.ArcOfCircle(Part.Circle(V(0, 0, 0), V(0, 0, 1), rh), a0, a1 + 2 * math.pi)
    sk = s.sk
    gb = sk.addGeometry(bs)
    sk.addConstraint(fcb.Sketcher.Constraint('Block', gb))
    ga = sk.addGeometry(arc)
    a_end = 2                                                         # arc vertex at the profile end
    l1 = sk.addGeometry(Part.LineSegment(pts[-1], p_end))
    l2 = sk.addGeometry(Part.LineSegment(p_start, pts[0]))
    for c in (('Coincident', l1, 1, gb, 2), ('Coincident', l1, 2, ga, a_end),
              ('Coincident', l2, 1, ga, 3 - a_end), ('Coincident', l2, 2, gb, 1),
              ('Coincident', ga, 3, fcb.ROOT, 1),
              ('PointOnObject', fcb.ROOT, 1, l1), ('PointOnObject', fcb.ROOT, 1, l2)):  # radial closing lines
        sk.addConstraint(fcb.Sketcher.Constraint(*c))
    s._c(fcb.Sketcher.Constraint('Radius', ga, rh), '$hub_d / 2 - 0.5')
    return r


def build_rotor():
    import InvoluteGearFeature
    d = fcb.PDoc('Rotor', params('rotor_top', 'cam_top', 'cam_bot', 'gear_top', 'gear_bot', 'hub_bot', 'hub_d',
                                 'rotor_bore', 'rotor_flat', 'flat_top', 'lug_r_in', 'lug_r_out', 'lug_w',
                                 'shoulder_d', 'mech_rot',
                                 extra=[('z_gear', L['z_gear'], 'teeth'), ('module', L['module'], 'mm'),
                                        ('screw_hole', 3.4, 'M3 clearance for the grub screw'),
                                        ('nut_af', 5.8, 'M3 nut trap, across flats (nut 5.5)'),
                                        ('nut_slot_t', 2.7, 'nut trap thickness (nut 2.4)'),
                                        ('nut_r', 8.5, 'nut trap centre from the axis: 2.0 to the flat, '
                                                       '2.1 to the hub side')]))
    d.body('Rotor')
    s = d.sketch('CamSketch', '$cam_bot'); cam_sketch(s)
    d.pad('Cam', s, '$cam_top - $cam_bot')
    s = d.sketch('StopLugSketch', '$cam_bot'); s.rect('-$lug_r_out', '-$lug_w / 2', '$lug_r_out - $lug_r_in', '$lug_w')
    d.pad('StopLug', s, '$cam_top - $cam_bot')
    s = d.sketch('BossSketch', '$cam_top'); s.circle(0, 0, '$shoulder_d')
    d.pad('Boss', s, '$rotor_top - $cam_top')
    s = d.sketch('WebSketch', '$gear_top'); s.circle(0, 0, '$hub_d')
    d.pad('Web', s, '$cam_bot - $gear_top')
    g = InvoluteGearFeature.makeInvoluteGear('GearProfile')
    d.b.addObject(g)
    g.AttachmentSupport = [(d.planes['XY_Plane'], '')]; g.MapMode = 'FlatFace'
    g.setExpression('.AttachmentOffset.Base.z', 'Params.gear_bot')
    g.setExpression('NumberOfTeeth', 'Params.z_gear'); g.setExpression('Modules', 'Params.module * 1 mm')
    d.pad('Gear', g, '$gear_top - $gear_bot')
    s = d.sketch('HubSketch', '$hub_bot'); s.circle(0, 0, '$hub_d')
    d.pad('Hub', s, '$gear_bot - $hub_bot')
    s = d.sketch('BoreSketch', '$rotor_top'); s.circle(0, 0, '$rotor_bore')
    d.pocket('Bore', s, '$rotor_top - $flat_top')
    # the D bore and the grub screw are turned by -mech_rot: the rotor sits turned by +mech_rot in the
    # case, the shaft does not, so its flat (and the handle) stay where they were
    s = d.sketch('DBoreSketch', '$flat_top'); s.dshape(0, 0, '$rotor_bore', '$rotor_flat')
    s.sk.setExpression('.AttachmentOffset.Rotation.Angle', '-Params.mech_rot * 1 deg')
    d.pocket('DBore', s, through=True)
    # grub screw: M3 x 5 through a nut trapped in the hub (the slot opens on the hub bottom, the nut
    # goes in from there); its tip on the flat leaves the whole grub in the nut, 1.9 under the hub side
    s = d.sketch('GrubSketch', 0, plane='YZ'); s.circle(0, '($gear_bot + $hub_bot) / 2', '$screw_hole')
    pl = s.sk.AttachmentOffset; pl.Rotation = App.Rotation(V(0, 1, 0), -L['mech_rot']); s.sk.AttachmentOffset = pl
    s.sk.setExpression('.AttachmentOffset.Rotation.Angle', '-Params.mech_rot * 1 deg')
    s.sk.setExpression('.AttachmentOffset.Base.x', '(Params.rotor_flat - 0.5) * sin(-Params.mech_rot * 1 deg)')
    s.sk.setExpression('.AttachmentOffset.Base.z', '(Params.rotor_flat - 0.5) * cos(-Params.mech_rot * 1 deg)')
    d.pocket('GrubHole', s, '$hub_d / 2 - $rotor_flat + 0.5', reversed=True)
    s = d.sketch('GrubNutSketch', '$hub_bot')
    s.rect('$nut_r - $nut_slot_t / 2', '-$nut_af / 2', '$nut_slot_t', '$nut_af')
    s.sk.setExpression('.AttachmentOffset.Rotation.Angle', '-Params.mech_rot * 1 deg')
    d.pocket('GrubNutTrap', s, '($gear_bot - $hub_bot) / 2 + $nut_af / 2', reversed=True)
    return d.save(os.path.join(CAD, 'Rotor.FCStd'))


def build_arm():
    d = fcb.PDoc('RollerArm', params('pivot_x', 'pivot_y', 'arm_bore', 'arm_hub_d', 'arm_top', 'arm_beam_bot',
                                     'arm_bot', 'arm_w', 'tip_y', 'roller_top', 'roller_B', 'roller_pin_d',
                                     'pin_shoulder_d', 'spring_z', 'spring_id', 'spigot_l',
                                     extra=[('pin_hole', 2.6, 'an M3 x 8 cuts its own thread (prints about 2.45)'),
                                            ('pin_hole_l', 8.5, 'M3 x 8 through a 0.8 washer, 1.3 to spare')]))
    d.body('RollerArm')
    s = d.sketch('HubSketch', '$arm_bot'); s.circle('$pivot_x', '$pivot_y', '$arm_hub_d')
    d.pad('Hub', s, '$arm_top - $arm_bot')
    s = d.sketch('BeamSketch', '$arm_beam_bot')
    s.rect('$pivot_x - $arm_w / 2', '$pivot_y', '$arm_w', '$tip_y + 5 - $pivot_y')
    d.pad('Beam', s, '$arm_top - $arm_beam_bot')
    s = d.sketch('TipSketch', '$arm_bot'); s.rect('$pivot_x - $arm_w / 2', '$tip_y - 5', '$arm_w', 10)
    d.pad('Tip', s, '$arm_top - $arm_bot')
    s = d.sketch('SpigotSketch', '$pivot_x + $arm_w / 2', plane='YZ'); s.circle('$tip_y', '$spring_z', '$spring_id - 0.5')
    d.pad('Spigot', s, '$spigot_l')
    s = d.sketch('PinShoulderSketch', '$roller_top'); s.circle('$pivot_x', 0, '$pin_shoulder_d')
    d.pad('PinShoulder', s, '$arm_beam_bot - $roller_top')
    s = d.sketch('RollerPinSketch', '$roller_top - $roller_B'); s.circle('$pivot_x', 0, '$roller_pin_d')
    d.pad('RollerPin', s, '$roller_B')
    s = d.sketch('PivotBoreSketch', '$arm_top'); s.circle('$pivot_x', '$pivot_y', '$arm_bore')
    d.pocket('PivotBore', s, through=True)
    s = d.sketch('PinHoleSketch', '$roller_top - $roller_B'); s.circle('$pivot_x', 0, '$pin_hole')
    d.pocket('PinHole', s, '$pin_hole_l', reversed=True)
    return d.save(os.path.join(CAD, 'RollerArm.FCStd'))


def build_deck():
    d = fcb.PDoc('Deck', params('deck_top', 'deck_t', 'arm_bot', 'arm_bore', 'pot_x', 'pot_bush_d', 'pivot_x',
                                'pot_frame_x', 'pot_frame_y', 'pot_tab_r', 'pot_tab_x', 'pot_tab_y', 'pot_tab_h',
                                'pot_nut_d', 'pot_nut_depth',
                                'pivot_y', 'spring_post_x', 'tip_y', 'mech_rot', 'case_in', 'cradle_x', 'board_l',
                                extra=PLATE_PARAMS + STOP_PARAMS +
                                [('boss_d', 14.0, 'spacer under the arm hub'), ('screw_hole', 3.4, 'M3'),
                                 ('head_d', 6.0, 'M3 head counterbore'), ('head_h', 4.2, '0.8 of deck under the head'),
                                 ('wire_hole', 30.0, 'wires out of the shaft'),
                                 ('pot_slot', 3.0, 'mesh adjustment along X')]))
    d.body('Deck')
    s = d.sketch('PlateSketch', '$deck_top - $deck_t'); s.rect('$plate_x0', '$plate_y0', '$plate_l', '$plate_w')
    d.pad('Plate', s, '$deck_t')
    s = d.sketch('PivotBossSketch', '$deck_top'); s.circle('$pivot_x', '$pivot_y', '$boss_d')
    d.pad('PivotBoss', s, '$arm_bot - 0.1 - $deck_top')
    s = d.sketch('WireHoleSketch', '$deck_top'); s.circle(0, 0, '$wire_hole')
    d.pocket('WireHole', s, through=True)
    s = d.sketch('PivotPinHoleSketch', '$deck_top'); s.circle('$pivot_x', '$pivot_y', '$arm_bore')
    d.pocket('PivotPinHole', s, 20, reversed=True)
    s = d.sketch('ScrewSketch', '$deck_top')
    for px, py in post_points():
        s.circle(px, py, '$screw_hole')
    d.pocket('ScrewHoles', s, through=True)
    s = d.sketch('CounterboreSketch', '$deck_top - $deck_t')
    for px, py in post_points():
        s.circle(px, py, '$head_d')
    d.pocket('Counterbores', s, '$head_h', reversed=True)
    # potentiometer: its frame on the deck bottom (5 thick: the shaft top 0.2 under the gear top), bushing
    # slot, a slot for the anti-rotation tab, washer and nut in a recess on the top (more thread for the nut)
    s = d.sketch('PotSlotSketch', '$deck_top')
    s.slot('$pot_x - $pot_slot / 2', '$pot_x + $pot_slot / 2', 0, '$pot_bush_d + 0.3')
    d.pocket('PotSlot', s, through=True)
    s = d.sketch('PotNutSketch', '$deck_top')
    s.slot('$pot_x - $pot_slot / 2', '$pot_x + $pot_slot / 2', 0, '$pot_nut_d')
    d.pocket('PotNutRecess', s, '$pot_nut_depth')
    s = d.sketch('PotTabSketch', '$deck_top - $deck_t')
    s.rect('$pot_x - $pot_slot / 2 - $pot_tab_x / 2 - 0.2', '$pot_tab_r - $pot_tab_y / 2 - 0.2',
           '$pot_tab_x + $pot_slot + 0.4', '$pot_tab_y + 0.4')
    d.pocket('PotTabSlot', s, '$pot_tab_h + 1', reversed=True)
    trim_to_case(d, '$deck_top')
    s = d.sketch('CradleClearSketch', '$deck_top')         # room for the RP2040 and its wires
    s.polygon([to_mech(x, y) for x, y in CRADLE_ZONE])
    d.pocket('CradleClear', s, through=True)
    return d.save(os.path.join(CAD, 'Deck.FCStd'))


def build_potgear():
    import InvoluteGearFeature
    d = fcb.PDoc('PotGear', params('gear_top', 'gear_bot', 'pot_shaft_d', 'pot_x', 'ins_d',
                                   extra=[('z_pot', L['z_pot'], 'teeth'), ('module', L['module'], 'mm'),
                                          ('hub_bot', -67.0, '2.1 over the pot nut'), ('hub_d', 12.0, ''),
                                          ('bore_clear', 0.2, 'drawn 6.03, prints about 5.83: the knurls bite '
                                           '(PETG holes print ~0.2 small: 5.6 drawn came out 5.4, 2026-11-06)')]))
    d.body('PotGear')
    g = InvoluteGearFeature.makeInvoluteGear('GearProfile')
    d.b.addObject(g)
    g.AttachmentSupport = [(d.planes['XY_Plane'], '')]; g.MapMode = 'FlatFace'
    g.AttachmentOffset = App.Placement(V(L['pot_x'], 0, L['gear_bot']), App.Rotation(V(0, 0, 1), 180.0 / L['z_pot']))
    g.setExpression('.AttachmentOffset.Base.x', 'Params.pot_x')
    g.setExpression('.AttachmentOffset.Base.z', 'Params.gear_bot')
    g.setExpression('.AttachmentOffset.Rotation.Angle', '180 deg / Params.z_pot')     # a gap faces the big gear
    g.setExpression('NumberOfTeeth', 'Params.z_pot'); g.setExpression('Modules', 'Params.module * 1 mm')
    d.pad('Gear', g, '$gear_top - $gear_bot')
    s = d.sketch('HubSketch', '$hub_bot'); s.circle('$pot_x', 0, '$hub_d')
    d.pad('Hub', s, '$gear_bot - $hub_bot')
    s = d.sketch('BoreSketch', '$gear_top'); s.circle('$pot_x', 0, '$pot_shaft_d + $bore_clear')
    d.pocket('Bore', s, through=True)
    return d.save(os.path.join(CAD, 'PotGear.FCStd'))


def build_small():
    # spring cup (between spring and M3 preload screw) and the TPU stop bumper
    build_spring_cup()
    d = fcb.PDoc('Bumper', params('bumper_d', 'stop_post_d', 'cam_top', 'cam_bot',
                                  extra=[('bore_clear', 0.3, 'TPU sleeve on the post')]))
    d.body('Bumper')
    s = d.sketch('BumperSketch', '$cam_bot'); s.ring(0, 0, '$bumper_d', '$stop_post_d + $bore_clear')
    d.pad('Sleeve', s, '$cam_top - $cam_bot')
    d.save(os.path.join(CAD, 'Bumper.FCStd'))
    build_stop_spacer()


def build_spring_cup():
    d = fcb.PDoc('SpringCup', params('spring_od', 'spring_id', 'spigot_l', 'spring_z', 'tip_y', 'pivot_x', 'arm_w',
                                     'spring_L0', 'spring_preload', 'cup_t', 'cup_socket_d', 'cup_socket_l',
                                     extra=[('cup_d', 14.0, '')]))
    d.body('SpringCup')
    x0 = '$pivot_x + $arm_w / 2 + $spring_L0 - $spring_preload'
    s = d.sketch('CupSketch', x0, plane='YZ'); s.circle('$tip_y', '$spring_z', '$cup_d')
    d.pad('Cup', s, '$cup_t')
    # blind centring hole for the preload screw tip, from the back face
    s = d.sketch('SocketSketch', x0 + ' + $cup_t', plane='YZ'); s.circle('$tip_y', '$spring_z', '$cup_socket_d')
    d.pocket('Socket', s, '$cup_socket_l')
    s = d.sketch('SpigotSketch', x0, plane='YZ'); s.circle('$tip_y', '$spring_z', '$spring_id - 0.5')
    d.pad('Spigot', s, '$spigot_l', reversed=True)
    return d.save(os.path.join(CAD, 'SpringCup.FCStd'))


def build_stop_spacer():
    # PETG tube under each bumper, on the stop post down to the deck: nothing else holds the TPU bumper at cam
    # height (2026-11-06; a TPU bumper that tall prints badly). Narrower than the bumper: the lug never meets it
    d = fcb.PDoc('StopSpacer', params('deck_top', 'cam_bot', 'stop_post_d',
                                      extra=[('spacer_d', 13.0, '1 under the bumper'),
                                             ('bore_clear', 0.4, 'PETG holes print ~0.2 small: slides on the post')]))
    d.body('StopSpacer')
    s = d.sketch('SpacerSketch', '$deck_top'); s.ring(0, 0, '$spacer_d', '$stop_post_d + $bore_clear')
    d.pad('Spacer', s, '$cam_bot - $deck_top')
    return d.save(os.path.join(CAD, 'StopSpacer.FCStd'))


def build_hardware():
    # reference shapes, not printed; each on its own axis, Z = 0 on its top face, going down
    d = fcb.PDoc('Hardware', params('brg_D', 'brg_d', 'brg_B', 'roller_D', 'roller_d', 'roller_B',
                                    'spring_od', 'spring_id', 'pot_body_d', 'pot_body_h', 'pot_bush_d',
                                    'pot_bush_h', 'pot_shaft_d', 'pot_shaft_l', 'pot_frame_x', 'pot_frame_y',
                                    'pot_tab_r', 'pot_tab_x', 'pot_tab_y', 'pot_tab_h',
                                    extra=[('spring_len', L['spring_L0'] - L['spring_preload'], 'preloaded length'),
                                           ('pcb_edge', 13.5, 'pot board edge from the axis (from the photo)'),
                                           ('pin_z', 4.75, 'pins under the frame top')]))
    for name, D, dd, B in (('Bearing6001', '$brg_D', '$brg_d', '$brg_B'),
                           ('Bearing608', '$roller_D', '$roller_d', '$roller_B')):
        d.body(name)
        s = d.sketch(name + 'Sketch', 0); s.ring(0, 0, D, dd)
        d.pad(name + 'Ring', s, B, reversed=True)
    d.body('Spring')                            # along +X from x = 0, at its preloaded length
    s = d.sketch('SpringSketch', 0, plane='YZ'); s.ring(0, 0, '$spring_od', '$spring_id')
    d.pad('Coil', s, '$spring_len')
    d.body('Pot')                               # Z = 0 on the frame top (bushing shoulder)
    s = d.sketch('PotBodySketch', '-$pot_body_h'); s.circle(0, 0, '$pot_body_d')
    d.pad('PotBody', s, '$pot_body_h - 0.8')
    s = d.sketch('FrameSketch', -0.8); s.rect('-$pot_frame_x / 2', '-$pot_frame_y / 2', '$pot_frame_x', '$pot_frame_y')
    d.pad('Frame', s, 0.8)
    s = d.sketch('TabSketch', 0)
    s.rect('-$pot_tab_x / 2', '$pot_tab_r - $pot_tab_y / 2', '$pot_tab_x', '$pot_tab_y')
    d.pad('Tab', s, '$pot_tab_h')
    s = d.sketch('BushingSketch', 0); s.circle(0, 0, '$pot_bush_d')
    d.pad('Bushing', s, '$pot_bush_h')
    s = d.sketch('ShaftSketch', '$pot_bush_h'); s.circle(0, 0, '$pot_shaft_d')
    d.pad('PotShaft', s, '$pot_shaft_l')
    s = d.sketch('BoardSketch', '-$pin_z - 0.8'); s.rect('-$pcb_edge', -6, '$pcb_edge', 12)
    d.pad('Board', s, 1.6)
    s = d.sketch('PinsSketch', 0, plane='YZ')            # three pins along -X, pitch 4
    for k in range(3):
        s.rect(-4 - 0.4 + 4 * k, '-$pin_z - 0.2', 0.8, 0.4)
    d.pad('Pins', s, '$pcb_edge + 5', reversed=True)
    return d.save(os.path.join(CAD, 'Hardware.FCStd'))


def build_fittest():
    # one plate: four 6001 seats, three shaft pins, three insert pilots
    d = fcb.PDoc('FitTest', [('plate_t', 4.0, 'plate'), ('seat_depth', 8.0, '6001 seats'),
                             ('ring_d', 33.0, 'seat wall'), ('pin_h', 12.0, 'shaft pins'),
                             ('boss_d', 8.0, 'insert bosses'), ('boss_h', 7.0, ''), ('ins_depth', 6.5, '')])
    d.body('FitTest')
    s = d.sketch('PlateSketch', 0); s.rect(0, -28, 140, 64)
    d.pad('Plate', s, '$plate_t')
    s = d.sketch('RingSketch', 0)
    for k in range(4):
        s.circle(18 + 34 * k, 18, '$ring_d')
    d.pad('Rings', s, '$seat_depth')
    s = d.sketch('SeatSketch', '$seat_depth')
    for k, sd in enumerate((27.95, 28.05, 28.15, 28.25)):
        s.circle(18 + 34 * k, 18, sd)
    d.pocket('Seats', s, through=True)
    s = d.sketch('PinSketch', '$plate_t')
    for k, sdia in enumerate((11.85, 11.95, 12.05)):
        s.circle(20 + 25 * k, -16, sdia)
    d.pad('ShaftPins', s, '$pin_h')
    s = d.sketch('BossSketch', '$plate_t')
    for k in range(3):
        s.circle(95 + 14 * k, -16, '$boss_d')
    d.pad('InsertBosses', s, '$boss_h')
    s = d.sketch('InsertSketch', '$plate_t + $boss_h')
    for k, idia in enumerate((3.9, 4.0, 4.1)):
        s.circle(95 + 14 * k, -16, idia)
    d.pocket('InsertHoles', s, '$ins_depth')
    return d.save(os.path.join(CAD, 'FitTest.FCStd'))


def build_fittest_pla():
    # case parts in PLA: three insert pilots and three RP2040 board gauges (board 22.85 wide)
    d = fcb.PDoc('FitTestPLA', [('plate_t', 3.0, 'plate'), ('boss_d', 8.0, 'insert bosses'), ('boss_h', 7.0, ''),
                                ('ins_depth', 6.5, ''), ('rail_w', 3.0, 'board gauges'), ('rail_h', 4.0, ''),
                                ('rail_l', 20.0, '')])
    d.body('FitTestPLA')
    s = d.sketch('PlateSketch', 0); s.rect(0, 0, 110, 50)
    d.pad('Plate', s, '$plate_t')
    s = d.sketch('BossSketch', '$plate_t')
    for k in range(3):
        s.circle(25 + 30 * k, 40, '$boss_d')
    d.pad('InsertBosses', s, '$boss_h')
    s = d.sketch('InsertSketch', '$plate_t + $boss_h')
    for k, idia in enumerate((3.9, 4.0, 4.1)):
        s.circle(25 + 30 * k, 40, idia)
    d.pocket('InsertHoles', s, '$ins_depth')
    s = d.sketch('RailSketch', '$plate_t')
    for k, gap in enumerate((23.0, 23.1, 23.2)):
        x = 25 + 35 * k
        s.rect(x - gap / 2 - 3.0, 5, '$rail_w', '$rail_l')
        s.rect(x + gap / 2, 5, '$rail_w', '$rail_l')
    d.pad('BoardRails', s, '$rail_h')
    return d.save(os.path.join(CAD, 'FitTestPLA.FCStd'))


# The handle is not built here: cad/Handle.FCStd is its master, edited in FreeCAD (2026-11-09).


# ---------------------------------------------------------------- case (PLA, case frame)
def chassis_screws():
    """The 4 chassis screws through the scale disc and the case top, in the case frame."""
    return [to_case('%s$case_screw' % sx, '%s$case_screw' % sy) for sx, sy in (('', ''), ('-', ''), ('-', '-'), ('', '-'))]


def corners(alias):
    return [('%s%s' % (sx, alias), '%s%s' % (sy, alias)) for sx, sy in (('', ''), ('-', ''), ('-', '-'), ('', '-'))]


CASE_PARAMS = ('case_t', 'case_in', 'case_wall', 'case_r', 'case_h', 'col_d', 'col_c', 'ins_d_pla', 'ins_l',
               'mech_rot', 'case_screw', 'csk_d')


def build_case_shell():
    # top and four walls in one piece, printed upside down (the top face on the bed)
    d = fcb.PDoc('CaseShell', params(*CASE_PARAMS, 'top_hole', 'cradle_x', 'usb_w', 'usb_h', 'rib_h', 'board_t',
                                     extra=[('screw_hole', 3.4, 'M3 clearance')]))
    d.body('CaseShell')
    s = d.sketch('OuterSketch', '-$case_h'); s.rrect(0, 0, '$case_in + 2 * $case_wall', '$case_in + 2 * $case_wall', '$case_r')
    d.pad('Shell', s, '$case_h')
    s = d.sketch('InnerSketch', '-$case_t'); s.rrect(0, 0, '$case_in', '$case_in', '$case_r - $case_wall')
    d.pocket('Hollow', s, through=True)
    s = d.sketch('ColumnSketch', '-$case_h')
    for x, y in corners('$col_c'):
        s.circle(x, y, '$col_d')
    d.pad('Columns', s, '$case_h - $case_t')
    s = d.sketch('BottomInsertSketch', '-$case_h')
    for x, y in corners('$col_c'):
        s.circle(x, y, '$ins_d_pla')
    d.pocket('BottomInserts', s, '$ins_l', reversed=True)
    s = d.sketch('TopHoleSketch', 0); s.circle(0, 0, '$top_hole')
    d.pocket('TopHole', s, '$case_t')
    s = d.sketch('ChassisScrewSketch', 0)
    for x, y in chassis_screws():
        s.circle(x, y, '$screw_hole')
    d.pocket('ChassisScrews', s, '$case_t')
    # USB-C: a notch up from the bottom edge of the back wall; a tongue on the bottom fills its lower part
    s = d.sketch('UsbSketch', '-$case_h')
    s.rect('$cradle_x - $usb_w / 2', '$case_in / 2 - 1', '$usb_w', '$case_wall + 2')
    d.pocket('UsbNotch', s, '$rib_h + $board_t + 1.6 + $usb_h / 2', reversed=True)
    return d.save(os.path.join(CAD, 'CaseShell.FCStd'))


def build_case_bottom():
    # bottom plate with the RP2040 cradle; 4 x M3 countersunk from below into the shell columns
    d = fcb.PDoc('CaseBottom', params(*CASE_PARAMS, 'bottom_t', 'foot_d', 'foot_c', 'cradle_x', 'board_l', 'board_w',
                                      'board_t', 'rib_h', 'usb_w', 'usb_h', 'board_gap',
                                      extra=[('screw_hole', 3.4, 'M3 clearance'), ('rail_t', 2.4, 'cradle side walls'),
                                             ('usb_edge', 77.6, 'board USB edge, Y'),
                                             ('lip', 1.5, 'groove blocks over the board, board pushed home (2 LEDs at ~2)'),
                                             ('hook', 0.8, 'latch over the board at the far end'),
                                             ('arm_t', 1.2, 'latch arm, it bends to let the board in'),
                                             ('rim_h', 2.0, 'rim inside the shell walls'), ('rim_t', 1.6, ''),
                                             ('rim_gap', 0.2, 'to the wall inside face')]))
    d.body('CaseBottom')
    F = '-$case_h'                                  # floor, top face of the bottom plate
    T = '-$case_h + $rib_h + $board_t'              # board top face
    y0 = '$usb_edge - $board_l'                     # board far edge
    s = d.sketch('PlateSketch', '-$case_h - $bottom_t')
    s.rrect(0, 0, '$case_in + 2 * $case_wall', '$case_in + 2 * $case_wall', '$case_r')
    d.pad('Plate', s, '$bottom_t')
    s = d.sketch('ScrewSketch', '-$case_h - $bottom_t')
    for x, y in corners('$col_c'):
        s.circle(x, y, '$screw_hole')
    d.hole('ScrewHoles', s, '$screw_hole', '$bottom_t', csk_d='$csk_d', reversed=True)
    s = d.sketch('FootSketch', '-$case_h - $bottom_t')
    for x, y in corners('$foot_c'):
        s.circle(x, y, '$foot_d + 0.4')
    d.pocket('FootRecesses', s, 1.0, reversed=True)
    # rim just inside the shell walls: lines the bottom up and keeps the walls from bending in;
    # it stops short of the corner columns and, at the back, of the RP2040 cradle
    a = '($col_c - $col_d / 2 - 0.5)'                 # rim ends, either side of the axis
    o = '($case_in / 2 - $rim_gap)'                   # rim outer face
    s = d.sketch('RimSketch', F)
    s.rect('-%s' % a, '-%s' % o, '2 * %s' % a, '$rim_t')                              # front
    s.rect('$cradle_x + 19', '%s - $rim_t' % o, '%s - $cradle_x - 19' % a, '$rim_t')   # back, right of the cradle
    s.rect('-%s' % o, '-%s' % a, '$rim_t', '2 * %s' % a)                              # left
    s.rect('%s - $rim_t' % o, '-%s' % a, '$rim_t', '2 * %s' % a)                      # right
    d.pad('Rim', s, '$rim_h')
    # cradle: side walls that only guide, a central rib between the pin rows, no ledge under the long edges
    s = d.sketch('RailSketch', F)
    s.rect('$cradle_x - $board_gap / 2 - $rail_t', '%s + 2' % y0, '$rail_t', '$board_l - 3')
    s.rect('$cradle_x + $board_gap / 2', '%s + 2' % y0, '$rail_t', '$board_l - 3')
    d.pad('Rails', s, '$rib_h + $board_t + 1')
    s = d.sketch('RibSketch', F); s.rect('$cradle_x - 3', '%s + 3' % y0, 6, '$board_l - 6')
    d.pad('Rib', s, '$rib_h')
    # USB end: two blocks beside the connector, with a groove the board edge slides into
    s = d.sketch('GrooveBlockSketch', F)
    for sx in ('+', '-'):
        s.rect('$cradle_x %s 6.8 - 1.5' % sx, '$usb_edge + 0.1 - $lip', 3, '$lip + 0.6')
    d.pad('GrooveBlocks', s, '$rib_h + $board_t + 1.6')
    s = d.sketch('GrooveSketch', '%s + 0.2' % T)
    s.rect('$cradle_x - 9', '$usb_edge - $lip', 18, '$lip + 0.1')     # groove bottom at usb_edge + 0.1
    d.pocket('Groove', s, '$board_t + 0.2')
    # far end: solid stops behind the board (the plug pushes it there) and a snap latch between them
    s = d.sketch('StopSketch', F)
    for sx in ('+', '-'):
        s.rect('$cradle_x %s 7.5 - 2.5' % sx, '%s - 3' % y0, 5, 2.9)
    d.pad('Stops', s, '$rib_h + $board_t')
    s = d.sketch('LatchSketch', '$cradle_x - 4', plane='YZ')
    s.polygon([('%s - 0.1 - $arm_t' % y0, F), ('%s - 0.1' % y0, F), ('%s - 0.1' % y0, '%s + 0.2' % T),
               ('%s + $hook' % y0, '%s + 0.2' % T), ('%s - 0.1' % y0, '%s + 1.8' % T),
               ('%s - 0.1 - $arm_t' % y0, '%s + 1.8' % T)])
    d.pad('Latch', s, 8)
    # tongue filling the lower part of the wall notch: the opening left is usb_w x usb_h
    s = d.sketch('TongueSketch', F)
    s.rect('$cradle_x - $usb_w / 2 + 0.2', '$case_in / 2 + 0.2', '$usb_w - 0.4', '$case_wall - 0.2')
    d.pad('Tongue', s, '$rib_h + $board_t + 1.6 - $usb_h / 2')
    # two zip-tie bridges for the wires, in front of the cradle
    s = d.sketch('BridgeSketch', F)
    for sx in ('+', '-'):
        s.rect('$cradle_x %s 8 - 4' % sx, '%s - 11' % y0, 8, 4)
    d.pad('Bridges', s, 5)
    s = d.sketch('BridgeTunnelSketch', '%s + 2.5' % F)
    for sx in ('+', '-'):
        s.rect('$cradle_x %s 8 - 2' % sx, '%s - 12' % y0, 4, 6)
    d.pocket('BridgeTunnels', s, 2.5)
    return d.save(os.path.join(CAD, 'CaseBottom.FCStd'))


SCALE = dict(
    index=-45.0,                  # handle index tab: the centre of the scale
    marks=(10, 30, 50, 75),       # degrees each side, with their numbers
    lh_sign=1,                    # LH towards counter-clockwise from above (the handle turned left)
    tick_r=(41.0, 45.0), tick_r0=39.0, tick_w=1.0,   # ticks; the centre one starts at tick_r0
    num_r=49.0, num_cap=4.5,      # numbers: mid-height on this radius, tops towards the centre (all)
    side_deg=89.0,                # LH / RH this far from the centre
)


def scale_items():
    """(kind, text, angle) of every mark: 'tick' with no text, 'num' and 'side' with text."""
    out = [('tick', '', SCALE['index'])]
    for sgn in (1, -1):
        for m in SCALE['marks']:
            a = SCALE['index'] + sgn * m
            out += [('tick', '', a), ('num', str(m), a)]
        side = 'LH' if sgn == SCALE['lh_sign'] else 'RH'
        out.append(('side', side, SCALE['index'] + sgn * SCALE['side_deg']))
    return out


def tick_outline(a, r0, r1, w):
    a = math.radians(a)
    c, sn = math.cos(a), math.sin(a)
    return [(round(r * c - t * sn, 4), round(r * sn + t * c, 4)) for r, t in ((r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2))]


def build_scale_disc():
    # on the case top, held by the 4 chassis screws (M3 x 12 countersunk through disc and top).
    # The scale round the handle index tab: ticks, numbers and LH / RH, a flush white inlay leg_t
    # deep (two 0.2 layers: the disc prints face down) as on the button cap; ScaleDiscLegend is the
    # white body. See SCALE.
    d = fcb.PDoc('ScaleDisc', params('disc_t', 'disc_d', 'top_hole', 'case_screw', 'mech_rot', 'csk_d',
                                     extra=[('screw_hole', 3.4, 'M3 clearance'), ('leg_t', B['leg_t'], 'inlay depth')]))
    disc = d.body('ScaleDisc')
    zt = L['disc_t']
    s = d.sketch('DiscSketch', 0); s.circle(0, 0, '$disc_d')
    d.pad('Disc', s, '$disc_t')
    s = d.sketch('HoleSketch', '$disc_t'); s.circle(0, 0, '$top_hole')
    d.pocket('ShaftHole', s, through=True)
    s = d.sketch('ScrewSketch', '$disc_t')
    for x, y in chassis_screws():
        s.circle(x, y, '$screw_hole')
    d.hole('ScrewHoles', s, '$screw_hole', '$disc_t', csk_d='$csk_d')
    items = scale_items()

    def ticks(sk):
        for kind, _, a in items:
            if kind == 'tick':
                r0 = SCALE['tick_r0'] if abs(a - SCALE['index']) < 1e-9 else SCALE['tick_r'][0]
                sk.polygon(tick_outline(a, r0, SCALE['tick_r'][1], SCALE['tick_w']))

    def texts(make):
        for k, (kind, txt, a) in enumerate(items):
            if kind != 'tick':
                r = SCALE['num_r']
                x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
                # every mark reads from outside the disc: its top towards the centre (user 2026-11-05;
                # the near-half / far-half flip read upside down on the far side)
                make(k, txt, x, y, a + 90)

    s = d.sketch('TickSketch', zt); ticks(s)
    d.pocket('Ticks', s, '$leg_t')

    def pocket_text(k, txt, x, y, rot):
        ss = legend_glyph(d, txt, x, y, zt, rot, SCALE['num_cap']); ss.Label = 'Mark%d_%s' % (k, txt)
        d.pocket('Mark%d' % k, ss, '$leg_t')
    texts(pocket_text)
    legend = d.body('ScaleDiscLegend', multi=True)
    s = d.sketch('LegendTickSketch', zt); ticks(s)
    d.pad('LegendTicks', s, '$leg_t', reversed=True)

    def pad_text(k, txt, x, y, rot):
        ss = legend_glyph(d, txt, x, y, zt, rot, SCALE['num_cap']); ss.Label = 'Text%d_%s' % (k, txt)
        d.pad('Text%d' % k, ss, '$leg_t', reversed=True)
    texts(pad_text)
    asm = d.doc.addObject('App::Part', 'ScaleDiscAssembly')
    asm.addObject(disc); asm.addObject(legend)
    return d.save(os.path.join(CAD, 'ScaleDisc.FCStd'))


def build_foot():
    d = fcb.PDoc('Foot', params('foot_d', 'foot_t'))
    d.body('Foot')                               # Z = 0 on its top face, 1 mm of it in the bottom recess
    s = d.sketch('FootSketch', '-$foot_t'); s.circle(0, 0, '$foot_d')
    d.pad('Pad', s, '$foot_t')
    return d.save(os.path.join(CAD, 'Foot.FCStd'))


# ---------------------------------------------------------------- PEDALS DISC button (button frame)
# The latch is a bought self-locking switch (see B, 2026-11-04): the cap is glued on its head, so it
# goes down flush and stays there, and comes up again at the next push; the switch holds it in.
# The skirt in the collar only guides it.
def bparams(*keys, extra=()):
    return [(k, round(B[k], 4), '') for k in keys] + list(extra)


def tangent_box(ang, r0, r1, half):
    """Rectangle across radius r0 ... r1 at angle ang (deg), half-width `half` tangentially."""
    a = math.radians(ang)
    n, t = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    return [(round(r * n[0] + s * half * t[0], 4), round(r * n[1] + s * half * t[1], 4))
            for r, s in ((r0, -1), (r1, -1), (r1, 1), (r0, 1))]


def legend_layout():
    """(char, x, y, rot) for every letter of LEGEND: x, y the centre of the letter's box at
    mid cap height, rot its turn (deg). The letters keep the font's spacing plus leg_track,
    measured along the arc."""
    import Draft
    tmp = App.newDocument('LegendLayout')
    out = []
    for word, side in LEGEND:
        ss = Draft.make_shapestring(String=word, FontFile=FONT, Size=B['leg_cap'], Tracking=0)
        tmp.recompute()
        faces = sorted(ss.Shape.Faces, key=lambda f: f.BoundBox.XMin)
        assert len(faces) == len(word), '%s: %d faces' % (word, len(faces))   # no letter in two pieces
        xs = [f.BoundBox.Center.x + k * B['leg_track'] for k, f in enumerate(faces)]
        mid = (faces[0].BoundBox.XMin + faces[-1].BoundBox.XMax + (len(word) - 1) * B['leg_track']) / 2
        R, cy = B['leg_R'], side * (B['leg_y'] - B['leg_R'])       # arc centre (0, cy)
        for ch, x in zip(word, xs):
            phi = (x - mid) / R
            px, py = R * math.sin(phi), cy + side * R * math.cos(phi)
            rot = -side * math.degrees(phi)
            a = math.radians(B['leg_rot'])
            out.append((ch, px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a),
                        rot + B['leg_rot']))
    App.closeDocument(tmp.Name)
    return out


def legend_glyph(d, ch, x, y, z, rot, size=None):
    """A letter (or a short string) as a ShapeString in the current body, its box centre at
    (x, y), face at z, turned by rot (deg); size is the cap height (default the button's)."""
    import Draft
    size = size or B['leg_cap']
    App.setActiveDocument(d.doc.Name)               # Draft makes it in the active document
    ss = Draft.make_shapestring(String=ch, FontFile=FONT, Size=size, Tracking=0)
    ss.Justification = 'Bottom-Left'
    ss.JustificationReference = 'Cap Height'
    d.doc.recompute()
    c = ss.Shape.BoundBox.Center
    c = V(c.x, size / 2, 0)                          # box centre across, mid cap height up
    r = App.Rotation(V(0, 0, 1), rot)
    ss.Placement = App.Placement(V(x, y, z) - r.multVec(c), r)
    d.b.addObject(ss)
    return ss


def build_button_base():
    # disc on the recess floor (2 pegs), the collar round the cap skirt, and in the middle a solid
    # pedestal with the square cup the switch body sits in; under it the well for the potted pins
    d = fcb.PDoc('ButtonBase', bparams('floor', 'disc_d', 'disc_t', 'collar_top', 'sw', 'sw_bot', 'cup_wall', 'cup_h',
                                       'cup_clear'))
    base = d.body('ButtonBase')
    top = B['floor'] + B['disc_t']
    s = d.sketch('DiscSketch', '$floor'); s.circle(0, 0, '$disc_d')
    d.pad('Disc', s, '$disc_t')
    s = d.sketch('PegSketch', '$floor')                     # two pegs into the handle floor: no turning
    for px, py in ((-9.71, -0.36), (11.29, -0.36)):
        s.circle(px, py, 3.0)
    d.pad('Pegs', s, 2.0, reversed=True)
    s = d.sketch('CollarSketch', top); s.ring(0, 0, 2 * B['collar_r'][1], 2 * B['collar_r'][0])
    d.pad('Collar', s, '$collar_top - $floor - $disc_t')
    o = B['ped']
    s = d.sketch('PedestalSketch', top); s.rect(-o / 2, -o / 2, o, o)
    d.pad('Pedestal', s, '$sw_bot + $cup_h - $floor - $disc_t')
    c = B['sw'] + 2 * B['cup_clear']
    s = d.sketch('CupSketch', B['sw_bot'] + B['cup_h']); s.rect(-c / 2, -c / 2, c, c)
    d.pocket('Cup', s, '$cup_h')
    # the well: all of it under the body except two ledges at the X ends, where there are no pins
    wx = B['sw'] - 2 * (B['sw_pin_in'][0] - 0.5)
    s = d.sketch('WellSketch', B['sw_bot']); s.rect(-wx / 2, -c / 2, wx, c)
    d.pocket('Well', s, through=True)
    asm = d.doc.addObject('App::Part', 'ButtonBaseAssembly')
    asm.addObject(base)
    # the switch as bought, latched, for the checks (no STL): body, wide block, neck, head, pins
    sw = d.body('Switch', multi=True)
    z0 = B['sw_bot']
    head_top = z0 + B['sw_on']
    s = d.sketch('SwBodySketch', z0); s.rect(-B['sw'] / 2, -B['sw'] / 2, B['sw'], B['sw'])
    d.pad('SwBody', s, B['sw'])
    bw = B['sw_block'][0]
    s = d.sketch('SwBlockSketch', z0 + B['sw'] - 0.5); s.rect(-bw / 2, -bw / 2, bw, bw)
    d.pad('SwBlock', s, head_top - B['sw_block'][1] - (z0 + B['sw'] - 0.5))
    nx, ny = B['sw_neck']
    if not B['head_long_x']:
        nx, ny = ny, nx
    s = d.sketch('SwNeckSketch', head_top - B['sw_block'][1] - 0.1); s.rect(-nx / 2, -ny / 2, nx, ny)
    d.pad('SwNeck', s, B['sw_block'][1] - B['sw_head'][2] + 0.1)
    hx, hy, ht = B['sw_head']
    if not B['head_long_x']:
        hx, hy = hy, hx
    s = d.sketch('SwHeadSketch', head_top - ht); s.rect(-hx / 2, -hy / 2, hx, hy)
    d.pad('SwHead', s, ht)
    s = d.sketch('SwPinSketch', z0)
    for px in (-1, 0, 1):
        for py in (-1, 1):
            x = px * (B['sw'] / 2 - B['sw_pin_in'][0])
            y = py * (B['sw'] / 2 - B['sw_pin_in'][1])
            s.rect(x - 0.25, y - 0.15, 0.5, 0.3)
    d.pad('SwPins', s, B['sw_pin_l'], reversed=True)
    asm.addObject(sw)
    return d.save(os.path.join(CAD, 'ButtonBase.FCStd'))


def build_button_cap():
    d = fcb.PDoc('ButtonCap', bparams('top', 'cap_d', 'cap_t', 'band', 'skirt_bot', 'leg_t', 'boss_d', 'boss_h',
                                      'socket_in', 'socket_depth', 'sleeve_in', 'sleeve_out', 'sleeve_bot'))
    d.body('ButtonCap')
    zt, sb = B['top'], B['skirt_bot']
    s = d.sketch('PlateSketch', '$top - $cap_t'); s.circle(0, 0, '$cap_d')
    d.pad('Plate', s, '$cap_t')
    s = d.sketch('BandSketch', '$top - $band'); s.ring(0, 0, '$cap_d', 2 * B['skirt_r'][0])
    d.pad('Band', s, '$band - $cap_t')
    s = d.sketch('SkirtSketch', '$skirt_bot'); s.ring(0, 0, 2 * B['skirt_r'][1], 2 * B['skirt_r'][0])
    d.pad('Skirt', s, '$top - $band - $skirt_bot')
    # square sleeve round the base pedestal, from the plate down to sleeve_bot: guides the cap up and down
    s = d.sketch('SleeveSketch', '$sleeve_bot')
    s.rect('-$sleeve_out / 2', '-$sleeve_out / 2', '$sleeve_out', '$sleeve_out')
    s.rect('-$sleeve_in / 2', '-$sleeve_in / 2', '$sleeve_in', '$sleeve_in')
    d.pad('Sleeve', s, '$top - $cap_t - $sleeve_bot')
    # boss under the plate in the middle, with the rectangular socket the switch head is glued in
    # (rectangular: the cap cannot turn)
    s = d.sketch('BossSketch', '$top - $cap_t - $boss_h'); s.circle(0, 0, '$boss_d')
    d.pad('HeadBoss', s, '$boss_h')
    sx, sy = B['socket'] if B['head_long_x'] else B['socket'][::-1]   # as the switch head
    s = d.sketch('SocketSketch', '$top - $cap_t - $boss_h'); s.rect(-sx / 2, -sy / 2, sx, sy)
    d.pocket('HeadSocket', s, '$socket_depth', reversed=True)
    # PEDAL DISC: each letter pocketed leg_t into the face; the same letters, leg_t thick, are the
    # ButtonCapLegend body, flush in the pockets (second filament, the first two layers face down)
    lay = legend_layout()
    cap = d.b
    for k, (ch, x, y, rot) in enumerate(lay):
        ss = legend_glyph(d, ch, x, y, zt, rot); ss.Label = 'Legend%d_%s' % (k + 1, ch)
        d.pocket('Legend%d' % (k + 1), ss, '$leg_t')
    legend = d.body('ButtonCapLegend', multi=True)
    for k, (ch, x, y, rot) in enumerate(lay):
        ss = legend_glyph(d, ch, x, y, zt, rot); ss.Label = 'Letter%d_%s' % (k + 1, ch)
        d.pad('Letter%d' % (k + 1), ss, '$leg_t', reversed=True)
    # cap and letters together: the assembly links this, so the legend shows in Tiller too
    asm = d.doc.addObject('App::Part', 'ButtonCapAssembly')
    asm.addObject(cap); asm.addObject(legend)
    return d.save(os.path.join(CAD, 'ButtonCap.FCStd'))


# ---------------------------------------------------------------- assembly
def build_assembly(docs):
    a = App.newDocument('Tiller')
    a.saveAs(os.path.join(CAD, 'Tiller.FCStd'))      # links need a saved owner
    def link(name, docname, obj, base=(0, 0, 0), rot=None):
        l = a.addObject('App::Link', name)
        l.LinkedObject = docs[docname].getObject(obj)
        pl = App.Placement(V(*base), rot or App.Rotation())
        l.Placement = pl
        return l
    R = App.Rotation(V(0, 0, 1), L['mech_rot'])
    def mlink(name, docname, obj, base=(0, 0, 0)):
        # mechanism parts: drawn in the mechanism frame, turned by mech_rot in the case
        return link(name, docname, obj, tuple(R.multVec(V(*base))), R)
    link('Handle', 'Handle', 'Handle', (0, 0, L['handle_z']))
    for n in ('ButtonBase', 'ButtonCap'):                         # latched, in the handle recess
        link(n, n, LINK_TARGET.get(n, n), (B['x'], B['y'], L['handle_z']))
    link('Shaft', 'Shaft', 'Shaft')
    mlink('Chassis', 'Chassis', 'Chassis')
    mlink('Rotor', 'Rotor', 'Rotor')
    mlink('RollerArm', 'RollerArm', 'RollerArm')
    mlink('Deck', 'Deck', 'Deck')
    mlink('PotGear', 'PotGear', 'PotGear')
    mlink('SpringCup', 'SpringCup', 'SpringCup')
    for k, (sx, sy) in enumerate(STOPS):
        mlink('Bumper%d' % (k + 1), 'Bumper', 'Bumper', (sx, sy, 0))
        mlink('StopSpacer%d' % (k + 1), 'StopSpacer', 'StopSpacer', (sx, sy, 0))
    link('BearingUpper', 'Hardware', 'Bearing6001', (0, 0, L['brg1_top']))
    link('BearingLower', 'Hardware', 'Bearing6001', (0, 0, L['brg2_top']))
    mlink('Roller', 'Hardware', 'Bearing608', (L['pivot_x'], 0, L['roller_top']))
    mlink('Spring', 'Hardware', 'Spring', (L['pivot_x'] + L['arm_w'] / 2, L['tip_y'], L['spring_z']))
    mlink('Pot', 'Hardware', 'Pot', (L['pot_x'], 0, L['deck_top'] - L['deck_t']))
    link('CaseShell', 'CaseShell', 'CaseShell')
    link('CaseBottom', 'CaseBottom', 'CaseBottom')
    link('ScaleDisc', 'ScaleDisc', LINK_TARGET['ScaleDisc'])
    fz = -L['case_h'] - L['bottom_t'] + 1
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        link('Foot%d' % (k + 1), 'Foot', 'Foot', (sx * L['foot_c'], sy * L['foot_c'], fz))
    a.recompute()
    a.save()
    return a


def export_stl(doc):
    """Every body of a part file to stl/Tiller-<body>.stl (fine mesh: the legend letters)."""
    import MeshPart
    import Mesh
    os.makedirs(os.path.join(ROOT, 'stl'), exist_ok=True)
    for b in [o for o in doc.Objects if o.TypeId == 'PartDesign::Body' and o.Name not in NO_STL]:
        m = MeshPart.meshFromShape(Shape=b.Shape, LinearDeflection=0.01, AngularDeflection=math.radians(5),
                                   Relative=False)
        path = os.path.join(ROOT, 'stl', 'Tiller-%s.stl' % b.Name)
        Mesh.Mesh(m).write(path)
        print('  wrote', path, m.CountFacets, 'facets')


def relink_assembly(doc):
    """Point the links of Tiller.FCStd into `doc` at its LINK_TARGET object, keeping the rest."""
    import keep_gui
    path = os.path.join(CAD, 'Tiller.FCStd')
    if not os.path.exists(path) or doc.Name not in LINK_TARGET:
        return
    gui = keep_gui.take(path)
    a = App.openDocument(path)
    for l in [o for o in a.Objects if o.TypeId == 'App::Link' and o.LinkedObject
              and o.LinkedObject.Document.Name == doc.Name]:
        l.LinkedObject = doc.getObject(LINK_TARGET[doc.Name])
        print('  Tiller: %s -> %s' % (l.Name, l.LinkedObject.Name))
    for n in GONE_LINKS:                                 # parts dropped from the design
        if a.getObject(n):
            a.removeObject(n)
            print('  Tiller: %s removed' % n)
    a.recompute()
    a.save()
    keep_gui.put(path, gui)


# Only some parts:  set TILLER_ONLY=build_button_cap  (function names, comma separated) before
# running; their part files are rebuilt, their bodies exported to stl/ and the Tiller links into
# them pointed at LINK_TARGET; nothing else is touched.
ONLY = [n.strip() for n in os.environ.get('TILLER_ONLY', '').split(',') if n.strip()]
if ONLY and not globals().get('NO_BUILD') and not getattr(App, '_tiller_built', False):
    App._tiller_built = True
    for n in ONLY:
        dd = globals()[n]()
        print('built', dd.Name)
        export_stl(dd)
        relink_assembly(dd)
elif not globals().get('NO_BUILD') and not getattr(App, '_tiller_built', False):
    App._tiller_built = True
    import traceback
    try:
        docs = {}
        for fn in (build_shaft, build_chassis, build_rotor, build_arm, build_deck, build_potgear, build_hardware,
                   build_fittest, build_fittest_pla, build_case_shell, build_case_bottom,
                   build_scale_disc, build_foot, build_button_base, build_button_cap):
            dd = fn(); docs[dd.Name] = dd
            print('built', dd.Name)
        docs['Handle'] = App.openDocument(os.path.join(CAD, 'Handle.FCStd'))   # not rebuilt
        build_small()
        for n in ('SpringCup', 'Bumper', 'StopSpacer'):
            docs[n] = App.getDocument(n)
        build_assembly(docs)
        print('stops at', [tuple(round(c, 2) for c in s) for s in STOPS], 'centre distance', CENTRE_DIST)
    except Exception:
        traceback.print_exc()
