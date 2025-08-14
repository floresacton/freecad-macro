import Part
import FreeCAD as App
import math

def point(x, y):
    return App.Vector(x, y, 0)

def line(p1, p2):
    return Part.makeLine(p1, p2)

def arc(p1, p2, p3):
    return Part.Edge(Part.Arc(p1, p2, p3))

def round_rect(widthd2, heightd2, radius):
    width = widthd2
    height = heightd2

    edges = []
    if radius == 0:
        p1 = point(width, height)
        p2 = point(-width, height)
        p3 = point(-width, -height)
        p4 = point(width, -height)

        edges.append(line(p1, p2))
        edges.append(line(p2, p3))
        edges.append(line(p3, p4))
        edges.append(line(p4, p1))
        return Part.Wire(edges)

    comp_width = width - radius
    comp_height = height - radius
    arc_distance = radius * math.sqrt(2)/2
    arc_width = comp_width + arc_distance
    arc_height = comp_height + arc_distance

    p1a = point(width, comp_height)
    p1b = point(comp_width, height)
    p2a = point(-comp_width, height)
    p2b = point(-width, comp_height)
    p3a = point(-width, -comp_height)
    p3b = point(-comp_width, -height)
    p4a = point(comp_width, -height)
    p4b = point(width, -comp_height)
    
    edges.append(arc(p1a, point(arc_width, arc_height), p1b))
    edges.append(line(p1b, p2a))
    edges.append(arc(p2a, point(-arc_width, arc_height), p2b))
    edges.append(line(p2b, p3a))
    edges.append(arc(p3a, point(-arc_width, -arc_height), p3b))
    edges.append(line(p3b, p4a))
    edges.append(arc(p4a, point(arc_width, -arc_height), p4b))
    edges.append(line(p4b, p1a))

    return Part.Wire(edges)

class Tube:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLength","Width").Width = 25.4
        obj.addProperty("App::PropertyLength","Height").Height = 25.4
        obj.addProperty("App::PropertyLength","Fillet").Fillet = 5
        obj.addProperty("App::PropertyLength","Thickness").Thickness = 3
        obj.addProperty("App::PropertyLength","Length").Length = 250

    def execute(self, obj):
        widthd2 = float(obj.Width) / 2
        heightd2 = float(obj.Height) / 2
        fillet = float(obj.Fillet)
        thickness = float(obj.Thickness)
        length = float(obj.Length)

        outer = round_rect(widthd2, heightd2, fillet)
        inner = round_rect(widthd2-thickness, heightd2-thickness, max(0, fillet-thickness))

        face = Part.makeFace([outer, inner])
        face.translate(App.Vector(0, 0, -length/2))
        obj.Shape = face.extrude(App.Vector(0, 0, length))
 
def make_tube():
    obj = App.ActiveDocument.addObject("Part::FeaturePython","Tube")
    Tube(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()

