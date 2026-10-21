# 图1版式微调

基准 `bc4cd3ffbfa48ad894ed3cf0f3f3b4fb3a1da8a1`。本轮只更新图1及删除图注中灰色对照路径的说明，单独本地提交，不推送。

实际修改：隐藏放大图全部坐标刻度，放大图宽高均缩小10%；主图T直接标在紫色区域面积中心附近(0.452,0.139)，删除其引线；移除主图/放大图的“维持至s=h”灰色对照段和文字；灰色选区上沿抬至i=0.166，避开sB文字。主图h点划线及i=K容量线仍按既有定义绘制。新脚本位于本目录，旧生成脚本和验证记录未修改。

实际命令（工作目录为项目目录）：

```powershell
& 'E:/anaconda/python.exe' validation/figure1_layout_20261021/make_optimal_partition.py --attempt 1
& 'C:/Users/cui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' validation/figure1_layout_20261021/build_revision.py --attempt 1
git diff --check
git diff --cached --check -- '*.tex' '*.py' '*.md' '*.json'
```

PDF编辑标记在仓库根目录实际运行一次，operation-kind=edit、expected-output-count=3。两份PDF实际各执行XeLaTeX→BibTeX→XeLaTeX→XeLaTeX，共8个进程全部退出0；主文41页、TheoryOnly31页，最终日志无错误、警告、未定义引用、缺字或溢出。编译的逐条绝对argv、cwd、退出码与源/图/PDF哈希见attempt1/build_report.json。

实际使用pdftoppm -r 150渲染主文第8页、TheoryOnly第7页并逐页目视通过；逐条argv、图页哈希见render_manifest.json，页面保存在rendered_pages_150dpi/。新PNG另有独立目视记录independent_visual_review.md/json。

几何点、E1/E2轨道端点和解析成本与上一提交完全相同；本轮文本仅删除图注的一行，所有模型、证明、其他正文和两个自动数值块不变。1515个既有保护文件（包括图2/N2/N3及历史记录）SHA256不变。新图文字碰线和文字重叠均为0。解析核对及前后图SHA在analytic_checks.json，完整范围核对见audit_report.json。

MATLAB、优化器、新增OCP求解、ODE积分均0次。页数与基准相同，没有触发停止条件或需要放宽的标准。完整文件清单见changed_files.txt。完成后等待作者审阅。
