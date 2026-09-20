function run_legacy_baseline()
% 在独立结果目录调用原始脚本，避免覆盖原图；完整区间成本另算。
cfg=numerical_cases_config(); addpath(cfg.paths.openocl_root); ocl;
addpath(fullfile(cfg.paths.openocl_root,'cui'));
out=fullfile(cfg.paths.data,'legacy_baseline'); if ~isfolder(out), mkdir(out); end
old=pwd; cleanup=onCleanup(@() cd(old)); cd(out);
set(groot,'defaultFigureVisible','off');
[solution,times,problem]=CUI_q();
run.t_state=reshape(times.states.value,[],1); run.s_state=reshape(solution.states.S.value,[],1);
run.i_state=reshape(solution.states.I.value,[],1); run.t_control=reshape(times.controls.value,[],1);
run.q_control=reshape(solution.controls.q.value,[],1); run.dt_control=diff([run.t_control;300]);
run.J_openocl=cfg.parameters.p*cfg.parameters.c*sum(run.q_control.*run.dt_control);
run.info=problem.solver.info(); run.matlab_version=version;
save('legacy_E2.mat','run');
fprintf('LEGACY_BASELINE_OK J_interval=%.12f success=%d\n',run.J_openocl,run.info.success);
end
