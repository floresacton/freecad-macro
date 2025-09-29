import Part
import FreeCAD as App

import numpy as np
from scipy.optimize import least_squares, fsolve
import math


def mirror_x(v):
    return App.Vector(-v.x, v.y, 0)


# (t, 1)
# rotate by t radians (or more for extra)


def trochoid_point(
    param, trochoid_beta, trochoid_distance, dedendum_radius, pitch_radius
):
    theta = trochoid_beta - param

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    temp = pitch_radius * param - trochoid_distance

    x = dedendum_radius * sin_theta + temp * cos_theta
    y = dedendum_radius * cos_theta - temp * sin_theta

    return np.array([x, y])


def involute_point(param, involute_beta, base_radius):
    theta = involute_beta + param

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    temp = base_radius * param

    x = temp * sin_theta + base_radius * cos_theta
    y = temp * cos_theta - base_radius * sin_theta

    return np.array([x, y])


def tooth_edges(
    teeth,
    module,
    pressure_angle,
    backlash_factor,
    dedendum_factor,
    addendum_factor,
    profile_shift_factor,
    points_per_tooth,
):
    backlash = module * backlash_factor
    profile_shift = module * profile_shift_factor
    dedendum = module * dedendum_factor - profile_shift
    addendum = module * addendum_factor + profile_shift

    pitch_radius = module * teeth / 2
    base_radius = pitch_radius * math.cos(pressure_angle)
    dedendum_radius = pitch_radius - dedendum
    addendum_radius = pitch_radius + addendum

    tan_pressure = math.tan(pressure_angle)

    delta_arc = 2 * profile_shift * tan_pressure - backlash
    delta_angle = delta_arc / pitch_radius / 2

    involute_beta = pressure_angle - tan_pressure - (math.pi / 2) / teeth - delta_angle
    trochoid_beta = (math.pi / 2) - (math.pi / 2) / teeth - delta_angle

    trochoid_distance = dedendum * tan_pressure

    def func(
        params,
        trochoid_beta,
        trochoid_distance,
        dedendum_radius,
        pitch_radius,
        involute_beta,
        base_radius,
    ):
        t1, t2 = params
        p1 = trochoid_point(
            t1, trochoid_beta, trochoid_distance, dedendum_radius, pitch_radius
        )
        p2 = involute_point(t2, involute_beta, base_radius)
        return p1 - p2

    initial_guess = [0.5, 0.5]
    lower_bounds = [0, 0]
    upper_bounds = [2, 2]
    result = least_squares(
        func,
        initial_guess,
        bounds=(lower_bounds, upper_bounds),
        args=(
            trochoid_beta,
            trochoid_distance,
            dedendum_radius,
            pitch_radius,
            involute_beta,
            base_radius,
        ),
    )

    if not result.success:
        print("optimizer fail")

    trochoid_end, involute_start = result.x

    trochoid_start = trochoid_distance / pitch_radius
    trochoid_step = (trochoid_end - trochoid_start) / points_per_tooth

    trochoid_points = [None] * (points_per_tooth + 1)
    for i in range(points_per_tooth + 1):
        param = trochoid_start + i * trochoid_step

        x, y = trochoid_point(
            param, trochoid_beta, trochoid_distance, dedendum_radius, pitch_radius
        )

        trochoid_points[i] = App.Vector(x, y, 0)

    trochoid = Part.BSplineCurve()
    trochoid.interpolate(trochoid_points)
    trochoid_edge = trochoid.toShape()

    involute_end = math.sqrt((addendum_radius / (base_radius)) ** 2 - 1)

    _, involute_end_y = involute_point(involute_end, involute_beta, base_radius)

    keep_outer_arc = involute_end_y > 0
    if involute_end_y < 0:
        print("Involute clip before adendum")

        def func(theta):
            return (theta - involute_beta) * math.cos(theta) - math.sin(theta)

        theta_guess = involute_beta + involute_end
        theta_solution = fsolve(func, theta_guess)[0]

        involute_end = theta_solution - involute_beta

    involute_step = (involute_end - involute_start) / points_per_tooth

    involute_points = [None] * (points_per_tooth + 1)
    involute_points[0] = trochoid_points[-1]
    for i in range(1, points_per_tooth + 1):
        param = involute_start + i * involute_step

        x, y = involute_point(param, involute_beta, base_radius)

        involute_points[i] = App.Vector(x, y, 0)

    involute = Part.BSplineCurve()
    involute.interpolate(involute_points)
    involute_edge = involute.toShape()

    edges = [involute_edge, trochoid_edge]

    if keep_outer_arc:
        start = App.Vector(addendum_radius, 0)
        midpoint = involute_points[-1].add(start).multiply(0.5)

        center_arc = Part.Arc(
            start,
            midpoint.normalize().multiply(addendum_radius),
            involute_points[-1],
        )
        edges = [center_arc.toShape()] + edges

    last_point = App.Vector(trochoid_points[0].x, trochoid_points[0].y, 0)

    half_ang = math.pi / teeth
    center_dedendum = App.Vector(math.cos(half_ang), math.sin(half_ang), 0).multiply(
        dedendum_radius
    )
    midpoint = (last_point.add(center_dedendum)).multiply(0.5)

    end_arc = Part.Arc(
        last_point, midpoint.normalize().multiply(dedendum_radius), center_dedendum
    )
    edges.append(end_arc.toShape())

    center = App.Vector(0, 0, 0)
    xaxis = App.Vector(1, 0, 0)
    zaxis = App.Vector(0, 0, 1)

    new = edges.copy()
    num_edges = len(edges)
    for i in range(num_edges):
        new.append(
            edges[num_edges - 1 - i]
            .copy()
            .rotate(center, xaxis, 180)
            .rotate(center, zaxis, 360 / teeth)
        )

    return new


class Gear:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyQuantity", "Teeth").Teeth = 12
        obj.addProperty("App::PropertyLength", "Module").Module = 2
        obj.addProperty("App::PropertyLength", "Height").Height = 6
        obj.addProperty("App::PropertyAngle", "HelixAngle").HelixAngle = 0
        obj.addProperty("App::PropertyBool", "DoubleHelix").DoubleHelix = True
        obj.addProperty("App::PropertyBool", "ReverseHelix").ReverseHelix = False
        obj.addProperty("App::PropertyAngle", "PressureAngle").PressureAngle = 20
        obj.addProperty("App::PropertyQuantity", "BacklashFactor").BacklashFactor = 0
        obj.addProperty("App::PropertyQuantity", "DedendumFactor").DedendumFactor = 1.25
        obj.addProperty("App::PropertyQuantity", "AddendumFactor").AddendumFactor = 1
        obj.addProperty(
            "App::PropertyQuantity", "ProfileShiftFactor"
        ).ProfileShiftFactor = 0
        obj.addProperty("App::PropertyQuantity", "PointsPerTooth").PointsPerTooth = 40
        obj.addProperty("App::PropertyLength", "SecondRadius").SecondRadius = 0
        obj.addProperty("App::PropertyQuantity", "TeethOverride").TeethOverride = 0

    def execute(self, obj):
        teeth = int(obj.Teeth)
        module = float(obj.Module)
        height = float(obj.Height)
        helix_angle = math.radians(float(obj.HelixAngle))
        double_helix = bool(obj.DoubleHelix)
        reverse_helix = bool(obj.ReverseHelix)
        pressure_angle = math.radians(float(obj.PressureAngle))
        backlash_factor = float(obj.BacklashFactor)
        dedendum_factor = float(obj.DedendumFactor)
        addendum_factor = float(obj.AddendumFactor)
        profile_shift_factor = float(obj.ProfileShiftFactor)
        points_per_tooth = int(obj.PointsPerTooth)
        second_radius = float(obj.SecondRadius)
        teeth_override = int(obj.TeethOverride)

        internal = second_radius > teeth * module / 2
        if internal:
            addendum_factor, dedendum_factor = dedendum_factor, addendum_factor
            backlash_factor = -backlash_factor

        edges = tooth_edges(
            teeth,
            module,
            pressure_angle,
            backlash_factor,
            dedendum_factor,
            addendum_factor,
            profile_shift_factor,
            points_per_tooth,
        )

        pitch_radius = teeth * module / 2
        profile_shift = module * profile_shift_factor
        addendum = module * addendum_factor + profile_shift
        addendum_radius = pitch_radius + addendum

        angle_per_tooth = 360 / teeth

        center = App.Vector(0, 0, 0)
        xaxis = App.Vector(1, 0, 0)
        zaxis = App.Vector(0, 0, 1)

        edges_copy = edges.copy()

        if teeth_override != 0:
            teeth = teeth_override

        for t in range(1, teeth):
            angle = t * angle_per_tooth
            for edge in edges_copy:
                edge_copy = edge.copy()
                edge_copy.rotate(center, zaxis, angle)
                edges.append(edge_copy)

        if teeth_override != 0:
            last = Part.makeLine(
                App.Vector(second_radius, 0, 0), App.Vector(addendum_radius, 0, 0)
            )
            first = last.copy().rotate(center, zaxis, angle_per_tooth * teeth)
            edges.append(first)
            if second_radius != 0:
                p1, p2 = first.Vertexes[0].Point, last.Vertexes[0].Point
                midpoint = p1.add(p2).multiply(0.5)
                arc = Part.Arc(p1, midpoint.normalize().multiply(second_radius), p2)
                edges.append(arc.toShape())

            edges.append(last)

        if teeth_override:
            wire = Part.Wire(edges)
        else:
            wire = Part.Wire(edges)

        heightd2 = height / 2

        if helix_angle == 0:
            wire.translate(App.Vector(0, 0, -heightd2))

            if second_radius != 0 and teeth_override == 0:
                circle = Part.Circle(
                    App.Vector(0, 0, -heightd2), App.Vector(0, 0, -1), second_radius
                )
                circle_wire = Part.Wire([circle.toShape()])
                if internal:
                    face = Part.Face([circle_wire, wire])
                else:
                    face = Part.Face([wire, circle_wire])
            else:
                face = Part.Face(wire)

            obj.Shape = face.extrude(App.Vector(0, 0, height))
        else:
            lead = 2 * math.pi * pitch_radius / math.tan(helix_angle)

            helix = Part.makeHelix(lead, heightd2, 1, 0, reverse_helix)

            pipe_shell = Part.BRepOffsetAPI.MakePipeShell(helix)
            pipe_shell.setFrenetMode(True)
            pipe_shell.add(wire)
            pipe_shell.build()

            wire_top = pipe_shell.lastShape()

            shell_faces = []
            if second_radius == 0:
                face_top = Part.Face([wire_top])
            else:
                circle = Part.Circle(
                    App.Vector(0, 0, heightd2), App.Vector(0, 0, -1), second_radius
                )
                circle_wire = Part.Wire([circle.toShape()])
                shell = circle_wire.extrude(App.Vector(0, 0, -height))
                tube_face = shell.Faces[0]
                shell_faces.append(tube_face)

                if internal:
                    face_top = Part.Face([circle_wire, wire_top])
                else:
                    face_top = Part.Face([wire_top, circle_wire])

            shell_top = pipe_shell.shape().Faces + [face_top]
            shell_faces += shell_top.copy()

            for face in shell_top:
                if double_helix:
                    new_face = face.mirror(center, zaxis)
                else:
                    new_face = face.copy().rotate(center, xaxis, 180)
                shell_faces.append(new_face)

            shell = Part.makeShell(shell_faces)

            obj.Shape = Part.makeSolid(shell)


def make_gear():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Gear")
    Gear(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()
