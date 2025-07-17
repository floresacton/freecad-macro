import Part
import FreeCAD as App
import math

class cycloid:
  def __init__(self, obj):
    obj.Proxy = self
    obj.addProperty("App::PropertyQuantity","Teeth")
    obj.addProperty("App::PropertyLength","Eccentricity")
    obj.addProperty("App::PropertyLength","OuterDiameter")
    obj.addProperty("App::PropertyLength","OuterPinDiameter")
    obj.addProperty("App::PropertyLength","Height")
    
    self.pointsPerTooth = 50
    self.curvature = 0.65

  def execute(self, obj):
    spline = Part.BSplineCurve()
    spline.interpolate(self.cycloidPoints(obj))

    edge = spline.toShape()
    wire = Part.Wire(edge)
    face = Part.Face(wire)

    height = float(obj.Height)
    prism = face.extrude(App.Vector(0, 0, height / 2))
    neg_prism = face.extrude(App.Vector(0, 0, -height / 2))
 
    obj.Shape = prism.fuse(neg_prism)
    
  def cycloidPoints(self, obj):
    teeth = int(obj.Teeth)
    eccentricity = float(obj.Eccentricity)
    outerDiameter = float(obj.OuterDiameter)
    outerPinDiameter = float(obj.OuterPinDiameter)
    pointsPerTooth = 50
    
    teethPlusOne = teeth + 1
    outerPinRadius = outerPinDiameter / 2
    outerRadius = outerDiameter / 2

    radiansPerTooth = 2 * math.pi / teeth

    points = []

    for t in range(teeth):
      for p in range(pointsPerTooth):
        toothFrac = p / pointsPerTooth
        theta = (t + self.spread(toothFrac)) * radiansPerTooth

        x = (outerRadius * math.sin(theta) + eccentricity * math.sin(teethPlusOne * theta))
        y = (outerRadius * math.cos(theta) + eccentricity * math.cos(teethPlusOne * theta))

        dx = outerRadius * math.cos(theta) + eccentricity * teethPlusOne * math.cos(teethPlusOne * theta)
        dy = -outerRadius * math.sin(theta) - eccentricity * teethPlusOne * math.sin(teethPlusOne * theta)

        length = math.sqrt(dx * dx + dy * dy)

        px = x + dy / length * outerPinRadius
        py = y - dx / length * outerPinRadius

        points.append(App.Vector(px, py, 0))

    points.append(points[0])
    return points
    
  def spread(self, input):
    x = input * 2 - 1
    mapped = (x - self.curvature * x) / (self.curvature - 2 * self.curvature * abs(x) + 1)
    return (mapped + 1) / 2


def makeCycloid():
  obj = App.ActiveDocument.addObject("Part::FeaturePython","Cycloid")
  cycloid(obj)
  obj.ViewObject.Proxy = 0
  App.ActiveDocument.recompute()
