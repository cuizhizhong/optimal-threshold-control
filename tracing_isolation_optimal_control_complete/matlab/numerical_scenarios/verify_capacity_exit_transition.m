function report = verify_capacity_exit_transition()
% 事件区间不由解析时刻改变；单单元包含与网格尺度一致分开断言。
checks={};
a=struct('type',{'q_B','transition','1'},'t_start',{0,1,1.1}, ...
    't_end',{1,1.1,2},'cells',{10,1,9});
r=capacity_exit_transition(a,1.05);
assert(r.supported && r.contains_theory && r.grid_scale_pass);
record('single_cell_containment');
r=capacity_exit_transition(a,1); assert(r.supported);
r=capacity_exit_transition(a,1.1); assert(r.supported);
record('closed_interval_endpoints');
r=capacity_exit_transition(a,1.2);
assert(~r.supported && ~r.contains_theory && r.grid_scale_pass && ...
    abs(r.time_distance_to_interval-0.1)<1e-12 && isequal(r.interval,[1 1.1]));
record('outside_interval_within_one_cell_without_expansion');
r=capacity_exit_transition(a,1.31);
assert(~r.supported && ~r.grid_scale_pass && strcmp(r.status,'outside_grid_scale'));
record('outside_one_cell_distance');
b=a; b(2).cells=2; b(2).t_end=1.2; b(3).t_start=1.2; b(3).cells=8;
r=capacity_exit_transition(b,1.15);
assert(~r.supported && r.grid_scale_pass && r.contains_theory && r.cells==2);
record('two_cells_accepted_without_single_cell_claim');
b=a; b(2).cells=3; b(2).t_end=1.3; b(3).t_start=1.3; b(3).cells=7;
r=capacity_exit_transition(b,1.15);
assert(~r.supported && ~r.grid_scale_pass && strcmp(r.status,'too_many_transition_cells'));
record('more_than_two_cells_rejected');
b=a; b(1).type='0'; r=capacity_exit_transition(b,1.05);
assert(~r.supported && strcmp(r.status,'missing_transition'));
r=capacity_exit_transition(a([]),1); assert(~r.supported && r.candidate_count==0);
record('missing_capacity_exit');
r=capacity_exit_transition([a a],1.05);
assert(strcmp(r.status,'ambiguous_transitions') && r.candidate_count==2 && ...
    numel(r.candidates)==2 && ~r.grid_scale_pass);
record('all_ambiguous_candidates_retained');
b=a; b(2).t_start=1.01; r=capacity_exit_transition(b,1.05);
assert(strcmp(r.status,'invalid_interval') && ~r.supported && ~r.grid_scale_pass);
record('nonadjacent_interval_rejected');
b=a([1 3]); b(2).t_start=1; b(2).cells=10;
r=capacity_exit_transition(b,1.05);
assert(strcmp(r.status,'direct_jump') && isequal(r.interval,[1 1]) && ...
    r.cells==0 && ~r.supported && ~r.contains_theory && r.grid_scale_pass);
record('direct_jump_shared_endpoint');
raw=capacity_exit_transition(a); compared=capacity_exit_transition(a,20);
assert(isequaln(raw.candidates,compared.candidates) && isequal(raw.interval,compared.interval));
record('theory_independent_detection');
r=capacity_exit_transition(a([]),NaN);
assert(strcmp(r.status,'not_applicable') && isempty(r.theory_time) && ...
    isempty(r.time_distance_to_interval) && ~r.contains_theory);
record('absent_theoretical_stage_not_fake_time_pass');
b=a; b(1).type='0'; b(2).type='0'; b(3).type='0';
r=capacity_exit_transition(b,1.05); assert(r.candidate_count==0);
record('zero_control_capacity_contact_not_paid_capacity');
report=struct('test','verify_capacity_exit_transition','passed',true, ...
    'case_count',numel(checks),'checks',{checks}, ...
    'execution_type','synthetic_unit_tests_no_optimizer');
fprintf('CAPACITY_EXIT_TRANSITION_CHECKS_OK cases=%d\n',numel(checks));

    function record(name)
        checks{end+1}=name;
    end
end
