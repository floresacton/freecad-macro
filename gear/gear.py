import Part
import FreeCAD as App
import math

def frange(start, stop, step):
    while start < stop:
        yield round(start, 10)
        start += step

def rotate(point, angle):
    x = point[0] * math.cos(angle) - point[1] * math.sin(angle)
    y = point[0] * math.sin(angle) + point[1] * math.cos(angle)
    return (x,y,)

class Gear:
    def __init__(self, obj):
      obj.Proxy = self
      obj.addProperty("App::PropertyQuantity","Teeth").Teeth = 4
      obj.addProperty("App::PropertyLength","Module").Module = 2
      obj.addProperty("App::PropertyLength","Height").Height = 2
      obj.addProperty("App::PropertyAngle","HelixAngle").HelixAngle = 20
      obj.addProperty("App::PropertyAngle","PressureAngle").PressureAngle = 20

    def execute(self, obj):
        points = 40
        loft_step = 0.25 # steps per tooth
        #clearance_factor = 1.0
        #backlash = 0.0
        
        teeth = int(obj.Teeth)
        module = float(obj.Module)
        height = float(obj.Height)
        helix_angle = float(obj.HelixAngle)/180 * math.pi
        pressure_angle = float(obj.PressureAngle)/180 * math.pi
        
        pitch_radius = teeth * module / 2.0
        base_radius = pitch_radius * math.cos(pressure_angle)
        
        alpha = math.sqrt(pitch_radius**2 - base_radius**2) / base_radius - pressure_angle
        beta = (math.pi/2) / teeth - alpha

        dedendum = module # add clearance factor here
        addendum = module # add clearance factor here

        dedendum_radius = pitch_radius - dedendum
        addendum_radius = pitch_radius + addendum

        if helix_angle != 0:
            lead = 2 * math.pi * pitch_radius / math.tan(helix_angle)

        # start logic here
        dedendum_line = base_radius > dedendum_radius

        involute_points = self.involute_points(beta, base_radius, addendum_radius, dedendum_radius, points)
    
        wire_list = []

        first_point = None
        last_point = None

        for tooth_index in range(teeth):
            spline1_points = []
            spline2_points = []

            for point in involute_points:
                p1 = (point[1], point[0])
                p1 = rotate(p1, (math.pi/teeth) * (1 + 2*tooth_index))
                spline1_points.append(App.Vector(p1[0], p1[1], 0))

                p2 = (-point[1], point[0])
                p2 = rotate(p2, (math.pi/teeth) * (1 + 2*tooth_index))
                spline2_points.append(App.Vector(p2[0], p2[1], 0))

            spline1 = Part.BSplineCurve()
            spline1.interpolate(spline1_points)

            spline2 = Part.BSplineCurve()
            spline2.interpolate(spline2_points)

            if tooth_index == 0:
                first_point = spline1_points[-1]
            else:
                wire_list.append(Part.makeLine(spline1_points[-1], last_point))
            
            wire_list.append(spline1.toShape())
            
            if dedendum_line:
                length = math.sqrt(spline1_points[0].x**2 + spline1_points[0].y**2)
                scalar = dedendum_radius/length
                
                dedendum_point1 = App.Vector(spline1_points[0].x*scalar, spline1_points[0].y*scalar, 0)
                dedendum_point2 = App.Vector(spline2_points[0].x*scalar, spline2_points[0].y*scalar, 0)
                
                wire_list.append(Part.makeLine(spline1_points[0], dedendum_point1))
                wire_list.append(Part.makeLine(dedendum_point1, dedendum_point2))
                wire_list.append(Part.makeLine(dedendum_point2, spline2_points[0]))
            else:
                wire_list.append(Part.makeLine(spline1_points[0], spline2_points[0]))
            
            wire_list.append(spline2.toShape())

            if tooth_index == teeth-1:
                wire_list.append(Part.makeLine(spline2_points[-1], first_point))

            last_point = spline2_points[-1]

        base_wire = Part.Wire(wire_list)
        
        angle_per_tooth = 360/teeth
        angle_step = angle_per_tooth*loft_step
        if helix_angle != 0:
            angle_per_height = 360/lead
            angle_total = angle_per_height * height
            steps = math.ceil(angle_total/angle_step)
        else:
            steps = 1
            angle_per_height = 0
        
        wires_top = []
        wires_bottom = []
        for index in range(1, steps + 1):
            z = height * index / steps
            angle_deg = angle_per_height * z
            
            wire_top = base_wire.copy()
            wire_bottom = base_wire.copy()
            
            wire_top.rotate(App.Vector(0,0,1), App.Vector(0,0,1), angle_deg)
            wire_top.translate(App.Vector(0,0,z))
            
            wire_bottom.rotate(App.Vector(0,0,1), App.Vector(0,0,1), angle_deg)
            wire_bottom.translate(App.Vector(0,0,-z))
            
            wires_top.append(wire_top)
            wires_bottom.append(wire_bottom)

        wires_bottom.reverse()
        wires_bottom.append(base_wire)
        wires_bottom.extend(wires_top)

        obj.Shape = Part.makeLoft(wires_bottom, True, True)
        
    def involute_points(self, beta, base_radius, addendum_radius, dedendum_radius, points):
        involute = []

        angle_start = 0
        if base_radius <= dedendum_radius:
            angle_start = math.sqrt((dedendum_radius / base_radius)**2 - 1)

        angle_end = math.sqrt((addendum_radius / (base_radius))**2 - 1)
        angle_step = (angle_end - angle_start) / points
        for angle in frange(angle_start, angle_end, angle_step):
            cos_theta = math.cos(angle + beta)
            sin_theta = math.sin(angle + beta)

            x = base_radius * (cos_theta + angle * sin_theta)
            y = base_radius * (sin_theta - angle * cos_theta)

            involute.append((x, y,))

        return involute

def make_gear():
    obj = App.ActiveDocument.addObject("Part::FeaturePython","Gear")
    Gear(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()
