# C1--C4 集成后的只读复核（2026-10-21）

范围：`git diff -- latex/main.tex latex/references.bib`，聚焦 C2、C4、证明依赖与教材来源。未修改论文。

## 必要修正

1. **C4 免费等待变分的适用域。** 初稿写“对 $x\in\mathcal E$，先自然免费等待，再完全跟踪”的指定策略，这包括 $i=K,s>h$，从这样的容量点出发任意正时间的零控制会立即超限。应限制为 $x\in\mathcal E\cap\{i<K\}$，并明确短自然弧保持在 $\mathcal E$ 和容量下方。容量线上的变分应使用 $C_B+W$ 的完整成本，而非称为免费等待。该点已向主任务报告。
2. 移除引理后有几处替换残句需顺文字：
   - “绝对连续函数的水平集性质的零水平集性质”改为“绝对连续函数的零水平集性质”；
   - “绝对连续函数的水平集性质的第二条”不再有编号，改为“两个绝对连续函数在该可测集合相等时，其导数几乎处处相等的性质”；
   - “上述复合引理”改为“上述复合性质”。

## 已核对通过

- 使用 Python 将 HEAD 的 `prop:regularity` 证明和当前新 `app:regularity-proof` 证明逐字符比较，结果为 True，两者均为 3362 个字符。完整证明无损搬移。
- `ref`/`eqref` 与 `label` 扫描没有发现实际缺失标签；唯一的 `#1` 来自既有宏 `NumTheoryRef`，不是缺失引用。
- 新总定理明确以已存在的最优性定理、唯一性定理和综合推论作后续证明，原推导没有调用新总定理；未发现循环证明。
- 主结果保持常系数、正感染物理域、全可测可行控制类、全时间轴 a.e. 唯一性的条件，没有把条件性时变结论合并为无条件结果。
- 标准事实段对 Fremlin 所引位置适用；尤其明确二维相对局部 Lipschitz 版本是有限局部化所得，并未误称教材标量练习原文直接覆盖二维相对版本。
- 正文保留容量/安全时间集、严格横穿与容量延续证明，未以二维状态空间 a.e. 可微替代沿轨道论证。
- C3 可行性命题加入后，原扩展局限已同步区分“可行域已完成”与“成本最优反馈和验证函数仍未构造”。

## Fremlin 的出版信息证据

当前条目作者为 David H. Fremlin，出版社为 Torres Fremlin，地址 Colchester，年份 2001。Torres Fremlin 是出版社，不是本书作者。以下是一手或作者官方证据：

1. [原书 PDF（NTNU 大学课程托管）](https://wiki.math.ntnu.no/_media/tma4225/2011/fremlin-vol2.pdf)，物理第 4 页的版权页明确写首版 2001、出版社 Torres Fremlin、地址 Colchester；物理第 2 页写首版 May 2001、second edition January 2010。原书内容本身是出版信息的一手证据，托管站点不是作者官网。
2. [作者官网总序 PDF](https://www1.essex.ac.uk/maths/people/Fremlin/chap0.ro.pdf)，物理第 1 页明确 Volume 2: Broad Foundations 的首版 May 2001，后有 2003 重印和 2010 精装版信息。
3. [作者官网的自引论文/笔记](https://www1.essex.ac.uk/maths/people/fremlin/n08j04.pdf)，末页参考文献将其自引为 `Fremlin D.H.[01] Measure Theory,Vol.2:Broad Foundations.Torres Fremlin,2001`，直接支持作者、书名、卷次、出版社和年份。
4. [作者官网书目主页](https://www1.essex.ac.uk/maths/people/fremlin/mt.htm) 确认整套书的作者与卷次。
5. [作者官网售书页](https://www1.essex.ac.uk/maths/people/fremlin/mtsales.htm) 确认第二卷标题及 ISBN 978-0-9538129-7-4；该 ISBN 对应后续精装印本，不建议额外填进仅按 2001 首版著录的条目而不注明版本。
6. [作者官网 2016 卷二源文件目录](https://www1.essex.ac.uk/maths/people/fremlin/mt2.2016/index.htm) 确认当前可用源文件属于 2016 printing。本轮实际核对的逐章官方 PDF 是在线修订稿；正文引用章节代码，验证记录应保留该访问来源，不冒称核对了 2001 纸本每一页。

出版信息本身可保留当前 `references.bib` 条目；无需为出版社名称要求作者再次决定。
