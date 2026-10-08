% 保存数据复核，不构建 OCP 或调用优化器。
evidenceRoot=fileparts(mfilename('fullpath'));
projectRoot=fileparts(fileparts(evidenceRoot));
addpath(evidenceRoot,fullfile(projectRoot,'matlab','numerical_scenarios'));
report=verify_stage89_initializations();
assert(report.passed,'stage89:InitializationsFailed','Saved initialization reconstruction failed; see recorded rows.');
