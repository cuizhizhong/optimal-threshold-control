


function dydt=ODE_SI(t, y)
global  beta  gamma  c_0  t1  t2 S0 I0 I_m Sc C S_star

if t < t1
    q = 0;
elseif t >= t1 & t < t2   
    denominator = (beta*c_0*S_star - gamma*(1-beta)) * exp(-c_0*I_m*(t - t1)) ...
              + gamma*(1-beta);
    q_star = 1 - gamma / denominator;
    q = q_star;
else
    q = 0;
end

dydt=zeros(2,1);
S=y(1);   I=y(2);    
dydt(1) =  - c_0 *(beta + (1 - beta) * q) * S* I; 
dydt(2) =  beta * c_0 * (1-q)* S*I - gamma*I; 

end

