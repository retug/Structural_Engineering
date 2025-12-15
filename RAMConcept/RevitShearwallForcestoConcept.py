# READ 4 CSVs (Wind X/Y line loads + point loads) AND CREATE THEM IN RAM CONCEPT
import os, csv, time
from pathlib import Path

# --- Dev API bootstrap (unchanged) ---
if os.environ.get("RAM_CONCEPT_DEVELOPER") is not None:
    import sys
    dev_api_directory = os.path.dirname(os.path.realpath(__file__)) + '\\..\\..'
    sys.path.insert(1, dev_api_directory)

# RAM Concept API
from ram_concept.concept import Concept
from ram_concept.point_2D import Point2D
from ram_concept.line_segment_2D import LineSegment2D

# ====== USER INPUTS ======
csv_dir   = r"C:\Users\aguter\Desktop"
file_path = r"D:\aguter\BUILDING B AND C PODIUM with Lateral Loads.cpt"  # <-- CHANGE THIS to your CPT path

csv_wind_x_lines  = os.path.join(csv_dir, "Wind X.csv")
csv_wind_y_lines  = os.path.join(csv_dir, "Wind Y.csv")
csv_wind_x_points = os.path.join(csv_dir, "Wind X - PointLoads.csv")
csv_wind_y_points = os.path.join(csv_dir, "Wind Y - PointLoads.csv")

# ====== HELPERS ======
def f(x):
    """Convert value to float or return None."""
    try:
        if x is None: return None
        s = str(x).strip()
        if not s or s.lower() == "none":
            return None
        return float(s)
    except:
        return None

def ensure_exists(p):
    if not os.path.exists(p):
        raise Exception("File not found: {}".format(p))



def add_line_load_vec(layer, cad_manager, p0, p1, fx_kipft, fy_kipft, fz_kipft):
    """
    Creates a line load on 'layer' using cad_manager.default_line_load.
    CSV values are kip/ft; RAM API expects lb/ft (based on typical usage / your examples).
    """
    if layer is None:
        return False

    fx = fx_kipft
    fy = fy_kipft
    fz = fz_kipft

    # Skip near-zero loads
    if (fx is None or abs(fx) < 1e-12) and (fy is None or abs(fy) < 1e-12) and (fz is None or abs(fz) < 1e-12):
        return False

    default_load = cad_manager.default_line_load
    default_load.elevation = 0

    # set_load_values(Fx, Fy, Fz, Mx, My)
    # (moments set to 0)
    default_load.set_load_values(
        0.0 if fx is None else fx,
        0.0 if fy is None else fy,
        0.0 if fz is None else fz,
        0.0, 0.0
    )

    seg = LineSegment2D(p0, p1)
    layer.add_line_load(seg)
    return True

def add_point_load_vec(layer, p, fx_kip, fy_kip, fz_kip):
    """
    Creates a point load on 'layer'.
    CSV values are kip; RAM API expects lb (based on typical usage / your example).
    """
    if layer is None:
        return False

    fx = fx_kip
    fy = fy_kip
    fz = fz_kip

    if (fx is None or abs(fx) < 1e-12) and (fy is None or abs(fy) < 1e-12) and (fz is None or abs(fz) < 1e-12):
        return False

    pl = layer.add_point_load(p)
    pl.elevation = 0
    pl.zero_load_values()

    # Set components (lb)
    pl.Fx = 0.0 if fx is None else fx
    pl.Fy = 0.0 if fy is None else fy
    pl.Fz = 0.0 if fz is None else fz
    return True

def import_line_csv(csv_path, layer, cad_manager, pause_every=500, pause_secs=0.05):
    """
    Reads line-load CSV with columns:
    StartX, StartY, StartZ, EndX, EndY, EndZ, Fx(kip/ft), Fy(kip/ft), Fz(kip/ft), VIEW_NAME
    Creates line loads on given layer.
    """
    ensure_exists(csv_path)

    created = 0
    skipped = 0
    ops_since_pause = 0

    with open(csv_path, "r", newline="") as fcsv:
        reader = csv.reader(fcsv)
        header = next(reader, None)  # skip header

        for idx, row in enumerate(reader, start=2):
            if not row or len(row) < 10:
                skipped += 1
                continue

            sx, sy, sz, ex, ey, ez, fx, fy, fz = row[:9]

            sx, sy, ex, ey = f(sx), f(sy), f(ex), f(ey)
            fx, fy, fz     = f(fx), f(fy), f(fz)

            if None in (sx, sy, ex, ey):
                skipped += 1
                continue

            p0, p1 = Point2D(sx, sy), Point2D(ex, ey)

            if add_line_load_vec(layer, cad_manager, p0, p1, fx, fy, fz):
                created += 1
                ops_since_pause += 1

            if ops_since_pause >= pause_every:
                time.sleep(pause_secs)
                ops_since_pause = 0

    return created, skipped

def import_point_csv(csv_path, layer, pause_every=500, pause_secs=0.05):
    """
    Reads point-load CSV with columns:
    X, Y, Z, FX(kip), FY(kip), FZ(kip), VIEW_NAME
    Creates point loads on given layer.
    """
    ensure_exists(csv_path)

    created = 0
    skipped = 0
    ops_since_pause = 0

    with open(csv_path, "r", newline="") as fcsv:
        reader = csv.reader(fcsv)
        header = next(reader, None)  # skip header

        for idx, row in enumerate(reader, start=2):
            if not row or len(row) < 7:
                skipped += 1
                continue

            x, y, z, fx, fy, fz = row[:6]
            x, y = f(x), f(y)
            fx, fy, fz = f(fx), f(fy), f(fz)

            if None in (x, y):
                skipped += 1
                continue

            p = Point2D(x, y)

            if add_point_load_vec(layer, p, fx, fy, fz):
                created += 1
                ops_since_pause += 1

            if ops_since_pause >= pause_every:
                time.sleep(pause_secs)
                ops_since_pause = 0

    return created, skipped

# ====== START CONCEPT ======
print("Opening:", file_path)
concept = Concept.start_concept(headless=True)

# ---- Persistent Session (prevents WinError 10048) ----
try:
    import requests as _requests
    _session = _requests.Session()
    adapter = _requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=3)
    _session.mount("http://", adapter)
    _session.mount("https://", adapter)

    import ram_concept.concept as _concept_mod
    _concept_mod.requests.post = _session.post
except Exception as e:
    print("⚠️ Warning: could not enable persistent HTTP session:", e)

try:
    model = concept.open_file(file_path)
    cad_manager = model.cad_manager

    # Ensure layers exist in the model
    wind_x_layer = cad_manager.force_loading_layer("Wind X")
    wind_y_layer = cad_manager.force_loading_layer("Wind Y")

    # ---- IMPORT LINE LOADS ----
    x_line_created, x_line_skipped = import_line_csv(csv_wind_x_lines, wind_x_layer, cad_manager)
    y_line_created, y_line_skipped = import_line_csv(csv_wind_y_lines, wind_y_layer, cad_manager)

    # ---- IMPORT POINT LOADS ----
    x_pt_created, x_pt_skipped = import_point_csv(csv_wind_x_points, wind_x_layer)
    y_pt_created, y_pt_skipped = import_point_csv(csv_wind_y_points, wind_y_layer)

    print("Line Loads:")
    print("  Wind X -> created:", x_line_created, "skipped:", x_line_skipped)
    print("  Wind Y -> created:", y_line_created, "skipped:", y_line_skipped)

    print("Point Loads:")
    print("  Wind X -> created:", x_pt_created, "skipped:", x_pt_skipped)
    print("  Wind Y -> created:", y_pt_created, "skipped:", y_pt_skipped)

    model.save_file(file_path)

finally:
    try:
        concept.shut_down()
    except Exception as e:
        print("⚠️ concept.shut_down() warning:", e)
    print("✅ Done.")
