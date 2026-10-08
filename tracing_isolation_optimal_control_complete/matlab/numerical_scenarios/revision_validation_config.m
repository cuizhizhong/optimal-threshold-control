function cfg = revision_validation_config(inputPath)
% 第6步的预先固定协议；此文件只列配置，任何阈值都不是实测结果。
if nargin<1, cfg=numerical_cases_config(); else, cfg=numerical_cases_config(inputPath); end
ids={'E1','E2','E3','E4','E5'};
x0=[0.75 0.99 0.50 0.70 0.50;0.01 0.01 0.14 0.15 0.15];
mainN=[4000 8000 4000 8000 4000];
assert(isequal(cfg.parameters,struct('p',0.5,'c',2,'gamma',0.3,'K',0.15)), ...
    'revision:ChangedProtocol','Shared parameters differ from the approved revision protocol.');
for k=1:5
    ix=find(strcmp({cfg.cases.id},ids{k}));
    assert(isscalar(ix) && isequal(cfg.cases(ix).x0,x0(:,k)) && cfg.cases(ix).main_N==mainN(k), ...
        'revision:ChangedProtocol','Shared input or main_N changed for %s.',ids{k});
end
cfg.revision=struct('schema_version',1,'protocol_version','2026-10-08-step6-v1', ...
    'default_unique_count',35,'unit_function','verify_revision_validation_unit', ...
    'mode_order',{{'unit','main','initialization','grid','horizon','threshold'}}, ...
    'allowed_modes',{{'unit','main','initialization','grid','horizon','threshold','all','extended'}}, ...
    'random_seed_base',20261008,'random_value_bounds',[0.15 0.85], ...
    'initialization_cost_absolute_tolerance',1e-5, ...
    'grid_cost_relative_tolerance',1e-4,'horizon_cost_absolute_span_tolerance',1e-5, ...
    'threshold_control',[5e-4 1e-3 2e-3],'threshold_capacity',[1e-5 2e-5 4e-5], ...
    'refinement_max_N',16000,'automatic_refinement',false,'extended_experiments',[]);
cfg.revision.experiments=struct('case_id',{},'parameters',{},'x0',{},'solver_settings',{}, ...
    'initialization',{},'configuration_id',{},'configuration_fingerprint',{},'groups',{}, ...
    'expected_region',{},'expected_structure',{});
for k=1:5, add(ids{k},300,mainN(k),struct('type','analytic_reference'),'main'); end
for k=1:5
    add(ids{k},300,mainN(k),struct('type','constant_control','control',0.7),'initialization-constant');
end
for k=1:5
    seed=cfg.revision.random_seed_base+k;
    knots=unique([0:2:20 300])';
    stream=RandStream('mt19937ar','Seed',seed);
    values=0.15+0.70*rand(stream,numel(knots),1);
    guess=struct('type','seeded_random','seed',seed,'generator','mt19937ar', ...
        'interpolation','linear','knot_times',knots,'knot_values',values,'value_bounds',[0.15 0.85]);
    add(ids{k},300,mainN(k),guess,'initialization-random');
end
for k=1:5
    for N=[2000 4000 8000], add(ids{k},300,N,struct('type','analytic_reference'),'grid'); end
end
for k=1:5
    for pair=[60 120 300;1600 3200 8000]
        add(ids{k},pair(1),pair(2),struct('type','analytic_reference'),'horizon');
    end
end
experiments=cfg.revision.experiments;
assert(numel(experiments)==35 && numel(unique({experiments.configuration_fingerprint}))==35, ...
    'revision:InvalidMatrix','The default protocol must contain exactly 35 distinct configurations.');
assert(sum(arrayfun(@(e) any(strcmp(e.groups,'main')),experiments))==5);
assert(sum(arrayfun(@(e) any(strcmp(e.groups,'grid')),experiments))==15);
assert(sum(arrayfun(@(e) any(strcmp(e.groups,'horizon')),experiments))==15);
cfg.revision.protocol_hash=numerical_sha256(struct('protocol',cfg.revision,'check',cfg.check));

    function add(id,T,N,guess,group)
        ix=find(strcmp({cfg.cases.id},id)); opts=cfg.solve;
        opts.T=T; opts.N=N; opts.d=2; opts.initialization=guess.type;
        payload=struct('case_id',id,'parameters',cfg.parameters,'x0',cfg.cases(ix).x0, ...
            'solver_settings',opts,'initialization',guess);
        hash=numerical_sha256(payload);
        previous=find(strcmp({cfg.revision.experiments.configuration_fingerprint},hash));
        if ~isempty(previous)
            assert(isscalar(previous),'revision:DuplicateConfiguration','Duplicated protocol configuration.');
            cfg.revision.experiments(previous).groups{end+1}=group;
            return;
        end
        row=payload; row.configuration_id=sprintf('C%02d',numel(cfg.revision.experiments)+1);
        row.configuration_fingerprint=hash; row.groups={group};
        row.expected_region=cfg.cases(ix).expected_region;
        row.expected_structure=cfg.cases(ix).expected_structure;
        if isempty(cfg.revision.experiments), cfg.revision.experiments=row;
        else, cfg.revision.experiments(end+1)=row; end
    end
end
