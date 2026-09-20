function export_numerical_latex()
% 从实际保存数据生成成本、汇总及简短结果说明，不运行优化。
cfg=numerical_cases_config(); runs=cell(1,5); passed=false(1,5);
for k=1:5
    d=load(fullfile(cfg.paths.data,sprintf('E%d.mat',k)),'run'); runs{k}=d.run;
    assert(isfield(d.run,'assessment'),'Missing numerical assessment.');
    passed(k)=d.run.success && d.run.assessment.passed && ...
        strcmp(d.run.assessment.observed_structure,cfg.cases(k).expected_structure);
end
checks=struct();
for id={'E2','E1'}
    f=fullfile(cfg.paths.data,'checks',[id{1} '.mat']);
    if isfile(f)
        d=load(f,'run'); checks.(id{1})=compact(d.run);
    end
end
checksOK=isfield(checks,'E1') && isfield(checks,'E2');
if checksOK, checksOK=checks.E1.assessment.passed && checks.E2.assessment.passed; end
verified=all(passed) && checksOK;
summary=repmat(compact(runs{1}),1,5);
for k=1:5, summary(k)=compact(runs{k}); end
out=struct('verified',verified,'cases',summary,'additional_checks',checks);
writefile(fullfile(cfg.paths.data,'numerical_checks.json'),jsonencode(out,PrettyPrint=true));
rows=cell(5,10);
for k=1:5
    r=runs{k}; rows(k,:)={r.case_id,r.x0(1),r.x0(2),r.reference.region, ...
        cfg.cases(k).expected_structure,r.assessment.observed_structure, ...
        r.reference.J_reference,r.J_openocl,r.solver_settings.N,r.assessment.passed};
end
tab=cell2table(rows,'VariableNames',{'case_id','s0','i0','region','expected_structure', ...
    'observed_structure','J_reference','J_openocl','N','checks_passed'});
writetable(tab,fullfile(cfg.paths.data,'scenario_summary.csv'));
suffix={'One','Two','Three','Four','Five'};
reference={'% MATLAB 解析公式评价；不含优化器结果。'};
pending={'% 从 data/numerical_scenarios 的真实结果生成；条件开关由 main.tex 定义。'};
if verified, pending{end+1}='\NumResultsVerifiedtrue'; else, pending{end+1}='\NumResultsVerifiedfalse'; end
pending{end+1}=macro('NumHorizon',sprintf('%g',runs{1}.solver_settings.T));
pending{end+1}=macro('NumIntervals',sprintf('%d',cfg.solve.N));
pending{end+1}=macro('NumDegree',sprintf('%d',runs{1}.solver_settings.d));
mesh={};
for k=1:5
    if runs{k}.solver_settings.N~=cfg.solve.N
        mesh{end+1}=sprintf('E%d 使用 $N=%d$',k,runs{k}.solver_settings.N); %#ok<AGROW>
    end
end
if isempty(mesh)
    pending{end+1}=macro('NumMeshDetails','五个主算例均使用上述网格。');
else
    pending{end+1}=macro('NumMeshDetails',['容量重积分核查后，' strjoin(mesh,'，') ...
        '；其余算例保留基准网格。图表均采用各例最终保存的结果。']);
end
for k=1:5
    reference{end+1}=macro(['NumJRefE' suffix{k}],sprintf('%.6f',runs{k}.reference.J_reference)); %#ok<AGROW>
    if runs{k}.success
        pending{end+1}=macro(['NumJOclE' suffix{k}],sprintf('%.6f',runs{k}.J_openocl)); %#ok<AGROW>
    else
        pending{end+1}=macro(['NumJOclE' suffix{k}],'未收敛'); %#ok<AGROW>
    end
end
g=build_theory_geometry(cfg.parameters); e=runs{1}.reference.events;
reference{end+1}=macro('NumSBRef',sprintf('%.8f',g.s_B));
reference{end+1}=macro('NumSwitchSEOneRef',sprintf('%.8f',e.full_state(1)));
reference{end+1}=macro('NumSwitchIEOneRef',sprintf('%.8f',e.full_state(2)));
reference{end+1}=macro('NumMaxReleaseRef',sprintf('%.8f',max(cellfun(@(r) r.reference.events.release,runs))));
e1=runs{1}.assessment.events; e2=runs{2}.assessment.events; e4=runs{4}.assessment.events;
waiting=sprintf(['实际控制输出中，E1 和 E2 分别识别出 $%s$ 与 $%s$。' ...
    '按控制区间识别，E1 的首个完全跟踪区间从 $t\\approx %.3f$ 开始，' ...
    '其状态约为 $(%.4f,%.4f)$，感染比例低于容量；' ...
    'E2 则出现正长度容量平台，随后转为完全跟踪。' ...
    '跳跃附近存在有限个过渡单元，因此这里的事件时刻只按当前网格精度解释。'], ...
    texstructure(runs{1}.assessment.observed_structure),texstructure(runs{2}.assessment.observed_structure), ...
    e1.full_start,e1.full_state(1),e1.full_state(2));
boundary=sprintf(['E3、E4、E5 的实际阶段依次为 $%s$、$%s$ 和 $%s$。' ...
    'E3 与 E5 均从初始正长度区间开始完全跟踪；E4 先维持容量平台。' ...
    'E2、E4 的首个完全跟踪区间起点分别约为 $(%.4f,%.4f)$ 和 $(%.4f,%.4f)$，' ...
    '可与共同理论容量退出点 $(s_B,K)$ 对照，二者并不要求在同一时刻离开平台。'], ...
    texstructure(runs{3}.assessment.observed_structure),texstructure(runs{4}.assessment.observed_structure), ...
    texstructure(runs{5}.assessment.observed_structure),e2.full_state(1),e2.full_state(2),e4.full_state(1),e4.full_state(2));
cap=max(cellfun(@(r) r.assessment.capacity_excess,runs));
state=max(cellfun(@(r) r.assessment.state_discrepancy,runs));
tail=max(cellfun(@(r) r.assessment.tail_max_q,runs));
checktext=sprintf(['对原始分段常数控制逐区间重积分后，五例最大容量超出量为 $\\num{%.2g}$，' ...
    '与配点状态的最大差异为 $\\num{%.2g}$；末尾 $20$ 个时间单位内最大控制幅值为 $\\num{%.2g}$。'],cap,state,tail);
if verified
    checktext=[checktext '各例终端状态均通过零控制安全延拓核查。' ...
        '另对 E2 使用 $N=8000$ 加密，并对 E1 使用常值 $q=0.7$ 生成非理论初始猜测，' ...
        '所得解均通过同样核查；这些浮点检查用于排查截断及离散问题，不是连续可行性的严格证明。'];
    finding=sprintf(['五例成本相对解析参考的最大差异约为 $%.3g\\%%$。' ...
        '计算结果支持这五个初值下的阶段顺序及切换位置预测；' ...
        '切换位置的偏差应结合控制区间宽度和过渡单元解释。'], ...
        100*max(cellfun(@(r) abs(r.assessment.relative_cost_difference),runs)));
else
    checktext=[checktext '尚有核查未通过或附加实验未完成，当前结果不标记为已验证；具体状态见配套核查文件。'];
    finding='当前数值验证尚未全部通过；成本列为实际求解输出，不以解析值填补或替换。';
end
pending{end+1}=macro('NumFindingWaiting',waiting);
pending{end+1}=macro('NumFindingTrackingBoundary',boundary);
pending{end+1}=macro('NumCheckStatement',checktext);
pending{end+1}=macro('NumOverallFinding',finding);
writefile(fullfile(cfg.paths.latex,'numerical_reference_values.tex'),strjoin(reference,newline));
writefile(fullfile(cfg.paths.latex,'numerical_pending.tex'),strjoin(pending,newline));
fprintf('NUMERICAL_LATEX_EXPORTED verified=%d\n',verified);
end

function c=compact(r)
c=struct('case_id',r.case_id,'x0',r.x0,'parameters',r.parameters, ...
    'solver_settings',r.solver_settings,'initialization',r.initialization, ...
    'success',r.success,'return_status',r.return_status,'J_reference',r.reference.J_reference, ...
    'J_openocl',r.J_openocl,'assessment',rmfield(r.assessment,'reintegration'));
end
function s=texstructure(s)
s=strrep(s,' -> ','\to ');
end
function s=macro(name,value)
s=['\providecommand{\' name '}{' value '}'];
end
function writefile(path,text)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cleaner=onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',text);
end
