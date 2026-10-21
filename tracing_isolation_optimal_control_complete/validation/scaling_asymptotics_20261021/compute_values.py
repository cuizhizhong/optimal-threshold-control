"""把本批解析 JSON 的少量量级结果写成正文宏，保留旧数值块。"""
from decimal import Decimal
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "analytic_results.json").read_text(encoding="utf-8"))
values = {}
for suffix, key in (("E", "E2"), ("Z", "Zhou_constructed_no_return")):
    for macro, field in (("fill", "J_fill"), ("opt", "J_star"), ("delta", "Delta_J"),
                         ("timeFill", "T_fill"), ("timeOpt", "T_star"),
                         ("sb", "s_B"), ("release", "s_bar")):
        values[macro + suffix] = Decimal(data[key][field]).quantize(Decimal("0.000001"))
    values["saving" + suffix] = (100 * Decimal(data[key]["relative_saving"])).quantize(Decimal("0.000001"))
historical = next(row for row in data["historical_check"]["cases"] if Decimal(row["K"]) == Decimal("0.0001"))
values["smallBetaError"] = Decimal(historical["asymptotics"]["Delta_J_error_pct"]).quantize(Decimal("0.01"))
text = "% D 批80位解析求值的展示舍入；不是新增优化结果。\n"
text += "".join("\\newcommand{\\D" + name + "}{" + str(value) + "}\n" for name, value in values.items())
(HERE / "computed_values.tex").write_text(text, encoding="utf-8", newline="\n")
print(f"D computed values: {len(values)} macros")
