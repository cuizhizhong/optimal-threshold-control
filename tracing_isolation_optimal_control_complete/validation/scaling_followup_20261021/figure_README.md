# 图 2 后续解析核查

实际成功运行：`python tracing_isolation_optimal_control_complete/validation/scaling_followup_20261021/figure_followup.py --attempt 3`。
以旧 D 脚本为底稿复制纯解析函数；不导入旧脚本，不写入旧验证目录。mpmath 80 位标量根与闭式公式，无 MATLAB、优化器、OCP 或 ODE 调用。

扫描固定 beta*c=1、gamma=0.3、s0=0.9999、i0=0.0001；与旧图完全相同的 620 个点。前三面板、K 网格与 mask 均逐项相同（30 项通过）；唯一排除点为 beta=0.13,K=0.15，因共同容量入口条件不成立。

第四面板逐点使用公共尾段公式 Delta_T=T_B(s_B,h)-log(K/i_bar)/gamma，再计算 beta*gamma*Delta_T；不由两个总时长相减。横轴为对数 K，y=1 虚线给出固定 beta 时的 K→0 极限。

| beta=0.5 的 K | beta*gamma*Delta_T | 四位小数参照 |
|---|---:|---:|
| .01 | 0.86672141341110843109958 | 0.8667 |
| .001 | 0.98376000591852332736489 | 0.9838 |
| .0001 | 0.99833772620248034390325 | 0.9983 |

正文实测宽度 469.47049 TeX pt，PDF 实际宽度 467.7165529265 bp；插图不缩放。刻度 8 pt、标签 9 pt，Times New Roman/STIXGeneral 与 stix 数学字体。

外置子图字母和单次顶部图例；去掉英文脚注。沿用图 1 的实际文字框与密曲线核查，并加入全局图例外框与所有曲线核查；所有文字框对亦检查，结果均零相交。

`figure_checks.json` 为主核查，`figure_data.json` 存全部作图数据，`label_collision_checks.json` 存文字碰撞检查；每次尝试单独存入 figure_attemptN。最终图输出到 figures/scaling/FigD_magnitude.pdf 与 .png。旧 D 图、旧脚本及 FigN1_regions/FigN2/FigN3/FigN1_optimal_partition 均经 SHA-256 核对未变。

首次尝试保留了文字框相交失败记录：LogLocator 返回实际窗外刻度，以及左下角刻度间距不足。第二次采用 Axis 实际绘制时的坐标窗筛选并增大 x 刻度间距，检查通过；此后只修正本说明中实际命令的 attempt 编号并保留新的核查。

最终 PDF 已用 pdftoppm -r 150 -png -singlefile 渲染，结果见 figure_attempt3/pdf_render_150dpi.png；其 SHA-256 与已经目视检查的第二次渲染逐字节一致。四面板、外置标签与图例均清楚，d 图向左趋于 y=1，未见裁切或重叠。pdffonts 实际确认嵌入 Times New Roman 正体/粗体及 STIXGeneral 正体/斜体，日志保存在 figure_attempt3/pdffonts.txt。
