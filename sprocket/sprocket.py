import Part
import FreeCAD as App
import math


# https://www.chiefdelphi.com/t/sprocket-design-tutorial/387449
class Sprocket:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyQuantity", "Teeth").Teeth = 12
        obj.addProperty("App::PropertyLength", "Pitch").Pitch = 12.7
        obj.addProperty("App::PropertyLength", "Height").Height = 3
        obj.addProperty("App::PropertyLength", "SeatRadius").SeatRadius = 3.95
        # 0 = no clearance 1 = full lobe
        obj.addProperty(
            "App::PropertyQuantity", "PitchClearFactor"
        ).PitchClearFactor = 0.4
        # 0 = no clearance up to something
        obj.addProperty(
            "App::PropertyQuantity", "SeatClearFactor"
        ).SeatClearFactor = 0.8
        # this will probably have to change for different gear tooth count
        obj.addProperty("App::PropertyAngle", "SeatClearAngle").SeatClearAngle = 35

    def execute(self, obj):
        teeth = int(obj.Teeth)
        pitch = float(obj.Pitch)
        height = float(obj.Height)
        arc1radius = float(obj.SeatRadius)

        arc3radius_factor = float(obj.PitchClearFactor)
        arc2radius_factor = float(obj.SeatClearFactor)
        arc1angle_factor = float(obj.SeatClearAngle) * math.pi / 180

        # general parameters
        tooth_angle_half = math.pi / teeth
        tooth_angle = tooth_angle_half * 2
        pitch_radius = pitch / (2 * math.sin(tooth_angle_half))

        # arc clearance parameters
        arc1angle = math.pi / 2 - tooth_angle_half - arc1angle_factor
        arc2radius = arc1radius * (1 + arc2radius_factor)

        # clearance arc center
        extra_dist = arc2radius_factor * arc1radius
        arc2cx = pitch_radius + extra_dist * math.cos(arc1angle)
        arc2cy = -extra_dist * math.sin(arc1angle)

        # next tooth center
        slot2x = pitch_radius * math.cos(tooth_angle)
        slot2y = pitch_radius * math.sin(tooth_angle)

        # vector from second to first
        slot_dx = pitch_radius - slot2x
        slot_dy = -slot2y

        # change to move along centerline
        center3dx = slot_dx * arc3radius_factor / 2
        center3dy = slot_dy * arc3radius_factor / 2

        # pitch arc parameters
        arc3cx = slot2x + center3dx
        arc3cy = slot2y + center3dy
        arc3radius = math.hypot(arc3cx - arc2cx, arc3cy - arc2cy) - arc2radius

        # arc2angle and arc3angle are arc angles
        diffangle = math.atan2(arc3cy - arc2cy, arc2cx - arc3cx)
        arc2angle = diffangle - arc1angle

        middlex = (slot2x + pitch_radius) / 2
        middley = slot2y / 2

        dy = pitch_radius - middlex
        dx = middley

        # arc3radius**2 = (middlex - arc3cx + dx * f)**2 + (middley - arc3cy + dy * f)**2
        # 0 = (dx**2 + dy**2) * f**2 + f*2*(dx*(middlex - arc3cx) + dy*(middley-arc3cy))
        # + (middlex - arc3cx)**2 +  (middley - arc3cy)**2 - arc3radius**2

        # -b +- sqrt(b**2 -4ac)/2a
        a = dx**2 + dy**2
        b = 2 * (dx * (middlex - arc3cx) + dy * (middley - arc3cy))
        c = (middlex - arc3cx) ** 2 + (middley - arc3cy) ** 2 - arc3radius**2

        # factor up the middle perpendicular
        fsol = (math.sqrt(b**2 - 4 * a * c) - b) / (2 * a)
        endx = middlex + dx * fsol
        endy = middley + dy * fsol

        arc3angle = arc1angle + arc2angle - math.atan2(arc3cy - endy, endx - arc3cx)

        # arc 1
        arc1p1 = App.Vector(pitch_radius - arc1radius, 0, 0)
        arc1p2 = App.Vector(
            pitch_radius - arc1radius * math.cos(arc1angle / 2),
            arc1radius * math.sin(arc1angle / 2),
            0,
        )
        arc1p3 = App.Vector(
            pitch_radius - arc1radius * math.cos(arc1angle),
            arc1radius * math.sin(arc1angle),
            0,
        )

        # arc 2
        arc2p2 = App.Vector(
            arc2cx - arc2radius * math.cos(arc1angle + arc2angle / 2),
            arc2cy + arc2radius * math.sin(arc1angle + arc2angle / 2),
            0,
        )
        arc2p3 = App.Vector(
            arc2cx - arc2radius * math.cos(arc1angle + arc2angle),
            arc2cy + arc2radius * math.sin(arc1angle + arc2angle),
            0,
        )

        # arc 3
        arc3p2 = App.Vector(
            arc3cx + arc3radius * math.cos(arc1angle + arc2angle - arc3angle / 2),
            arc3cy - arc3radius * math.sin(arc1angle + arc2angle - arc3angle / 2),
            0,
        )
        arc3p3 = App.Vector(
            arc3cx + arc3radius * math.cos(arc1angle + arc2angle - arc3angle),
            arc3cy - arc3radius * math.sin(arc1angle + arc2angle - arc3angle),
            0,
        )

        arc1 = Part.Arc(arc1p1, arc1p2, arc1p3)
        arc3 = Part.Arc(arc2p3, arc3p2, arc3p3)

        if arc1angle_factor == 0:
            edges = [arc1.toShape(), arc3.toShape()]
        else:
            arc2 = Part.Arc(arc1p3, arc2p2, arc2p3)
            edges = [arc1.toShape(), arc2.toShape(), arc3.toShape()]

        center = App.Vector(0, 0, 0)
        xaxis = App.Vector(1, 0, 0)
        zaxis = App.Vector(0, 0, 1)

        tooth_edges = edges.copy()
        num_edges = len(edges)
        for i in range(num_edges):
            tooth_edges.append(
                edges[num_edges - 1 - i]
                .copy()
                .rotate(center, xaxis, 180)
                .rotate(center, zaxis, 360 / teeth)
            )

        all_edges = tooth_edges.copy()
        for t in range(1, teeth):
            for edge in tooth_edges:
                all_edges.append(edge.copy().rotate(center, zaxis, 360 / teeth * t))

        wire = Part.Wire(all_edges)
        face = Part.Face(wire)

        obj.Shape = face.extrude(App.Vector(0, 0, height))


def make_sprocket():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Sprocket")
    Sprocket(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()
