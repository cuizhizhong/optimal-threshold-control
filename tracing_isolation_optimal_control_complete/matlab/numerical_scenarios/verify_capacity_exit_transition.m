function verify_capacity_exit_transition()
% 事件说明必须依赖真实邻接关系，异常时不能导出“单网格包含”结论。
a=struct('type',{'q_B','transition','1'},'t_start',{0,1,1.1}, ...
    't_end',{1,1.1,2},'cells',{10,1,9});
r=capacity_exit_transition(a,1.05); assert(r.supported && r.contains_theory);
r=capacity_exit_transition(a,1); assert(r.supported);
r=capacity_exit_transition(a,1.1); assert(r.supported);
r=capacity_exit_transition(a,1.2); assert(~r.supported && strcmp(r.status,'theory_outside'));
b=a; b(2).cells=2; r=capacity_exit_transition(b,1.05);
assert(~r.supported && strcmp(r.status,'multiple_cells'));
b=a; b(1).type='0'; r=capacity_exit_transition(b,1.05);
assert(~r.supported && strcmp(r.status,'missing_transition'));
r=capacity_exit_transition(a([]),1); assert(~r.supported);
r=capacity_exit_transition([a a],1.05); assert(strcmp(r.status,'ambiguous_transitions'));
b=a; b(2).t_start=1.01; r=capacity_exit_transition(b,1.05);
assert(strcmp(r.status,'invalid_interval'));
fprintf('CAPACITY_EXIT_TRANSITION_CHECKS_OK\n');
end
