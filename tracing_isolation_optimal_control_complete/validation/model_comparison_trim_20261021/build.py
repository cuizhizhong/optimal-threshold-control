"""复用既有双版本构建器，将本次日志保存在独立目录。"""

from pathlib import Path

here = Path(__file__).resolve().parent
project = here.parents[1]
source = project / "validation/model_no_return_revision_20261020/build_revision.py"
code = source.read_text(encoding="utf-8").replace(
    "tmp/model_no_return_revision_20261020", "tmp/model_comparison_trim_20261021")
code = code.replace('"A1_no_return_revision"', '"A1_comparison_trim"')
namespace = {"__name__": "reused_build", "__file__": str(source)}
exec(compile(code, str(source), "exec"), namespace)
namespace.update(HERE=here, PROJECT=project, LATEX=project / "latex")
namespace["main"]()
