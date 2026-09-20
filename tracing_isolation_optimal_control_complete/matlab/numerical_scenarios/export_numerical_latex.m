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
neutral=[]; f=fullfile(cfg.paths.data,'checks','neutral_E2','E2.mat');
if isfile(f)
    d=load(f,'run'); neutral=d.run;
    if isfield(neutral,'assessment') && isfield(neutral,'reference')
        checks.neutral_E2=compact(neutral);
    end
end
neutralCheck=compare_neutral_initialization(runs{2},neutral,cfg.check);
failurePath=fullfile(cfg.paths.data,'checks','neutral_E2','E2_failure.mat');
if isempty(neutral) && isfile(failurePath)
    d=load(failurePath,'failure'); neutralCheck.status='error';
    neutralCheck.failure=d.failure;
end
exitChecks=struct();
for k=[2 4]
    exitChecks.(sprintf('E%d',k))=capacity_exit_transition( ...
        runs{k}.assessment.arcs,runs{k}.reference.events.full_start);
end
summary=repmat(compact(runs{1}),1,5);
for k=1:5, summary(k)=compact(runs{k}); end
out=struct('verified',verified,'cases',summary,'additional_checks',checks, ...
    'neutral_E2_check',neutralCheck,'capacity_exit_checks',exitChecks);
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
e1=runs{1}.assessment.events;
waiting=sprintf(['实际控制输出中，E1 和 E2 分别识别出 $%s$ 与 $%s$。' ...
    '按控制区间识别，E1 的首个完全跟踪区间从 $t\\approx %.3f$ 开始，' ...
    '其状态约为 $(%.4f,%.4f)$，感染比例低于容量；' ...
    'E2 则出现正长度容量平台，随后转为完全跟踪。' ...
    '跳跃附近存在有限个过渡单元，因此这里的事件时刻只按当前网格精度解释。'], ...
    texstructure(runs{1}.assessment.observed_structure),texstructure(runs{2}.assessment.observed_structure), ...
    e1.full_start,e1.full_state(1),e1.full_state(2));
boundary=sprintf(['E3、E4、E5 的实际阶段依次为 $%s$、$%s$ 和 $%s$。' ...
    'E3 与 E5 均从初始正长度区间开始完全跟踪；E4 先维持容量平台。'], ...
    texstructure(runs{3}.assessment.observed_structure),texstructure(runs{4}.assessment.observed_structure), ...
    texstructure(runs{5}.assessment.observed_structure));
if exitChecks.E2.supported && exitChecks.E4.supported
    boundary=[boundary 'E2、E4 的理论容量退出时刻均位于各自容量段与完全跟踪段之间的单网格过渡区间内，' ...
        '因此不将首个纯完全跟踪单元的起点直接等同于连续切换点。'];
else
    boundary=[boundary sprintf(['容量退出过渡区间的自动核查未全部支持单网格包含结论（E2: %s；E4: %s），' ...
        '不能据首个纯完全跟踪单元确定连续切换点。'], ...
        strrep(exitChecks.E2.status,'_','-'),strrep(exitChecks.E4.status,'_','-'))];
end
for k=[2 4]
    e=exitChecks.(sprintf('E%d',k));
    pending{end+1}=macro(sprintf('NumExitE%sStart',suffix{k}),sprintf('%.8f',e.interval(1))); %#ok<AGROW>
    pending{end+1}=macro(sprintf('NumExitE%sEnd',suffix{k}),sprintf('%.8f',e.interval(2))); %#ok<AGROW>
    reference{end+1}=macro(sprintf('NumExitE%sTheory',suffix{k}),sprintf('%.8f',e.theory_time)); %#ok<AGROW>
end
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
if neutralCheck.passed
    checktext=[checktext sprintf(['对 E2 另以常值 $q=0.7$ 及其积分状态为初猜重新求解，' ...
        '所得阶段顺序与解析初始化相同，成本绝对差为 $\\num{%.3g}$，并通过同样的数值核查。'], ...
        neutralCheck.absolute_cost_difference)];
elseif strcmp(neutralCheck.status,'missing')
    checktext=[checktext 'E2 的非解析初猜复核尚无可用结果，当前不作初猜一致性结论。'];
else
    checktext=[checktext 'E2 的非解析初猜复核未通过预定的一致性与数值核查，具体结果见复核记录；' ...
        '五个主算例的通过状态不代替这项独立复核。'];
end
pending{end+1}=macro('NumNeutralETwoCostDifference',sprintf('%.12g',neutralCheck.absolute_cost_difference));
gap=runs{4}.J_openocl-runs{4}.reference.J_reference;
pending{end+1}=macro('NumEFourSignedCostDifference',sprintf('%.12g',gap));
pending{end+1}=macro('NumEFourCapacityExcess',sprintf('%.12g',runs{4}.assessment.capacity_excess));
if gap<0
    finding=[finding sprintf(['E4 的离散成本比解析参考低约 $\\num{%.3g}$，' ...
        '其重积分轨道同时存在约 $\\num{%.3g}$ 的容量超出；' ...
        '该结果不能视为低于解析最优值的严格连续时间可行控制。'], ...
        -gap,runs{4}.assessment.capacity_excess)];
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
    'J_openocl',r.J_openocl,'reference_events',r.reference.events, ...
    'assessment',rmfield(r.assessment,'reintegration'));
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
