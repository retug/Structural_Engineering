# Python Imports
import os
import json
import math
from pathlib import Path

# RAM Concept API imports
from ram_concept.concept import Concept
from ram_concept.model import DesignCode
from ram_concept.model import StructureType

# RAM Concept rebar imports
from ram_concept.enums import BarEnd
from ram_concept.enums import ElevationReference
from ram_concept.enums import SlabFace
from ram_concept.enums import SpanSet
from ram_concept.point_2D import Point2D
from ram_concept.polygon_2D import Polygon2D


# --------------------------------------------------
# USER PATHS
# --------------------------------------------------

user_directory = str(Path.home())

json_file_path = (
    r"C:\Users\16142\Desktop\Retug\Own Work\RAMConcept"
    r"\RAMConceptPresentation\Python Files\04 - Drafting Automation"
    r"\01 - Mild Rebar Script\Text File Imports\rebar_export.json"
)

concept_file_path = os.path.join(user_directory, "Revit_Rebar_Import.cpt")


# --------------------------------------------------
# DEFAULTS
# --------------------------------------------------

DEFAULT_SPACING_FT = 0.25  # 3 inches
DEFAULT_SPACING_IN = 3.0
FT_TO_IN = 12.0

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def parse_rebar_quantity(value):
    try:
        return int(value)
    except:
        return 1


def parse_spacing_to_in(spacing_text):
    """
    Converts spacing from JSON to inches.

    3"      -> 3.0 in
    3 in    -> 3.0 in
    0.25 ft -> 3.0 in

    If no unit is provided, assume inches.
    """

    if spacing_text is None:
        return DEFAULT_SPACING_IN

    text = str(spacing_text).lower().strip()

    try:
        if '"' in text or "in" in text:
            text = text.replace('"', '').replace("in", "").strip()
            return float(text)

        if "ft" in text:
            text = text.replace("ft", "").strip()
            return float(text) * FT_TO_IN

        # If no unit is provided, assume inches
        return float(text)

    except:
        return DEFAULT_SPACING_IN


def get_ram_rebar_type(model, rebar_size):
    rebars = model.rebars

    raw_name = str(rebar_size).strip()
    name_without_hash = raw_name.replace("#", "").strip()

    possible_names = [
        raw_name,                  # "#6"
        name_without_hash,         # "6"
        "# " + name_without_hash,  # "# 6"
    ]

    for name in possible_names:
        bar_type = rebars.rebar(name)

        if bar_type is not None:
            return bar_type

    print("\nAvailable rebar types:")
    for rebar in rebars.rebars:
        print(repr(rebar.name))

    raise Exception(
        "Could not find RAM Concept rebar type for '{}'. Tried: {}".format(
            raw_name,
            possible_names
        )
    )


def get_bar_end(has_hook):
    return BarEnd.HOOK_90 if has_hook else BarEnd.STRAIGHT


def get_point_from_json(point_data):
    """
    Revit exported coordinates are in feet.
    RAM Concept API appears to be using inches here,
    so multiply by 12.
    """

    return Point2D(
        point_data["x_ft"] * FT_TO_IN,
        point_data["y_ft"] * FT_TO_IN
    )


def get_line_angle_degrees(start_point, end_point):
    dx = end_point.x - start_point.x
    dy = end_point.y - start_point.y

    return math.degrees(math.atan2(dy, dx))


def make_rebar_polygon(start_point, end_point, spacing_ft, bar_quantity):
    """
    Creates a Polygon2D zone around the start/end line.

    Offset distance = spacing * quantity / 2

    Points:
    1. start + perpendicular offset
    2. start - perpendicular offset
    3. end   - perpendicular offset
    4. end   + perpendicular offset
    """

    dx = end_point.x - start_point.x
    dy = end_point.y - start_point.y

    length = math.sqrt(dx * dx + dy * dy)

    if length == 0:
        raise Exception("Rebar line has zero length.")

    perp_x = -dy / length
    perp_y = dx / length

    offset = spacing_ft * bar_quantity / 2.0

    p1 = Point2D(
        start_point.x + perp_x * offset,
        start_point.y + perp_y * offset
    )

    p2 = Point2D(
        start_point.x - perp_x * offset,
        start_point.y - perp_y * offset
    )

    p3 = Point2D(
        end_point.x - perp_x * offset,
        end_point.y - perp_y * offset
    )

    p4 = Point2D(
        end_point.x + perp_x * offset,
        end_point.y + perp_y * offset
    )

    return Polygon2D([p1, p2, p3, p4])


# --------------------------------------------------
# ADD REBAR FROM JSON
# --------------------------------------------------

def add_rebar_from_json(model, json_path):
    cad_manager = model.cad_manager
    rebar_layer = cad_manager.rebar_layer

    with open(json_path, "r") as f:
        rebar_entries = json.load(f)

    default_distributed_rebar = cad_manager.default_distributed_rebar

    created_count = 0

    for entry in rebar_entries:
        start_point = get_point_from_json(entry["start_point"])
        end_point = get_point_from_json(entry["end_point"])

        rebar_size = entry.get("rebar_size", "#6")
        rebar_quantity = parse_rebar_quantity(entry.get("rebar_quantity", 1))
        rebar_spacing_in = parse_spacing_to_in(entry.get("rebar_spacing", '3"'))

        bar_position = entry.get("bar_position", "Bottom")

        hooks = entry.get("hooks", {})
        left_hook = hooks.get("left_hook", False)
        right_hook = hooks.get("right_hook", False)

        bar_type = get_ram_rebar_type(model, rebar_size)

        rebar_polygon = make_rebar_polygon(
            start_point,
            end_point,
            rebar_spacing_in,
            rebar_quantity
        )

        default_distributed_rebar.bar_type = bar_type
        default_distributed_rebar.span_set = SpanSet.LATITUDE
        default_distributed_rebar.spacing = rebar_spacing_in
        default_distributed_rebar.slab_face = SlabFace.BY_ELEVATION_REFERENCE

        if bar_position == "Top":
            default_distributed_rebar.elevation_reference = ElevationReference.TOP_COVER
        else:
            default_distributed_rebar.elevation_reference = ElevationReference.BOTTOM_COVER

        default_distributed_rebar.ending_anchorage_1 = get_bar_end(left_hook)
        default_distributed_rebar.ending_anchorage_2 = get_bar_end(right_hook)

        distributed_rebar = rebar_layer.add_distributed_rebar(rebar_polygon)

        distributed_rebar.span_set = SpanSet.LATITUDE
        distributed_rebar.orientation = get_line_angle_degrees(start_point, end_point)

        created_count += 1

    print("Created {} distributed rebar regions.".format(created_count))


# --------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------

concept = Concept.start_concept(headless=True)

model = concept.new_model()
model.setup_new_model(DesignCode.ACI318_320_25US, StructureType.ELEVATED)

# Set/save units
units = model.units
units.set_US_user_units()
saved_units = units.get_units()
units.set_US_API_units()

# Set/save signs
signs = model.signs
signs.set_standard_signs()
saved_signs = signs.get_signs()
signs.set_positive_signs()

# Add rebar from exported Revit JSON
add_rebar_from_json(model, json_file_path)

# Restore units and signs
units.set_units(saved_units)
signs.set_signs(saved_signs)

# Save file
model.save_file(concept_file_path)

# Shut down RAM Concept
concept.shut_down()

print("Saved RAM Concept file to:")
print(concept_file_path)