import time
import math
import requests
import os
import json
from typing import Dict, Tuple, List

import matplotlib.pyplot as plt

from ram_concept.concept import Concept
from ram_concept.loading_layer import LoadingCause
from ram_concept.result_layers import ReactionContext
from ram_concept.point_2D import Point2D


# ✅ Only extract these layer results (case-insensitive match)
ALLOWED_LAYER_NAMES = [
    "Other Dead Loading",
    "Live (Reducible) Loading",
    "Live (Unreducible) Loading",
    "Wind X",
    "Wind Y",
    "Snow Loading",
    "Live (Roof) Loading",
    "Cladding",
    "Self-Dead Loading",
]

Key = Tuple[float, float, float]          # (x, y, elev)
Vec = List[float]                         # [Fx, Fy, Fz]
LoadsByLayer = Dict[str, Dict[Key, Vec]]  # loads[layer][(x,y,z)] = [Fx,Fy,Fz]

DL_LL_LAYERS = [
    "Self-Dead Loading",
    "Other Dead Loading",
    "Live (Reducible) Loading",
    "Cladding",
]

# --- Self-dead special handling ---
SELF_DEAD_SRC_NAME = "Self-Dead Loading"
# More consistent naming (same pattern as other layers, but clearly API-created)
SELF_DEAD_TARGET_NAME = "API - Transfer Self-Dead Loading"


def enable_persistent_http_session_like_yours():
    """Match your known-good session patch as closely as possible."""
    try:
        _session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=3)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)

        import ram_concept.concept as _concept_mod
        _concept_mod.requests.post = _session.post
        return True
    except Exception as e:
        print("⚠️ Warning: could not enable persistent HTTP session:", e)
        return False


def with_retries(fn, *, tries=3, sleep=0.5, label="op"):
    last = None
    for k in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            msg = str(e)

            # Blank string parse coming back from API
            if "could not convert string to float" in msg:
                print(f"⚠️ {label} returned blank/invalid result; skipping this item. ({e})")
                return None

            print(f"⚠️ {label} failed (attempt {k+1}/{tries}): {e}")
            time.sleep(sleep)

    print(f"⚠️ {label} failed after {tries} attempts; skipping. Last error: {last}")
    return None


def iter_layers_like_docs(cad_manager, allowed_names):
    """
    Match API docs:
      - start from force_loading_layers
      - remove hyperstatic
      - (combos optional; omitted per your earlier request)
    Then filter by allowed_names.
    """
    allowed = {n.strip().lower() for n in allowed_names}

    loadings = list(cad_manager.force_loading_layers)
    loadings = [L for L in loadings if L.loading_type.cause != LoadingCause.HYPERSTATIC]

    loadings_and_combos = loadings  # combos intentionally ignored

    filtered = [L for L in loadings_and_combos if (L.name or "").strip().lower() in allowed]

    found = {(L.name or "").strip().lower() for L in filtered}
    missing = [n for n in allowed_names if n.strip().lower() not in found]
    if missing:
        print("⚠️ These requested layers were not found in the model (name mismatch?):")
        for m in missing:
            print("   -", m)

    return filtered


def add_point_load(layer, x, y, fx, fy, fz, *, elevation=0.0):
    p = Point2D(x, y)
    pl = layer.add_point_load(p)
    pl.elevation = elevation
    pl.zero_load_values()
    pl.Fx = fx
    pl.Fy = fy
    pl.Fz = fz
    return pl


def wall_fr_fs_to_global_xy(fr, fs, angle_degrees):
    """
    Convert wall local reactions (Fr, Fs) into global (Fx, Fy) using reaction_angle.

    Requirements:
      - angle=0°  -> Fr is X, Fs is Y
      - angle=90° -> Fr is Y, Fs is X
      - otherwise use trig

    Mapping:
      Fx = Fr*cosθ + Fs*sinθ
      Fy = Fr*sinθ + Fs*cosθ
    """
    theta = math.radians(angle_degrees)
    c = math.cos(theta)
    s = math.sin(theta)
    fx = fr * c + fs * s
    fy = fr * s + fs * c
    return fx, fy


def extract_below_reactions(
    source_path,
    *,
    allowed_layer_names,
    reaction_context=ReactionContext.STANDARD,
    units_in_kips=False,
    combine_tol=0.01,
    pause_every=50,
    pause_secs=0.05,
    debug_samples_per_layer=3,
    run_analysis=True,
):
    """
    Returns dict: loads[layer_name][(x_round,y_round,elev)] = [Fx,Fy,Fz]
    - Columns: uses reaction.x/y/z directly (no negation)
    - Walls: treats reaction.x/y as Fr/Fs and rotates into global Fx/Fy
    """
    concept = Concept.start_concept(headless=False)
    enable_persistent_http_session_like_yours()

    loads: LoadsByLayer = {}
    ops = 0

    def maybe_pause():
        nonlocal ops
        ops += 1
        if pause_every and ops % pause_every == 0:
            time.sleep(pause_secs)

    try:
        model = concept.open_file(source_path)

        if run_analysis:
            try:
                print("🧩 Generating mesh...")
                model.generate_mesh()
            except Exception as e:
                print(f"⚠️ generate_mesh() warning: {e}")

            try:
                print("🧮 Running calc_all() (this can take a bit)...")
                model.calc_all()
            except Exception as e:
                print(f"⚠️ calc_all() warning: {e}")

        cad = model.cad_manager
        element_layer = cad.element_layer

        cols_below = list(element_layer.column_elements_below)
        walls_below = list(element_layer.wall_element_groups_below)

        print(f"=== Below elements ===")
        print(f"Columns below: {len(cols_below)}")
        print(f"Wall groups below: {len(walls_below)}")
        print("======================\n")

        for loading_or_combo in iter_layers_like_docs(cad, allowed_layer_names):
            lname = loading_or_combo.name
            acc: Dict[Key, Vec] = {}

            def add_acc(x, y, elev, fx, fy, fz):
                kx = round(x / combine_tol) * combine_tol
                ky = round(y / combine_tol) * combine_tol
                key = (kx, ky, elev)
                if key not in acc:
                    acc[key] = [0.0, 0.0, 0.0]
                acc[key][0] += fx
                acc[key][1] += fy
                acc[key][2] += fz

            printed = 0

            # ---- Column reactions ----
            for col in cols_below:
                def _get():
                    return loading_or_combo.column_reaction(col, reaction_context)

                reaction = with_retries(_get, label=f"{lname}.column_reaction")
                maybe_pause()
                if reaction is None:
                    continue

                loc = col.location
                fx, fy, fz = reaction.x, reaction.y, reaction.z  # keep as-is

                if printed < debug_samples_per_layer:
                    print(f"[SAMPLE RAW] {lname} col @ ({loc.x:.3f},{loc.y:.3f}) -> Fx={fx}, Fy={fy}, Fz={fz}")
                    printed += 1

                if units_in_kips:
                    fx *= 1000.0
                    fy *= 1000.0
                    fz *= 1000.0

                if abs(fx) < 1e-12 and abs(fy) < 1e-12 and abs(fz) < 1e-12:
                    continue

                add_acc(loc.x, loc.y, 0.0, fx, fy, fz)

            # ---- Wall group reactions ----
            for wg in walls_below:
                def _get():
                    return loading_or_combo.wall_group_reaction(wg, reaction_context)

                reaction = with_retries(_get, label=f"{lname}.wall_group_reaction")
                maybe_pause()
                if reaction is None:
                    continue

                centroid = wg.centroid
                angle = wg.reaction_angle

                fr, fs, fz = reaction.x, reaction.y, reaction.z
                fx, fy = wall_fr_fs_to_global_xy(fr, fs, angle)

                if printed < debug_samples_per_layer:
                    zc = getattr(centroid, "z", 0.0)
                    print(
                        f"[SAMPLE RAW] {lname} wall @ ({centroid.x:.3f},{centroid.y:.3f},{zc:.3f}) "
                        f"angle={angle:.3f}° -> Fr={fr}, Fs={fs}, Fz={fz} => Fx={fx}, Fy={fy}"
                    )
                    printed += 1

                if units_in_kips:
                    fx *= 1000.0
                    fy *= 1000.0
                    fz *= 1000.0

                if abs(fx) < 1e-12 and abs(fy) < 1e-12 and abs(fz) < 1e-12:
                    continue

                elev = getattr(centroid, "z", 0.0)
                add_acc(centroid.x, centroid.y, elev, fx, fy, fz)

            loads[lname] = acc
            print(f"✅ Extracted layer '{lname}': {len(acc)} combined points\n")

        return loads

    finally:
        try:
            concept.shut_down()
        except Exception as e:
            print("⚠️ concept.shut_down() warning:", e)


def _key_to_str(k: Key) -> str:
    return f"{k[0]},{k[1]},{k[2]}"


def _str_to_key(s: str) -> Key:
    a, b, c = s.split(",")
    return (float(a), float(b), float(c))


def save_loads_to_json(loads: LoadsByLayer, path: str) -> None:
    out: Dict[str, Dict[str, Vec]] = {}
    for lname, pts in loads.items():
        out[lname] = {_key_to_str(k): v for k, v in pts.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


def load_loads_from_json(path: str) -> LoadsByLayer:
    data = json.load(open(path, "r", encoding="utf-8"))
    loads: LoadsByLayer = {}
    for lname, pts in data.items():
        loads[lname] = {_str_to_key(k): v for k, v in pts.items()}
    return loads


def combine_vertical_reactions(loads: LoadsByLayer, layer_names: List[str]) -> Dict[Key, float]:
    combined: Dict[Key, float] = {}

    missing = [n for n in layer_names if n not in loads]
    if missing:
        print("⚠️ Missing layers in loads dict:")
        for m in missing:
            print("   -", m)

    for lname in layer_names:
        pts = loads.get(lname, {})
        for k, vec in pts.items():
            fz = float(vec[2])
            combined[k] = combined.get(k, 0.0) + fz

    return combined


def open_writable_model(concept: Concept, target_path: str):
    """
    Open a model in a way that avoids read-only locks.
    Strategy:
      1) Open the file
      2) Immediately Save As to a new path (timestamped) and re-open that path
    """
    model = concept.open_file(target_path)

    base, ext = os.path.splitext(target_path)
    writable_path = f"{base}__writable_{int(time.time())}{ext}"

    model.save_file(writable_path)
    model.close_model()

    model2 = concept.open_file(writable_path)
    return model2, writable_path


def get_or_create_force_layer(cad_manager, layer_name: str):
    """
    Returns a ForceLoadingLayer. Creates it if missing.

    IMPORTANT:
      Your ram_concept build shows CadManager.add_force_loading_layer()
      takes only (layer_name). Do NOT pass LoadingType.
    """
    layer = cad_manager.force_loading_layer(layer_name)
    if layer is not None:
        return layer

    print(f"➕ Creating force loading layer: '{layer_name}'")
    created = cad_manager.add_force_loading_layer(layer_name)
    return created


def get_target_layer_for_write(cad_manager, src_layer_name: str):
    """
    Self-Dead is read-only in many models. Redirect writes into a new API-created layer.
    """
    if (src_layer_name or "").strip().lower() == SELF_DEAD_SRC_NAME.lower():
        layer = get_or_create_force_layer(cad_manager, SELF_DEAD_TARGET_NAME)
        return layer, SELF_DEAD_TARGET_NAME

    layer = cad_manager.force_loading_layer(src_layer_name)
    return layer, src_layer_name


def write_point_loads(target_path, loads_by_layer, *, pause_every=200, pause_secs=0.05):
    concept = Concept.start_concept(headless=False)
    enable_persistent_http_session_like_yours()

    ops = 0

    def maybe_pause():
        nonlocal ops
        ops += 1
        if pause_every and ops % pause_every == 0:
            time.sleep(pause_secs)

    try:
        # ✅ open writable copy
        model, used_path = open_writable_model(concept, target_path)
        cad = model.cad_manager

        print(f"✍️ Writing into writable copy:\n   {used_path}\n")

        total = 0
        for src_lname, pts in loads_by_layer.items():
            layer, used_name = get_target_layer_for_write(cad, src_lname)

            # If the layer doesn't exist (non-self-dead), create it
            if layer is None:
                layer = get_or_create_force_layer(cad, used_name)

            if used_name != src_lname:
                print(f"↪ Redirecting '{src_lname}' -> '{used_name}' (Self-Dead is read-only)")

            created = 0
            for (x, y, elev), (fx, fy, fz) in pts.items():
                try:
                    add_point_load(layer, x, y, fx, fy, fz, elevation=elev)
                    created += 1
                    total += 1
                except Exception as e:
                    print(f"⚠️ Could not write to '{used_name}' at ({x:.2f},{y:.2f},{elev:.2f}): {e}")

                maybe_pause()

            print(f"✅ Wrote '{used_name}': {created} point loads")

        model.save_file(used_path)
        print(f"✅ Saved target: {used_path}")
        return total, used_path

    finally:
        try:
            concept.shut_down()
        except Exception as e:
            print("⚠️ concept.shut_down() warning:", e)


def plot_reaction_heatmap_with_piles(
    combined_fz: Dict[Key, float],
    *,
    pile_capacity_kips: float = 60.0,
    annotate: bool = True,
    max_labels: int | None = None,
    label_offset: Tuple[float, float] = (1.5, 1.5),
    use_abs_for_piles: bool = True,
    title: str = "1.0DL + 1.0LL (Fz) Reaction Heat Map",
) -> None:
    if not combined_fz:
        print("⚠️ No combined reactions to plot.")
        return

    xs, ys, vals = [], [], []
    for (x, y, _z), fz in combined_fz.items():
        xs.append(x)
        ys.append(y)
        vals.append(fz)

    abs_vals = [abs(v) for v in vals]

    min_s = 20.0
    max_s = 400.0
    max_abs = max(abs_vals) if max(abs_vals) > 0 else 1.0
    sizes = [min_s + (max_s - min_s) * (a / max_abs) for a in abs_vals]

    fig, ax = plt.subplots()
    sc = ax.scatter(xs, ys, c=vals, s=sizes)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("Fz (kips)")

    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect("equal", adjustable="box")

    if annotate:
        items = list(combined_fz.items())
        if max_labels is not None and len(items) > max_labels:
            items = sorted(items, key=lambda kv: abs(kv[1]), reverse=True)[:max_labels]

        dx, dy = label_offset
        for (x, y, _z), fz in items:
            demand = abs(fz) if use_abs_for_piles else fz
            piles = int(math.ceil(demand / pile_capacity_kips)) if pile_capacity_kips > 0 else 0
            ax.text(x + dx, y + dy, f"{piles} piles required", fontsize=8)

    plt.show()


if __name__ == "__main__":
    source_path = r"C:\Users\aguter\OneDrive - QUINLIVAN PIERIK & KRAUSE - ARCHITECTS ENGINEERS\Desktop\RAM Concept Models\Sample Export Reactions and Read Reactions\Base Model\sample reactions read and write.cpt"
    target_path = r"C:\Users\aguter\OneDrive - QUINLIVAN PIERIK & KRAUSE - ARCHITECTS ENGINEERS\Desktop\RAM Concept Models\Sample Export Reactions and Read Reactions\Base Model\sampleWriteModel.cpt"

    loads = extract_below_reactions(
        source_path,
        allowed_layer_names=ALLOWED_LAYER_NAMES,
        reaction_context=ReactionContext.STANDARD,
        units_in_kips=False,
        combine_tol=0.01,
        pause_every=50,
        pause_secs=0.05,
        debug_samples_per_layer=3,
        run_analysis=True,
    )

    # If you want the plot, uncomment:
    # combined = combine_vertical_reactions(loads, DL_LL_LAYERS)
    # plot_reaction_heatmap_with_piles(
    #     combined,
    #     pile_capacity_kips=60.0,
    #     annotate=True,
    #     max_labels=80,
    #     label_offset=(2.0, 2.0),
    # )

    total = write_point_loads(
        target_path,
        loads,
        pause_every=200,
        pause_secs=0.05,
    )

    print(f"✅ Done. Total point loads created: {total}")
