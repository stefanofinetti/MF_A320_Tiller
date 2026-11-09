# Small helper to build parametric FreeCAD part files from scripts.
#
# Every part document gets a "Params" spreadsheet. Sizes passed as strings are
# expressions on it: "$shaft_d / 2" becomes "Params.shaft_d / 2", so the part can
# be changed later in the FreeCAD GUI by editing the spreadsheet.
import FreeCAD as App
import Part
import keep_gui                      # keeps the user's colours and visibility across runs

V = App.Vector


class Doc:
    def __init__(self, name, params):
        """params: list of (alias, value, note)."""
        self.doc = App.newDocument(name)
        self.p = {a: v for a, v, _ in params}
        sh = self.doc.addObject('Spreadsheet::Sheet', 'Params')
        sh.set('A1', 'Parameter'); sh.set('B1', 'Value'); sh.set('C1', 'Note')
        for i, (a, v, note) in enumerate(params, start=2):
            sh.set('A%d' % i, a); sh.set('B%d' % i, repr(float(v))); sh.setAlias('B%d' % i, a)
            sh.set('C%d' % i, note)
        self.sheet = sh
        self.doc.recompute()

    # -- values and expressions -------------------------------------------
    def x(self, e):
        return e.replace('$', 'Params.')

    def val(self, e):
        if not isinstance(e, str):
            return e
        return eval(e.replace('$', ''), {}, dict(self.p))

    def set(self, obj, prop, v):
        if isinstance(v, str):
            obj.setExpression(prop, self.x(v))
        else:
            target, *path = prop.lstrip('.').split('.')
            if not path:
                setattr(obj, target, v)
            else:
                pl = obj.Placement
                if path == ['z']:
                    pl.Base.z = v
                elif path == ['x']:
                    pl.Base.x = v
                elif path == ['y']:
                    pl.Base.y = v
                obj.Placement = pl

    def place(self, obj, x, y, z):
        for k, v in (('x', x), ('y', y), ('z', z)):
            if isinstance(v, str):
                obj.setExpression('.Placement.Base.' + k, self.x(v))
            else:
                pl = obj.Placement; setattr(pl.Base, k, float(v)); obj.Placement = pl

    # -- primitives --------------------------------------------------------
    def cyl(self, name, r, h, x=0, y=0, z=0, axis='z', angle=360):
        c = self.doc.addObject('Part::Cylinder', name)
        self.set(c, 'Radius', r); self.set(c, 'Height', h)
        if angle != 360:
            c.Angle = angle
        rot = {'x': App.Rotation(V(0, 1, 0), 90), '-x': App.Rotation(V(0, 1, 0), -90),
               'y': App.Rotation(V(1, 0, 0), -90)}.get(axis)
        if rot:
            pl = c.Placement; pl.Rotation = rot; c.Placement = pl
        self.place(c, x, y, z)
        return c

    def box(self, name, L, W, H, x=0, y=0, z=0):
        b = self.doc.addObject('Part::Box', name)
        self.set(b, 'Length', L); self.set(b, 'Width', W); self.set(b, 'Height', H)
        self.place(b, x, y, z)
        return b

    def feature(self, name, shape):
        f = self.doc.addObject('Part::Feature', name)
        f.Shape = shape
        return f

    def extrude(self, name, base, h, z=None):
        e = self.doc.addObject('Part::Extrusion', name)
        e.Base = base; e.DirMode = 'Custom'; e.Dir = V(0, 0, 1); e.Solid = True
        self.set(e, 'LengthFwd', h)
        base.Visibility = False
        return e

    def fuse(self, name, objs, refine=True):
        f = self.doc.addObject('Part::MultiFuse', name)
        f.Shapes = objs; f.Refine = refine
        for o in objs:
            o.Visibility = False
        return f

    def cut(self, name, base, tools, refine=True):
        tool = tools[0] if len(tools) == 1 else self.fuse(name + '_Tools', tools, refine=False)
        c = self.doc.addObject('Part::Cut', name)
        c.Base = base; c.Tool = tool; c.Refine = refine
        base.Visibility = False; tool.Visibility = False
        return c

    def save(self, path):
        self.doc.recompute()
        bad = [o.Name for o in self.doc.Objects if 'Invalid' in o.State or 'Error' in o.State]
        if bad:
            raise RuntimeError('%s: objects in error: %s' % (self.doc.Name, bad))
        gui = keep_gui.take(path)            # before saveAs overwrites the file
        self.doc.saveAs(path)
        keep_gui.put(path, gui)
        return self.doc


# ---------------------------------------------------------------- PartDesign
# Bodies made of constrained sketches and Pad / Pocket features. Sketch dimensions
# are named constraints driven by the Params sheet, so the part is edited in the GUI
# either from the sheet or by opening a sketch.
import math
import Sketcher

AXIS_H, AXIS_V, ROOT = -1, -2, -1          # sketch H axis, V axis, root point (ROOT, 1)


class PDoc(Doc):
    multi = ()                               # names of bodies allowed to be several solids

    def body(self, name, base=None, multi=False):
        self.b = self.doc.addObject('PartDesign::Body', name)
        if base is not None:
            self.b.BaseFeature = base
        if multi:
            self.b.AllowCompound = True
            self.multi = tuple(self.multi) + (name,)
        self.planes = {f.Role: f for f in self.b.Origin.OriginFeatures}
        return self.b

    def val(self, e):
        if not isinstance(e, str):
            return e
        ns = dict(self.p, cos=math.cos, sin=math.sin, pi=math.pi)
        return eval(e.replace('$', '').replace('deg', '* pi / 180'), {}, ns)

    def sketch(self, name, z=0, plane='XY', rot=0):
        """Sketch on a body origin plane, offset along its normal by z (number or expression).
        XY: sketch x, y = X, Y, normal +Z.  YZ: sketch x, y = Y, Z, normal +X.
        XZ: sketch x, y = X, Z (a half section through the Z axis); rot turns it about Z
        (degrees, counter-clockwise seen from +Z), for revolutions and helices."""
        sk = self.b.newObject('Sketcher::SketchObject', name)
        sk.AttachmentSupport = [(self.planes[plane + '_Plane'], '')]
        sk.MapMode = 'FlatFace'
        if plane == 'XZ':
            sk.AttachmentOffset = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 1, 0), rot))
        elif rot:
            sk.AttachmentOffset = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 0, 1), rot))
        if isinstance(z, str):
            sk.setExpression('.AttachmentOffset.Base.z', self.x(z))
        elif z:
            pl = sk.AttachmentOffset; pl.Base.z = float(z); sk.AttachmentOffset = pl
        return Sk(self, sk)

    def vsketch(self, name, ang, dist):
        """Sketch on a vertical plane facing outwards at angle ang (deg, counter-clockwise from +X),
        dist from the Z axis (numbers). Sketch x runs along the tangent (towards ang + 90), y = Z;
        the normal points away from the axis."""
        sk = self.b.newObject('Sketcher::SketchObject', name)
        sk.AttachmentSupport = [(self.planes['XZ_Plane'], '')]
        sk.MapMode = 'FlatFace'
        r = App.Rotation(App.Vector(0, 1, 0), ang + 90)    # the XZ plane faces -Y: turn it to face ang
        sk.AttachmentOffset = App.Placement(r.multVec(App.Vector(0, 0, float(dist))), r)
        return Sk(self, sk)

    def _z_axis(self):
        return [f for f in self.b.Origin.OriginFeatures if f.Role == 'Z_Axis'][0]

    def revolve(self, name, prof, angle=360):
        """Revolve an XZ half-section sketch about Z by angle (degrees, counter-clockwise)."""
        f = self.b.newObject('PartDesign::Revolution', name)
        f.Profile = prof.sk
        f.ReferenceAxis = (self._z_axis(), [''])
        f.Angle = angle
        f.Refine = True
        return f

    def helix(self, name, prof, pitch, angle, left=False, sub=True):
        """Sweep an XZ half-section sketch about Z along a helix of the given pitch, through
        angle degrees: counter-clockwise rising (right-handed) or clockwise rising (left=True)."""
        f = self.b.newObject('PartDesign::%sHelix' % ('Subtractive' if sub else 'Additive'), name)
        f.Profile = prof.sk
        f.ReferenceAxis = (self._z_axis(), [''])
        f.Mode = 'pitch-turns-angle'
        f.Pitch = pitch
        f.Turns = angle / 360.0
        f.LeftHanded = left
        f.Refine = True
        return f

    def polar(self, name, feats, n):
        """Polar pattern of features about Z, n occurrences over 360 degrees."""
        f = self.b.newObject('PartDesign::PolarPattern', name)
        f.Originals = feats
        f.Axis = (self._z_axis(), [''])
        f.Angle = 360
        f.Occurrences = n
        f.Refine = True
        return f

    def _feat(self, kind, name, prof, length, reversed=False, through=False):
        f = self.b.newObject('PartDesign::' + kind, name)
        f.Profile = prof.sk if isinstance(prof, Sk) else prof
        if through:
            f.Type = 'ThroughAll'
        else:
            self.set(f, 'Length', length)
        f.Reversed = reversed
        f.Refine = True
        return f

    def pad(self, name, prof, length, reversed=False):
        """Pads grow along the sketch normal (up for XY sketches) unless reversed."""
        return self._feat('Pad', name, prof, length, reversed)

    def pocket(self, name, prof, length=None, reversed=False, through=False):
        """Pockets cut against the sketch normal (down for XY sketches) unless reversed."""
        return self._feat('Pocket', name, prof, length, reversed, through)

    def hole(self, name, prof, d, depth, csk_d=None, csk_angle=90, reversed=False):
        """PartDesign Hole at every circle centre of the sketch, drilled against the
        sketch normal (down for XY sketches) unless reversed; optional countersink."""
        h = self.b.newObject('PartDesign::Hole', name)
        h.Profile = prof.sk if isinstance(prof, Sk) else prof
        h.Threaded = False
        self.set(h, 'Diameter', d)
        h.DepthType = 'Dimension'
        self.set(h, 'Depth', depth)
        if csk_d is not None:
            h.HoleCutType = 'Countersink'
            self.set(h, 'HoleCutDiameter', csk_d)
            h.HoleCutCountersinkAngle = csk_angle
        h.DrillPoint = 'Flat'
        h.Reversed = reversed
        h.Refine = True
        return h

    def save(self, path):
        # as the GUI leaves it: only the body and its tip shown, sketches and earlier features hidden
        for b in [o for o in self.doc.Objects if o.TypeId == 'PartDesign::Body']:
            for o in b.Group + b.Origin.OriginFeatures + [b.Origin]:
                o.Visibility = (o == b.Tip)
            if b.BaseFeature:
                b.BaseFeature.Visibility = False
            b.Visibility = True
        doc = super().save(path)
        for b in [o for o in doc.Objects if o.TypeId == 'PartDesign::Body']:
            s = b.Shape
            # loose letters (a legend inlay) may be several solids, every other body is one
            if not s.isValid() or not s.Solids or (len(s.Solids) != 1 and b.Name not in self.multi):
                raise RuntimeError('%s: body is not one valid solid (%d solids)' % (b.Name, len(s.Solids)))
            loose = [o.Label for o in b.Group if o.TypeId == 'Sketcher::SketchObject' and not o.FullyConstrained]
            if loose:
                print('  %s: sketches not fully constrained: %s' % (b.Name, loose))
        return doc


class Sk:
    """Constrained sketch geometry. Coordinates and sizes are numbers or "$alias" expressions."""

    def __init__(self, pd, sk):
        self.pd, self.sk = pd, sk

    def _c(self, cons, expr=None):
        i = self.sk.addConstraint(cons)
        if isinstance(expr, str):
            e = expr.strip()
            name = e[1:] if e.startswith('$') and e[1:].isidentifier() else 'c%d' % i
            names = {c.Name for c in self.sk.Constraints if c.Name}
            base, k = name, 1
            while name in names:
                k += 1; name = '%s_%d' % (base, k)
            self.sk.renameConstraint(i, name)
            self.sk.setExpression('.Constraints.' + name, self.pd.x(expr))
        return i

    def point(self, g, pos, x, y):
        """Put a vertex at (x, y): on the axes when a coordinate is the number 0."""
        if not isinstance(x, str) and not isinstance(y, str) and x == 0 and y == 0:
            return self._c(Sketcher.Constraint('Coincident', g, pos, ROOT, 1))
        for coord, kind, axis in ((x, 'DistanceX', AXIS_V), (y, 'DistanceY', AXIS_H)):
            if not isinstance(coord, str) and coord == 0:
                self._c(Sketcher.Constraint('PointOnObject', g, pos, axis))
            else:
                self._c(Sketcher.Constraint(kind, ROOT, 1, g, pos, float(self.pd.val(coord))), coord)

    def circle(self, x, y, d):
        v = self.pd.val
        g = self.sk.addGeometry(Part.Circle(V(v(x), v(y), 0), V(0, 0, 1), v(d) / 2))
        self.point(g, 3, x, y)
        self._c(Sketcher.Constraint('Diameter', g, float(v(d))), d)
        return g

    def ring(self, x, y, d_out, d_in):
        g = self.circle(x, y, d_out)
        h = self.sk.addGeometry(Part.Circle(V(self.pd.val(x), self.pd.val(y), 0), V(0, 0, 1), self.pd.val(d_in) / 2))
        self._c(Sketcher.Constraint('Coincident', h, 3, g, 3))
        self._c(Sketcher.Constraint('Diameter', h, float(self.pd.val(d_in))), d_in)
        return g, h

    def rect(self, x, y, w, h):
        """Rectangle with its lower-left corner at (x, y), size w x h."""
        v = self.pd.val
        x0, y0 = v(x), v(y); x1, y1 = x0 + v(w), y0 + v(h)
        c = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
        g = [self.sk.addGeometry(Part.LineSegment(c[i], c[(i + 1) % 4])) for i in range(4)]
        for i in range(4):
            self._c(Sketcher.Constraint('Coincident', g[i], 2, g[(i + 1) % 4], 1))
        self._c(Sketcher.Constraint('Horizontal', g[0])); self._c(Sketcher.Constraint('Horizontal', g[2]))
        self._c(Sketcher.Constraint('Vertical', g[1])); self._c(Sketcher.Constraint('Vertical', g[3]))
        self.point(g[0], 1, x, y)
        self._c(Sketcher.Constraint('DistanceX', g[0], 1, g[0], 2, float(v(w))), w)
        self._c(Sketcher.Constraint('DistanceY', g[1], 1, g[1], 2, float(v(h))), h)
        return g

    def dshape(self, x, y, d, flat):
        """D-shaped hole: circle of diameter d centred at (x, y), cut by a chord at x + flat
        (flat > 0 keeps the material on +x, flat < 0 on -x)."""
        v = self.pd.val
        cx, cy, r, f = v(x), v(y), v(d) / 2, v(flat)
        a = math.acos(abs(f) / r)
        c = Part.Circle(V(cx, cy, 0), V(0, 0, 1), r)
        arc = Part.ArcOfCircle(c, a, 2 * math.pi - a) if f > 0 else Part.ArcOfCircle(c, -math.pi + a, math.pi - a)
        ga = self.sk.addGeometry(arc)
        gl = self.sk.addGeometry(Part.LineSegment(arc.EndPoint, arc.StartPoint))
        self._c(Sketcher.Constraint('Coincident', gl, 1, ga, 2)); self._c(Sketcher.Constraint('Coincident', gl, 2, ga, 1))
        self._c(Sketcher.Constraint('Vertical', gl))
        self.point(ga, 3, x, y)
        self._c(Sketcher.Constraint('Diameter', ga, float(2 * r)), d)
        self._c(Sketcher.Constraint('DistanceX', ga, 3, gl, 1, float(f)), flat)
        return ga, gl

    def polygon(self, pts):
        """Closed polygon through the vertices pts [(x, y), ...], each placed by DistanceX / DistanceY."""
        v = self.pd.val
        c = [V(v(x), v(y), 0) for x, y in pts]
        n = len(c)
        g = [self.sk.addGeometry(Part.LineSegment(c[i], c[(i + 1) % n])) for i in range(n)]
        for i in range(n):
            self._c(Sketcher.Constraint('Coincident', g[i], 2, g[(i + 1) % n], 1))
            self.point(g[i], 1, *pts[i])
        return g

    def sector(self, r0, r1, a0, a1):
        """Annular sector between radii r0 < r1 and angles a0 < a1 (degrees, numbers), centred on the origin."""
        n = V(0, 0, 1)
        t0, t1 = math.radians(a0), math.radians(a1)
        arcs = [self.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(0, 0, 0), n, r), t0, t1)) for r in (r0, r1)]
        pts = lambda r, t: V(r * math.cos(t), r * math.sin(t), 0)
        lines = [self.sk.addGeometry(Part.LineSegment(pts(r0, t), pts(r1, t))) for t in (t0, t1)]
        for k, (a, r) in enumerate(zip(arcs, (r0, r1))):
            self._c(Sketcher.Constraint('Coincident', a, 3, ROOT, 1))
            self._c(Sketcher.Constraint('Radius', a, float(r)))
        for j, ln in enumerate(lines):           # arc ends: 1 = start (a0), 2 = end (a1)
            self._c(Sketcher.Constraint('Coincident', ln, 1, arcs[0], j + 1))
            self._c(Sketcher.Constraint('Coincident', ln, 2, arcs[1], j + 1))
            self._c(Sketcher.Constraint('PointOnObject', ROOT, 1, ln))
        self._c(Sketcher.Constraint('Angle', lines[0], t0))
        self._c(Sketcher.Constraint('Angle', lines[1], t1))
        return arcs, lines

    def rrect(self, cx, cy, w, h, r):
        """Rectangle centred at (cx, cy), size w x h, corners rounded with radius r."""
        v = self.pd.val
        X, Y, hw, hh, rr = v(cx), v(cy), v(w) / 2, v(h) / 2, v(r)
        n = V(0, 0, 1)
        # arcs counter-clockwise (the solver swaps the ends of clockwise ones)
        ctr = [(X + hw - rr, Y + hh - rr), (X - hw + rr, Y + hh - rr), (X - hw + rr, Y - hh + rr), (X + hw - rr, Y - hh + rr)]
        arcs = [self.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(px, py, 0), n, rr), math.pi / 2 * k, math.pi / 2 * (k + 1)))
                for k, (px, py) in enumerate(ctr)]
        lines = []
        for k in range(4):
            a = self.sk.Geometry[arcs[k]].EndPoint
            b = self.sk.Geometry[arcs[(k + 1) % 4]].StartPoint
            lines.append(self.sk.addGeometry(Part.LineSegment(a, b)))
        for k in range(4):
            self._c(Sketcher.Constraint('Tangent', arcs[k], 2, lines[k], 1))
            self._c(Sketcher.Constraint('Tangent', lines[k], 2, arcs[(k + 1) % 4], 1))
        self._c(Sketcher.Constraint('Horizontal', lines[0])); self._c(Sketcher.Constraint('Vertical', lines[1]))
        self._c(Sketcher.Constraint('Horizontal', lines[2])); self._c(Sketcher.Constraint('Vertical', lines[3]))
        for k in range(1, 4):
            self._c(Sketcher.Constraint('Equal', arcs[0], arcs[k]))
        self._c(Sketcher.Constraint('Radius', arcs[0], rr), r)
        # size between the opposite lines, and the centre
        self._c(Sketcher.Constraint('DistanceX', arcs[1], 3, arcs[0], 3, 2 * (hw - rr)), '(%s) - 2 * (%s)' % (w, r) if isinstance(w, str) or isinstance(r, str) else None)
        self._c(Sketcher.Constraint('DistanceY', arcs[2], 3, arcs[1], 3, 2 * (hh - rr)), '(%s) - 2 * (%s)' % (h, r) if isinstance(h, str) or isinstance(r, str) else None)
        cxe = cx if isinstance(cx, str) else None
        cye = cy if isinstance(cy, str) else None
        self._c(Sketcher.Constraint('DistanceX', ROOT, 1, arcs[2], 3, X - hw + rr),
                '(%s) - (%s) / 2 + (%s)' % (cx, w, r) if (cxe or isinstance(w, str) or isinstance(r, str)) else None)
        self._c(Sketcher.Constraint('DistanceY', ROOT, 1, arcs[2], 3, Y - hh + rr),
                '(%s) - (%s) / 2 + (%s)' % (cy, h, r) if (cye or isinstance(h, str) or isinstance(r, str)) else None)
        return arcs, lines

    def edges(self, shape):
        """Every edge of a planar shape drawn in sketch coordinates (lines and circle arcs), each
        held by a Block constraint: computed outlines such as a groove, still fully constrained."""
        out = []
        for e in shape.Edges:
            c = e.Curve
            if isinstance(c, Part.Line):
                g = Part.LineSegment(e.Vertexes[0].Point, e.Vertexes[-1].Point)
            elif isinstance(c, Part.Circle) and e.isClosed():
                g = Part.Circle(V(c.Center.x, c.Center.y, 0), V(0, 0, 1), c.Radius)
            elif isinstance(c, Part.Circle):
                # through its ends and middle, counter-clockwise as the sketcher keeps arcs
                p0, pm, p1 = e.Vertexes[0].Point, e.valueAt((e.FirstParameter + e.LastParameter) / 2), e.Vertexes[-1].Point
                g = Part.ArcOfCircle(p0, pm, p1)
                if g.Axis.z < 0:
                    g = Part.ArcOfCircle(p1, pm, p0)
            else:
                raise ValueError('edges(): %s not supported' % type(c).__name__)
            out.append(self.sk.addGeometry(g))
        for g in out:
            self._c(Sketcher.Constraint('Block', g))
        return out

    def slot(self, x0, x1, y, d):
        """Slot along x between centres x0 and x1, width d."""
        v = self.pd.val
        a, b, yy, r = v(x0), v(x1), v(y), v(d) / 2
        n = V(0, 0, 1)
        g0 = self.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(a, yy, 0), n, r), math.pi / 2, 3 * math.pi / 2))
        g1 = self.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(b, yy, 0), n, r), -math.pi / 2, math.pi / 2))
        g2 = self.sk.addGeometry(Part.LineSegment(V(a, yy + r, 0), V(b, yy + r, 0)))
        g3 = self.sk.addGeometry(Part.LineSegment(V(a, yy - r, 0), V(b, yy - r, 0)))
        for c in (('Tangent', g0, 1, g2, 1), ('Tangent', g0, 2, g3, 1), ('Tangent', g1, 1, g3, 2),
                  ('Tangent', g1, 2, g2, 2)):
            self._c(Sketcher.Constraint(*c))
        self._c(Sketcher.Constraint('Horizontal', g2))
        self._c(Sketcher.Constraint('Equal', g0, g1))
        self._c(Sketcher.Constraint('Diameter', g0, float(2 * r)), d)
        self.point(g0, 3, x0, y)
        self._c(Sketcher.Constraint('DistanceX', ROOT, 1, g1, 3, float(b)), x1)
        return g0, g1, g2, g3
