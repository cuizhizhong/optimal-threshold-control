"""仅依据已经存在并通过核对的报告登记第 10--11 步交付。"""
from pathlib import Path
import hashlib
import json
import subprocess

P = Path(__file__).resolve().parents[2]
V = P / "validation/numerical_scenarios"


def read(name):
    return json.loads((V / name).read_text(encoding="utf-8"))


def main():
    result = read("step1011_validation_report.json")
    assert result["passed"]
    clean = result["clean_checkout"]
    qa = read("step1011_pdf_qa.json")
    assert not qa["visual_defects"]
    assert qa["main_pdf_sha256"] == hashlib.sha256((P / "latex/main.pdf").read_bytes()).hexdigest()
    final_export = read("step1011_final_export_report.json")
    assert final_export["idempotent"] and final_export["compiled_tex_unchanged"]
    assert final_export["optimizer_executions"] == 0 and final_export["first"]["verified"] and final_export["second"]["verified"]
    clean_build = read("step1011_clean_build_report.json")
    assert all(clean_build[k]["success"] and not clean_build[k]["final_log_issues"] for k in ("main", "theory_only"))
    clean_python = read("step1011_clean_python_report.json")
    assert clean_python["generator_check_passed"] and clean_python["python_tests_passed"] == 6 and clean_python["fixture_unchanged"]
    assert clean_python["generator_exit_code"] == 0 and clean_python["unittest_exit_code"] == 0
    candidate_match = read("step1011_candidate_source_match.json")
    assert candidate_match["main_tex_byte_identical"] and candidate_match["current_sources_match_candidate"]
    assert candidate_match["raw_solver_fixture_and_inputs_byte_unchanged"] and candidate_match["compatibility_scientific_content_identical"]
    assert candidate_match["protected_assessment_files_byte_unchanged"] == 35
    assert not candidate_match["candidate_figures_visual_review"]["defects"]
    anomalies = [
        {"kind": "read_only_navigation", "detail": "仓库根目录 CODEX_EXECUTION_PLAN.md 与 .gitignore 不存在；一次验证函数查找误用 validation 路径。已定位当前 ai/codex_revision_plan 及 matlab/numerical_scenarios 中的实际文件。", "scientific_optimizer_calls": 0},
        {"kind": "python_encoding", "original_error": "UnicodeDecodeError: 'gbk' codec can't decode byte 0x82", "detail": "JSON 读取改用 encoding='utf-8'；PDF 文本控制台输出改设 PYTHONIOENCODING=utf-8。渲染页面中文正常。", "resolved": True},
        {"kind": "subagent_matlab_startup", "original_error": "MATLAB::settings::prefdir::PrefdirNotWritable", "detail": "受限环境无法访问 C:/Users/cui/AppData/Roaming/MathWorks/MATLAB/R2025b，退出1；独立临时偏好目录的启动被根代理中断以避免并发，均未产生科学求解。随后根代理在本机环境运行成功。", "scientific_optimizer_calls": 0},
        {"kind": "matlab_entrypoint", "detail": "run() 临时改变 pwd，首次入口拼出错误目录并无法识别 numerical_cases_config；改用 mfilename('fullpath') 定位并重新运行成功。", "log": "step1011_postprocess_attempt1.log", "scientific_optimizer_calls": 0, "resolved": True},
        {"kind": "latex_overfull", "detail": "首次主文附录路径段落 Overfull hbox 11.08316pt；只调整换段后重编，最终主文与 TheoryOnly 日志零问题。", "log": "step1011_main_attempt1_final.log", "resolved": True},
        {"kind": "diagnostic_false_positives", "detail": "首次日志筛选把 infwarerr 包说明和 pdftexcmds Info 当作异常；现改为真正 Warning/Overfull/Underfull/缺字/错误模式。首次报告仍保留。", "report": "step1011_build_attempt1_report.json", "resolved": True},
        {"kind": "clean_archive_long_path", "original_error": "FileNotFoundError: [Errno 2] No such file or directory", "detail": "首次 tar 展开遇 Windows 长路径限制；改为长路径目标前缀并设置 Git core.longpaths；失败临时目录保留。", "scientific_optimizer_calls": 0, "resolved": True},
        {"kind": "clean_missing_assessment", "original_error": "No current saved assessment: run_4dfaa3539e6241ae8d3d7cd4028c667a.", "detail": "第一次 clean MATLAB 的12组 unit通过，但保存数据导出回归失败；源文件 is_file 枚举跳过35个长路径 assessment。原工作区数据完整；源枚举也采用长路径前缀，核对评估集合完整后重建并重跑。一次定位诊断的相对路径 stat 亦遇 WinError 3，已使用绝对长路径。", "log": "step1011_clean_attempt1.log", "scientific_optimizer_calls": 0, "resolved": True},
        {"kind": "vector_export_warning", "identifier": "MATLAB:print:ContentTypeImageSuggested", "detail": "原工作区及干净候选各有三次矢量导出耗时/文件大小提醒，未屏蔽警告；实际输出完成、来源哈希匹配并经视觉检查。", "log": "step1011_postprocess.log", "clean_log": "step1011_clean_execution.log", "scientific_result_failure": False},
        {"kind": "git_line_endings", "detail": "git diff --check 提示部分文本未来会由 LF 转 CRLF；没有据此改写求解或评估源码，受保护字节及源码指纹已核对。", "scientific_result_failure": False},
        {"kind": "export_source_snapshot_refresh", "detail": "后处理初次来源快照记录了最终 exporter 修改前的哈希；旧快照保留为 step1011_source_fingerprints_postprocess.json，当前快照仅以实际最终重复导出的来源报告刷新，并逐文件核对四类当前来源。未改写 solve 或 assessment 指纹。", "resolved": True, "scientific_optimizer_calls": 0},
        {"kind": "candidate_comparison_overstrict", "original_error": "AssertionError", "detail": "首次比较把 all,false 合法重新发布后的 selection_manifest 也要求字节不变，断言失败。实际仅 selected_utc、兼容文件中的同一时间戳和相应兼容哈希更新；五例全部其余字段/数组、35条原始求解和solver、35条assessment、输入和fixture不变。已逐字段核对并保留差异报告，没有把候选字节一致性误称为通过。", "log": "step1011_candidate_compare_attempt1.log", "resolved": True},
        {"kind": "candidate_png_differences", "detail": "三个PNG的Creation Time均变化；解码后FigN1有3/2171984像素不同、FigN2有1/2418948像素不同、FigN3像素全同。三张候选图经独立逐图视觉复核，未见曲线、阶梯、阴影、边界或布局的实际变化。图像不宣称字节相同；灰色辅助线穿透明图例背景的既有轻微现象两份均保留且可读。", "report": "step1011_candidate_source_match.json", "scientific_result_failure": False},
        {"kind": "patch_context_retry", "detail": "一次组合补丁因单/双引号上下文不匹配而被 apply_patch 拒绝；未改变科学文件，按实际文本修正后已成功应用。", "resolved": True, "scientific_optimizer_calls": 0},
        {"kind": "integrity_macro_parameter", "original_error": "AssertionError", "detail": "首次完整性检查把 NumTheoryRef 宏定义的 \\ref{#1} 参数误当成缺失正文标签；已只排除合法宏参数#[1-9]，实际正文引用和两份最终编译日志仍检查。未修改TeX源或科学数据。", "log": "step1011_integrity_attempt1.log", "resolved": True, "scientific_optimizer_calls": 0},
    ]
    (V / "step1011_operational_anomalies.json").write_text(json.dumps(anomalies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["operational_anomalies"] = anomalies
    result["pdf_visual_qa"] = qa
    result["final_export"] = final_export
    result["clean_build"] = clean_build
    result["clean_python"] = clean_python
    result["candidate_source_comparison"] = candidate_match
    result["candidate_snapshot"] = read("step1011_checkout_manifest.json")["snapshot_commit"]
    (V / "step1011_validation_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    origins = "\n".join(f"- `{g['solve_commit']}`：{g['records']} 条，`solve_dirty={g['solve_dirty']}`，求解源码哈希 `{g['solve_code_hash']}`。" for g in result["solve_provenance_groups"])
    failures = "\n".join(f"| {r['case_id']} | {r['N']} | {r['numeric_pass']} | {r['agreement_pass']} | {r['capacity_excess']:.12g} | `{r['observed_structure']}` |" for r in result["failed_diagnostic_records"])
    text = f"""# 第 10–11 步实际交付记录

第 10–11 步已完成实际导出、编译、页面检查与候选成果快照的干净检出复核。计划及预期值未作为结果；本批科学优化为 0 次。原始35条求解记录、五例主选择及完整求解/评估源码字节保持不变。

## 科学结果与范围

默认配置实际覆盖 35/35，求解成功35；numeric_pass=29/35，agreement_pass=29/35，双通过28/35。主五例均通过两类检查。原严格 grid 一致性仍为 false，正文明确 E2/E4 未通过该口径；第8–9步的建议最细级比较结果独立保留，没有用它改写原失败状态。初始化、固定步长时域与45个阈值识别组合均有真实记录。七条至少一类诊断失败如下；所有原始记录和事件仍可追溯。

| 例 | N | numeric | agreement | 容量超出 | 实际识别结构 |
|---|---:|---|---|---:|---|
{failures}

当前 E4 选中成本差 -3.68275844664e-6、重积分容量超出 7.70286958773e-7，由选中数据重新生成；未称为低于解析值的严格可行控制。无 unresolved_discrepancy 记录。N=16000、T=600及额外初猜未运行，没有新结果宏或数值被填入。

## 实际执行

原工作区：`revision_preflight`、12组无优化器单元测试、3项失败清空回归、8项保存数据回归、2项未运行/blocked回归；实际 `make_numerical_figures` 和重复 `export_numerical_latex`，重复正文导出相同且不修改生成块外正文。最终导出源码另实际重导出两次，编译文本保持相同。

候选快照：`run_revision_validation('unit',false)`、保存数据9项回归、`run_revision_validation('all',false)`，实际可信缓存 {clean['trusted_cache_hits']}，科学求解 {clean['scientific_optimizer_executions']}，缓存记录成功35、求解失败0；协议完成 true、一致性 false。另实际完成 T=1,N=4,d=2 的一个接口smoke，成功1、失败0，独立保存在smoke文件，排除于35条科学配置。Python fixture `--check` 和6项测试通过，fixture字节未变。精确命令见本目录 `step1011_commands.md`，每次执行日志与报告均保留。

干净检出是 Git HEAD加明确成果文件的候选快照 `{result['candidate_snapshot']}`，起始 Git status为空；复用显式 `OPENOCL_ROOT` 指向原仓库已跟踪、哈希匹配的 OpenOCL/CasADi依赖。它验证候选源和数据可检出及运行，不声称在另一台机器重新安装全部环境。

候选与原工作区主TeX字节相同；35条raw/solver、35条assessment、输入和fixture字节不变。五例兼容文件全部科学字段/数组相同，仅重新发布的选择时间戳及对应哈希更新。PNG含新的Creation Time，解码像素变化分别为3、1、0，独立逐图视觉复核未见曲线或布局差别；不宣称PNG字节一致。比较器首轮过严断言及其修正证据保留。

## 编译与图表

原工作区及候选检出均实际执行 XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，main 34页、TheoryOnly 26页，最终日志无未定义引用、重复标签、缺图、缺字、Overfull/Underfull。已人工检查主文第5、25–30、33页及三张PNG。保持三张主图、一个主表；每张图精确绑定case_id/run_id和PDF/PNG哈希，数值控制为阶梯，解析跳跃用重复事件时刻。

## 修改及来源

修改 main.tex 的数值方法、结果解释、复现附录和两个生成块；新增附加协议开关/摘要。未重做第5步主理论修改；abstract至数值章节前的正文保持规范化字节相同。修改 exporter、figure脚本与导出回归，更新四份README和MANIFEST；新增本批入口、构建和完整性脚本及实际报告。精确路径清单见 `CHANGED_FILES_STAGE1011.txt`。

原仓库 HEAD仍为 `{result['original_repository_head']}`；本次没有新增交付提交或push。科学记录真实来源如下，未用候选提交或导出提交替代：

{origins}

## 异常保留

首次MATLAB目录定位失败、子代理受限偏好目录失败/中断、首次主文11.08316pt行溢出、首次tar长路径失败及漏复制长评估文件导致的clean导出失败均记录于 `step1011_operational_anomalies.json`，对应失败日志和临时副本保留。Git换行提示、PDF文本控制台编码修复和MATLAB矢量导出性能提醒也保留。最终实际复核通过不覆盖这些先前异常。

另外保留来源快照刷新、候选比较器过严断言、宏参数误识别和一次补丁上下文拒绝；这些检查器异常的修正未改写科学数据、求解源码或评估源码。图像元数据/微像素差异与既有透明图例辅助线现象也已记录。

协议完成、浮点接受、有限网格/时域比较与重复局部收敛均不构成连续可行性、收敛定理或全局最优性的新增证明。
"""
    (V / "step1011_results.md").write_text(text, encoding="utf-8")
    status_path = V / "REVISION_STATUS.md"
    status = status_path.read_text(encoding="utf-8")
    status = status.replace("# 第 0–9 步执行状态", "# 第 0–11 步执行状态", 1)
    start = status.index("\n\n| 步骤")
    status = "# 第 0–11 步执行状态\n\n本批仅执行第10–11步；第0–9步记录保持历史证据。计划不作为结果，科学优化0次；候选检出35次可信缓存、1次独立接口smoke。原严格grid一致性失败保留。" + status[start:]
    status = status.replace("| 10：正文、结果宏及图表更新 | not_started | 本批不执行 |", "| 10：正文、结果宏及图表更新 | completed | `step1011_postprocess_report.json`、`step1011_final_export_report.json`、`step1011_pdf_qa.json`；主结果true、协议完成true、一致性false |")
    status = status.replace("| 11：干净复现与最终编译 | not_started | 本批不执行 |", "| 11：干净复现与最终编译 | completed | `step1011_validation_report.json`；候选缓存35、科学重求解0、独立smoke1成功，双版本编译及渲染通过；所有先前异常保留 |")
    status += "\n\n## 第10–11步当前交付\n\n详见 `step1011_results.md`、`step1011_validation_report.json`。当前科学主结果/源码来源与原始字节未改变，三图一表保留；N=16000、T=600及额外初猜未运行。完成表示本批复现与导出执行完成，不代表原严格grid一致性全通过。\n"
    status_path.write_text(status, encoding="utf-8")
    print("STAGE1011_DELIVERY_REGISTERED")


if __name__ == "__main__":
    main()
