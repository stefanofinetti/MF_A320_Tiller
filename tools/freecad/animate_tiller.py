# Animated GIF of the tiller mechanism over its travel, from cad/Tiller.FCStd.
#   "C:\Program Files\FreeCAD 1.1\bin\freecad.exe" tools/freecad/animate_tiller.py
# Needs the FreeCAD GUI (it renders the 3D view). It opens Tiller.FCStd, moves the links with the
# same kinematics as check_assembly.py (handle, shaft, rotor turn by theta; arm and roller by the
# beta the cam gives; pot gear by -theta * z_gear / z_pot; the spring shortens by the arm tip
# travel), saves one image per frame, builds media/tiller.gif and quits. Tiller.FCStd is not saved.
# Settings through environment variables: TILLER_FRAMES (default 96), TILLER_SIZE (900x700),
# TILLER_KEEP=1 to leave FreeCAD open at the end.
import os
import sys
import math
import numpy as np
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else \
    'D:/MobiFlight/Airbus_Tiller/tools/freecad'
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
g = {'__file__': os.path.join(HERE, 'build_mechanism.py'), 'NO_BUILD': True, '__name__': 'lib'}
exec(open(os.path.join(HERE, 'build_mechanism.py'), encoding='utf-8').read(), g)
L, cam, CAD = g['L'], g['cam'], g['CAD']

N = int(os.environ.get('TILLER_FRAMES', '96'))
W, H = (int(v) for v in os.environ.get('TILLER_SIZE', '900x700').split('x'))
OUT = os.path.join(ROOT, 'media')
FRAMES = os.path.join(OUT, 'frames')
HIDE = ('CaseShell', 'CaseBottom', 'Deck', 'Pot')           # the deck and the case would hide the mechanism
# colour (r, g, b) and transparency (%) per link
LOOK = {'Chassis': ((0.75, 0.78, 0.82), 75), 'ScaleDisc': ((0.75, 0.78, 0.82), 60),
        'StopSpacer1': ((0.75, 0.78, 0.82), 50), 'StopSpacer2': ((0.75, 0.78, 0.82), 50),
        'Handle': ((0.25, 0.25, 0.28), 0), 'Shaft': ((0.55, 0.55, 0.58), 0),
        'Rotor': ((0.95, 0.55, 0.10), 0), 'RollerArm': ((0.15, 0.45, 0.85), 0),
        'Roller': ((0.70, 0.70, 0.72), 0), 'Spring': ((0.85, 0.15, 0.15), 0),
        'SpringCup': ((0.15, 0.45, 0.85), 0), 'PotGear': ((0.20, 0.65, 0.30), 0),
        'Bumper1': ((0.15, 0.15, 0.15), 0), 'Bumper2': ((0.15, 0.15, 0.15), 0)}
TURN = ('Handle', 'Shaft', 'Rotor', 'ButtonBase', 'ButtonCap')
ARM = ('RollerArm', 'Roller')

syn = cam.synth()
Z = App.Vector(0, 0, 1)
R = App.Rotation(Z, L['mech_rot'])
PIV = R.multVec(App.Vector(L['pivot_x'], L['pivot_y'], 0))
POT = R.multVec(App.Vector(L['pot_x'], 0, 0))


def beta_at(th_deg):
    return float(np.interp(math.radians(th_deg), syn['th'], syn['beta']))


def turned(p0, deg, centre=App.Vector()):
    return App.Placement(App.Vector(), App.Rotation(Z, deg), centre).multiply(p0)


VIEW = tuple(float(v) for v in os.environ.get('TILLER_VIEW', '-30,-30,0.65').split(','))   # azimuth, elevation, zoom


def set_camera(view, az, el, zoom):
    # camera on a sphere round the mechanism: azimuth from +X (deg), elevation (negative: from below), Z up
    a, e = math.radians(az), math.radians(el)
    back = App.Vector(math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))   # towards the camera
    right = Z.cross(back); right.normalize()
    up = back.cross(right)
    m = App.Matrix(right.x, up.x, back.x, 0, right.y, up.y, back.y, 0, right.z, up.z, back.z, 0, 0, 0, 0, 1)
    view.setCameraOrientation(App.Rotation(m))
    view.fitAll()
    c = view.getCameraNode()
    try:
        c.height.setValue(c.height.getValue() * zoom)
    except AttributeError:
        pass


def main():
    # the part files first, fully: opened only through the links they come in partly, without proper
    # view providers, and some bodies then show their vertices only
    import re
    import zipfile
    with zipfile.ZipFile(os.path.join(CAD, 'Tiller.FCStd')) as z:
        xml = z.read('Document.xml').decode('utf-8')
    for f in sorted(set(re.findall(r'(\w+)\.FCStd', xml))):
        if f != 'Tiller' and os.path.exists(os.path.join(CAD, f + '.FCStd')):
            App.openDocument(os.path.join(CAD, f + '.FCStd'))
    doc = App.openDocument(os.path.join(CAD, 'Tiller.FCStd'))
    Gui.getDocument(doc.Name).ActiveView    # Tiller's view in front
    links = {o.Name: o for o in doc.Objects if o.TypeId == 'App::Link'}
    for o in links.values():
        o.LinkedObject.Document.recompute()
        lo = o.LinkedObject                         # a body hidden in its own file shows only bits in the link
        lvp = Gui.getDocument(lo.Document.Name).getObject(lo.Name)
        if lvp is not None and not lvp.Visibility:
            lvp.Visibility = True
    p0 = {n: App.Placement(o.Placement) for n, o in links.items()}
    for n in links:                                 # whatever was hidden in the GUI last time
        links[n].Visibility = not (n in HIDE or n.startswith('Foot'))
    if os.environ.get('TILLER_DEBUG'):
        for n in ('Rotor', 'RollerArm', 'PotGear'):
            vp = Gui.getDocument(doc.Name).getObject(n)
            print(n, 'linkvp', {p: str(getattr(vp, p))[:60] for p in vp.PropertiesList})
            ld = links[n].LinkedObject.Document
            for o in ld.Objects:
                ov = Gui.getDocument(ld.Name).getObject(o.Name)
                print('   ', o.Name, o.TypeId, ov.Visibility if ov else None,
                      getattr(ov, 'DisplayMode', None), getattr(ov, 'Transparency', None))
    gdoc = Gui.getDocument(doc.Name)
    for n, (rgb, t) in LOOK.items():
        if n in links:
            lo = links[n].LinkedObject              # the body in its own file (not saved)
            lvp = Gui.getDocument(lo.Document.Name).getObject(lo.Name)
            try:
                lvp.ShapeColor = rgb
                lvp.Transparency = t
                continue
            except Exception as e:
                print('colour on the body', n, e)
            vp = gdoc.getObject(n)
            vp.OverrideMaterial = True
            m = vp.ShapeMaterial
            m.DiffuseColor = rgb + (0.0,)
            m.AmbientColor = tuple(0.3 * c for c in rgb) + (0.0,)
            m.Transparency = t / 100.0
            vp.ShapeMaterial = m
    view = gdoc.ActiveView
    view.setAnimationEnabled(False)
    set_camera(view, *VIEW)
    os.makedirs(FRAMES, exist_ok=True)
    for f in os.listdir(FRAMES):
        os.remove(os.path.join(FRAMES, f))

    Lp = L['spring_L0'] - L['spring_preload']
    tip = cam.P['ARM_TIP']
    paths = []
    for i in range(N):
        th = 75.0 * math.sin(2 * math.pi * i / N)
        b = beta_at(th)
        for n in TURN:
            if n in links:
                links[n].Placement = turned(p0[n], th)
        for n in [n for n in links if n.startswith('Bearing')]:
            links[n].Placement = turned(p0[n], th)
        for n in ARM:
            links[n].Placement = turned(p0[n], -math.degrees(b), PIV)
        links['PotGear'].Placement = turned(p0['PotGear'], -th * L['z_gear'] / L['z_pot'], POT)
        x = tip * math.sin(abs(b))                  # extra compression, the cup end stays
        sp = App.Placement(p0['Spring'])
        sp.Base = sp.Base + sp.Rotation.multVec(App.Vector(x, 0, 0))
        links['Spring'].Placement = sp
        links['Spring'].ScaleVector = App.Vector((Lp - x) / Lp, 1, 1)
        doc.recompute()
        Gui.updateGui()
        p = os.path.join(FRAMES, 'f%03d.png' % i)
        view.saveImage(p, W, H, '#FFFFFF')
        paths.append((p, th, L['spring_k'] * (L['spring_preload'] + x)))
    make_gif(paths)


def make_gif(paths):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('arial.ttf', 22)
    except OSError:
        font = ImageFont.load_default()
    imgs = []
    for p, th, force in paths:
        im = Image.open(p).convert('RGB')
        d = ImageDraw.Draw(im)
        d.text((16, 14), 'tiller %+5.1f deg   spring %4.1f N' % (th, force), fill=(40, 40, 40), font=font)
        imgs.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    out = os.path.join(OUT, 'tiller.gif')
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=45, loop=0, optimize=True)
    print('wrote', out, os.path.getsize(out) // 1024, 'kB')


def run():
    os.makedirs(OUT, exist_ok=True)
    log = open(os.path.join(OUT, 'animate.log'), 'w', encoding='utf-8')
    sys.stdout = sys.stderr = log                    # the GUI has no console here
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    log.flush()
    if os.environ.get('TILLER_KEEP') != '1':
        for d in list(App.listDocuments().values()):
            App.closeDocument(d.Name)               # nothing is saved
        Gui.getMainWindow().close()


QtCore.QTimer.singleShot(1500, run)                 # after the main window is up
