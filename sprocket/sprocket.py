import Part
import FreeCAD as App


# https://www.chiefdelphi.com/t/sprocket-design-tutorial/387449
class Sprocket:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyQuantity", "Teeth").Teeth = 12
        obj.addProperty("App::PropertyLength", "Pitch").Pitch = 12.7
        obj.addProperty(
            "App::PropertyLength", "PitchClearFactor"
        ).PitchClearFactor = 0.2  # 0 = no clearance 0.5 = full lobe
        obj.addProperty("App::PropertyLength", "SeatRadius").SeatRadius = 3.175
        obj.addProperty(
            "App::PropertyLength", "SeatClearFactor"
        ).SeatClearFactor = 0.8  # 0 = no clearance
        obj.addProperty("App::PropertyLength", "Height").Height = 3

    def execute(self, obj):
        teeth = int(obj.Teeth)
        pitch = float(obj.Pitch)
        height = float(obj.Height)

        seat_radius = float(obj.SeatRadius)
        seat_clear_factor = float(obj.SeatClearFactor)
        pitch_clear_factor = float(obj.PitchClearFactor)

        tooth_angle = 2 * math.pi / teeth
        pitch_radius = pitch / (2 * sin(tooth_angle / 2))
        seat_clear_radius = seat_radius * (1 + seat_clear_factor)
        pitch_clear_radius = pitch * (1 - pitch_clear_factor)

        secondx = pitch_radius * cos(tooth_angle)
        secondy = pitch_radius * sin(tooth_angle)

        obj.Shape = Part.makeSolid(shell)


def make_sprocket():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Sprocket")
    Sprocket(obj)
    obj.ViewObject.Proxy = 0
    App.ActiveDocument.recompute()
