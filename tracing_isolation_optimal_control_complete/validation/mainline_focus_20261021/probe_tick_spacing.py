"""只重建同尺寸坐标轴，检查主轴与插图刻度框；不生成或改写生产图。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
    "mathtext.fontset": "stix", "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": .6})


def probe(right):
    fig = plt.figure(figsize=(469.47049 / 72.27, 8 / 2.54), dpi=150)
    main = fig.add_axes([.075, .145, .905, .80])
    inset = fig.add_axes([.107, .205, .300, .337])
    main.set_xlim(.15, 1.01)
    main.set_ylim(0, .17)
    main.set_xticks([.2, .4, .6, .8, 1.])
    main.set_yticks([0, .05, .10, .15])
    inset.set_xlim(.42, .60)
    inset.set_ylim(.10, .155)
    inset.set_xticks([.42, .50, .60])
    inset.set_yticks([.10, .125, .15])
    for ax in (main, inset):
        ax.tick_params(direction="out", length=2.5, width=.6, pad=2)
    if right:
        inset.yaxis.tick_right()
        inset.tick_params(axis="y", labelleft=False, labelright=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    records = []
    for name, ax in (("main", main), ("inset", inset)):
        for tick in ax.get_yticklabels():
            box = tick.get_window_extent(renderer)
            records.append({"axis": name, "text": tick.get_text(), "bbox_150dpi_px": [box.x0, box.y0, box.x1, box.y1]})
    pairs = []
    for a in [r for r in records if r["axis"] == "main"]:
        for b in [r for r in records if r["axis"] == "inset"]:
            x0, y0, x1, y1 = a["bbox_150dpi_px"]
            u0, v0, u1, v1 = b["bbox_150dpi_px"]
            overlap_x = min(x1, u1) - max(x0, u0)
            overlap_y = min(y1, v1) - max(y0, v0)
            if overlap_x > 0 and overlap_y > 0:
                pairs.append({"main": a["text"], "inset": b["text"], "overlap_width_px": overlap_x,
                              "overlap_height_px": overlap_y, "overlap_area_px2": overlap_x * overlap_y})
    target_a = next(r for r in records if r["axis"] == "main" and r["text"] == "0.05")
    target_b = next(r for r in records if r["axis"] == "inset" and r["text"] == "0.125")
    plt.close(fig)
    return {"inset_y_tick_side": "right" if right else "left", "ticks": records,
            "overlapping_cross_axes_tick_pairs": pairs, "requested_pair": {"main": target_a, "inset": target_b}}


evidence = {"status": "read_only_layout_probe", "production_figure_modified": False,
            "dpi": 150, "size_cm": [469.47049 / 72.27 * 2.54, 8],
            "current_left_ticks": probe(False), "proposed_right_ticks": probe(True)}
(HERE / "tick_spacing_probe.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value["overlapping_cross_axes_tick_pairs"] for key, value in evidence.items() if isinstance(value, dict)}, ensure_ascii=False))
