import Part
import FreeCAD as App
import math

class Cycloid:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyQuantity","Teeth").Teeth = 23
        obj.addProperty("App::PropertyLength","Eccentricity").Eccentricity = 1
        obj.addProperty("App::PropertyLength","OuterDiameter").OuterDiameter = 52
        obj.addProperty("App::PropertyLength","OuterPinDiameter").OuterPinDiameter = 4
        obj.addProperty("App::PropertyLength","Height").Height = 4
        
        self.points_per_tooth = 50
        self.curvature = 0.65

    def execute(self, obj):
        spline = Part.BSplineCurve()
        spline.interpolate(self.cycloid_points(obj))

        edge = spline.toShape()
        wire = Part.Wire(edge)
        face = Part.Face(wire)

        height = float(obj.Height)
        prism = face.extrude(App.Vector(0, 0, height / 2))
        neg_prism = face.extrude(App.Vector(0, 0, -height / 2))
     
        obj.Shape = prism.fuse(neg_prism)
        
    def cycloid_points(self, obj):
        teeth = int(obj.Teeth)
        eccentricity = float(obj.Eccentricity)
        outer_diameter = float(obj.OuterDiameter)
        outer_pin_diameter = float(obj.OuterPinDiameter)
        points_per_tooth = 50
        
        teeth_plus_one = teeth + 1
        outer_pin_radius = outer_pin_diameter / 2
        outer_radius = outer_diameter / 2

        radians_per_tooth = 2 * math.pi / teeth

        profile_points = []

        for tooth_index in range(teeth):
            for point_index in range(points_per_tooth):
                tooth_fraction = point_index / points_per_tooth
                theta = (tooth_index + self.spread_map(tooth_fraction)) * radians_per_tooth

            x = (outer_radius * math.sin(theta) + eccentricity * math.sin(teeth_plus_one * theta))
            y = (outer_radius * math.cos(theta) + eccentricity * math.cos(teeth_plus_one * theta))

            dx = outer_radius * math.cos(theta) + eccentricity * teeth_plus_one * math.cos(teeth_plus_one * theta)
            dy = -outer_radius * math.sin(theta) - eccentricity * teeth_plus_one * math.sin(teeth_plus_one * theta)

            tangent_length = math.sqrt(dx * dx + dy * dy)

            px = x + dy / tangent_length * outer_pin_radius
            py = y - dx / tangent_length * outer_pin_radius

            profile_points.append(App.Vector(px, py, 0))

        profile_points.append(profile_points[0])
        return profile_points
        
    def spread_map(self, input):
        x = input * 2 - 1
        mapped = (x - self.curvature * x) / (self.curvature - 2 * self.curvature * abs(x) + 1)
        return (mapped + 1) / 2

def make_cycloid():
    obj = App.ActiveDocument.addObject("Part::FeaturePython","Cycloid")
    Cycloid(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()

make_cycloid()
