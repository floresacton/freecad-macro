import Part
import FreeCAD as App
import math

def spread(input, curvature):
    x = input * 2 - 1
    mapped = (x - curvature * x) / (curvature - 2 * curvature * abs(x) + 1)
    return (mapped + 1) / 2

def cycloid_point(theta, teethp1, eccentricity, teethp1_ecc, outer_radius, outer_pin_radius):
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    
    teethp1_theta = teethp1 * theta
    sin_teethp1_theta = math.sin(teethp1_theta)
    cos_teethp1_theta = math.cos(teethp1_theta)

    x = outer_radius * sin_theta + eccentricity * sin_teethp1_theta
    y = outer_radius * cos_theta + eccentricity * cos_teethp1_theta

    dx = outer_radius * cos_theta + teethp1_ecc * cos_teethp1_theta
    dy = -outer_radius * sin_theta - teethp1_ecc * sin_teethp1_theta

    length = math.hypot(dx, dy)

    px = x + dy / length * outer_pin_radius
    py = y - dx / length * outer_pin_radius

    return (px, py)

class Cycloid:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyQuantity","Teeth").Teeth = 23
        obj.addProperty("App::PropertyLength","Eccentricity").Eccentricity = 1
        obj.addProperty("App::PropertyLength","OuterDiameter").OuterDiameter = 52
        obj.addProperty("App::PropertyLength","OuterPinDiameter").OuterPinDiameter = 4
        obj.addProperty("App::PropertyLength","Height").Height = 4
        obj.addProperty("App::PropertyQuantity","PointsPerTooth").PointsPerTooth = 200

    def execute(self, obj):
        teeth = int(obj.Teeth)
        eccentricity = float(obj.Eccentricity)
        outer_diameter = float(obj.OuterDiameter)
        outer_pin_diameter = float(obj.OuterPinDiameter)
        height = float(obj.Height)
        points_per_tooth = int(obj.PointsPerTooth)
        
        tooth_edge = self.tooth_edge(teeth, eccentricity, outer_diameter, outer_pin_diameter, points_per_tooth)
        
        center = App.Vector(0, 0, 0)
        axis = App.Vector(0, 0, 1)
        tooth_angle = 360/teeth
        
        edges = [tooth_edge]
        for t in range(1, teeth):
            edge_copy = tooth_edge.copy()
            edge_copy.rotate(center, axis, t*tooth_angle)
            edges.append(edge_copy)
            
        wire = Part.Wire(edges)
        wire.translate(App.Vector(0,0,-height/2))
        face = Part.Face(wire)
     
        obj.Shape = face.extrude(App.Vector(0, 0, height))
        
    def tooth_edge(self, teeth, eccentricity, outer_diameter, outer_pin_diameter, points_per_tooth):
        teethp1 = teeth + 1
        teethp1_ecc = eccentricity * teethp1
        
        outer_pin_radius = outer_pin_diameter / 2
        outer_radius = outer_diameter / 2

        radians_per_tooth = 2 * math.pi / teeth

        points = [None] * (points_per_tooth + 1)
        
        for p in range(points_per_tooth+1):
            theta = spread(p / points_per_tooth, 0.65) * radians_per_tooth
            
            x, y = cycloid_point(theta, teethp1, eccentricity, teethp1_ecc, outer_radius, outer_pin_radius)
            
            points[p] = App.Vector(x, y, 0)
        
        spline = Part.BSplineCurve()
        spline.interpolate(points)

        return spline.toShape()

def make_cycloid():
    obj = App.ActiveDocument.addObject("Part::FeaturePython","Cycloid")
    Cycloid(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()
