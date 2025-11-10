# READ CSV OF LINE LOADS AND CREATE THEM IN RAM CONCEPT
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
user_directory = r"D:\aguter"
file_path = os.path.join(user_directory, "MyCustomLoading.cpt")
csv_path  = os.path.join(user_directory, "SpanLines.csv")  # path to your CSV export

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

def add_line_load(layer, cad_manager, p0, p1, plf):
    """
    Creates a line load using cad_manager.default_line_load on the specified layer.
    plf is pounds per foot (positive down). Always sets values for each call.
    """
    if layer is None or plf is None or abs(plf) < 1e-9:
        return False

    default_load = cad_manager.default_line_load
    default_load.elevation = 0
    # Keep original behavior: put plf/1000.0 into Fy (no sign flip).
    # If your convention needs up-positive, flip sign here.
    default_load.set_load_values(0, 0, float(plf)/1000.0, 0, 0)

    seg = LineSegment2D(p0, p1)
    layer.add_line_load(seg)
    return True

# ====== START CONCEPT ======
print(f"Opening: {file_path}")
concept = Concept.start_concept(headless=True)

# ---- Use a persistent Session to avoid socket exhaustion (WinError 10048) ----
try:
    import requests as _requests
    _session = _requests.Session()
    adapter = _requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=3)
    _session.mount("http://", adapter)
    _session.mount("https://", adapter)

    import ram_concept.concept as _concept_mod
    _concept_mod.requests.post = _session.post
except Exception as e:
    print(f"⚠️ Warning: could not enable persistent HTTP session: {e}")

try:
    model = concept.open_file(file_path)
    cad_manager = model.cad_manager

    # loading layers
    dead_ldg = cad_manager.force_loading_layer("Other Dead Loading")
    live_ldg = cad_manager.force_loading_layer("Live (Reducible) Loading")
    snow_ldg = cad_manager.force_loading_layer("Snow Loading")

    count_dead = count_live = count_snow = skipped = 0

    # ====== READ CSV AND CREATE LOADS ======
    with open(csv_path, "r", newline="") as fcsv:
        reader = csv.reader(fcsv)
        header = next(reader, None)  # skip header

        ops_since_pause = 0
        PAUSE_EVERY = 500  # adjust if needed
        PAUSE_SECS  = 0.05

        for idx, row in enumerate(reader, start=2):
            # expecting 10 columns: Start X..Z, End X..Z, DEAD, LIVE, SNOW, VIEW_NAME
            if not row or len(row) < 10:
                skipped += 1
                continue

            sx, sy, sz, ex, ey, ez, d_plf, l_plf, s_plf = row[:9]
            sx, sy, ex, ey = f(sx), f(sy), f(ex), f(ey)
            d_plf, l_plf, s_plf = f(d_plf), f(l_plf), f(s_plf)

            if None in (sx, sy, ex, ey):
                skipped += 1
                continue

            p0, p1 = Point2D(sx, sy), Point2D(ex, ey)

            # DEAD
            if add_line_load(dead_ldg, cad_manager, p0, p1, d_plf):
                count_dead += 1
                ops_since_pause += 1

            # LIVE
            if add_line_load(live_ldg, cad_manager, p0, p1, l_plf):
                count_live += 1
                ops_since_pause += 1

            # SNOW
            if add_line_load(snow_ldg, cad_manager, p0, p1, s_plf):
                count_snow += 1
                ops_since_pause += 1

            # Gentle throttle to help Windows recycle ephemeral ports
            if ops_since_pause >= PAUSE_EVERY:
                time.sleep(PAUSE_SECS)
                ops_since_pause = 0

    print(f"Created line loads → Dead: {count_dead}, Live: {count_live}, Snow: {count_snow}, Skipped: {skipped}")
    model.save_file(file_path)

finally:
    try:
        concept.shut_down()
    except Exception as e:
        print(f"⚠️ concept.shut_down() warning: {e}")
    print("✅ Done.")
