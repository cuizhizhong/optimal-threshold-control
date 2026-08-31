function vanderpol2
  problem = ocl.Problem(10, @varsfun, @daefun, @pathcost, 'N', 30);

  problem.setInitialBounds('x',     0);
  problem.setInitialBounds('y',     1);

  problem.initialize('x', [0 1], [-0.2 -0.2]);

  [solution,timepoints] = problem.solve()
  


  % plotting of control and state p trajectory:
  %ocl.plot(timepoints.controls, solution.controls.u)
  %ocl.plot(timepoints.states, solution.states.x)
end

function varsfun(vh)
  vh.addState('x', 'lb', -0.25, 'ub', inf);
  vh.addState('y');
  vh.addControl('F', 'lb', -1, 'ub', 1);
end

function daefun(daeh,x,z,u,p)
  daeh.setODE('x', (1-x.y^2)*x.x - x.y + u.F);
  daeh.setODE('y', x.x);
end

function pathcost(ch,x,z,u,p)
  ch.add( x.x^2 );
  ch.add( x.y^2 );
  ch.add( u.F^2 );
end