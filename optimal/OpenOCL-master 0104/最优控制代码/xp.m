%用多重打靶法求解含有纯状态约束的最优控制问题
% min \int_0^{tf} u(t)^2 d(t)
% 满足方程 dS/dt=-(1-u)*beta*S*I; dI/dt=(1-u)*beta*S*I-gamma*I;
% 控制变量约束 0<=u<=1
% 纯状态变量约束 I<=I_{max}

clc
clear all



r=0.7;ET=1;EIL=1.1;
eta=2;
%initial value
x0=0.5;p0=0.8;


%%求初值
delta1=1;delta0=0.2;
par=[r eta delta0 delta1 ET];
options = odeset('RelTol',1e-12,'AbsTol',[1e-12 1e-12]);
[T,Y] = ode45(@(t,y) xp0(t,y,par),[1 100],[x0 p0],options);
x_0=Y(:,1);p_0=Y(:,2);

figure(1)
subplot(121)
hold on
plot(T,x_0,'-','LineWidth',2)
box on
ylabel('N(t)')
xlabel('Time (Day)')
subplot(122)
hold on
plot(T,p_0,'-','LineWidth',2)
ylabel('p(t)')
xlabel('Time (Day)')
box on


% %title('原始图')
% 
% %% 01 初始参数设置
% p.ns = 2; p.nu = 2;                     % 状态量个数和控制量个数
% p.t0 = 0; p.tf = 100;                     % 初始时间和终止时间
% p.x0 = [x0 p0];                              % 初始条件
% %固定的参数
% p.r=r;p.eta=eta;p.ET=ET;
% %状态约束
% xmax=EIL;
% 
% % 多重打靶法参数设置
% p.N = 100;                               % 打靶点数 => (N-1) 个子时间区段
% p.M = 4;                                % 每个子时间区段包含的打靶点
% p.t = linspace(p.t0,p.tf,p.N);          % 时间序列
% 
% % 设置状态量和控制量的索引
% p.x_index = 1:p.ns*p.N;
% p.u_index = p.ns*p.N+1:(p.ns+p.nu)*p.N;
% %% 02 求解算法
% % 限定0<=u<=1,且I<=2
% lb=zeros((p.ns + p.nu)* p.N, 1);
% ub=ones((p.ns + p.nu)* p.N, 1);
% ub(1:p.N)=xmax*ones(p.N,1);
% % 设置初值
% y0 = zeros((p.ns + p.nu)* p.N, 1);
% y0(p.x_index)=[x_0' p_0'];
% item=find(y0>=ub);
% y0(item)=ub(item);
% % 设定求解器设置
% options = optimoptions('fmincon','Display','Iter','Algorithm','sqp','MaxFunEvals',1e5,'ConstraintTolerance',1e-8); 
% % mc = 10;
% % time_record = zeros(mc,1);
% % 
% % for index = 1:mc
% tic;
% [X,fval,exitflag,output] = fmincon(@(y) objfun(y, p),y0,[],[],[],[],lb,ub,@(y) noncon(y, p),options);
% toc;
% % time_record(index) = toc; 
% % end
% % time_cal = sum(time_record)/mc;
% 
% %% 03 处理数据
% p.x = reshape(X(p.x_index), [], p.ns);
% p.u = reshape(X(p.u_index), [], p.nu);
% % 尝试外推最后一个时间点的值
% % p.u(p.N) = (p.t(p.N)-p.t(p.N-1)) * (p.u(p.N-1)-p.u(p.N-2)) / (p.t(p.N-1)-p.t(p.N-2)) + p.u(p.N-1);
% % % [x(1)-x(2)]/[t(1)-t(2)]=[x(2)-x(3)]/[t(2)-t(3)]
% % 尝试平滑第一个时间点的值
% u0 = p.u(1+1,:) + (p.u(1+1,:)-p.u(2+1,:))*(p.t(0+1,:)-p.t(1+1,:))/(p.t(1+1,:)-p.t(2+1,:));
% p.u(1,:) = u0;
% %% 04 画图
% window_width = 500;
% window_height = 416;
% 
% % 状态量和控制量
% subplot(121)
% hold on
% plot(p.t,p.x(:,1),'r','LineWidth',1.5)
% plot([p.t0 p.tf],[xmax xmax],'k --','LineWidth',1)
% subplot(122)
% hold on
% plot(p.t,p.x(:,2),'b','LineWidth',1.5)
% %legend('S(t) without control','I(t) without control','S(t) with control','I(t) with control','I_{max}')
% % I_opc=p.x(:,2);
% % save OPC.mat T I_0 I_opc
% figure(2)
% hold on
% plot(p.t, p.u(:,1), 'r.-', 'LineWidth',1.5);
% plot(p.t, p.u(:,2), 'b.-', 'LineWidth',1.5);
% %stairs(p.u,'LineWidth',1)
% %% 子函数  
% % 目标函数
% function f = objfun(y,p)
%     % 得到状态量和控制量
%     x = y(p.x_index);
%     u = y(p.u_index);
%     x_x=x(1:100);x_p=x(101:end);
%     u1=u(1:100);u2=u(101:end);
%     % 为了保证 x 和 u 的维度一致，需要对 u 进行外推，得到 u 在末端时刻的值
%     % 利用简单的线性外推方法进行外推
%     % k = (x2-x1)/(t2-t1) == (x3-x2)/(t3-t2)
%     % x3 = (t3-t2)(x2-x1)/(t2-t1) + x2
% %     N = p.N;
% %     t = p.t;
% %     u(N) = (t(N)-t(N-1)) * (u(N-1)-u(N-2)) / (t(N-1)-t(N-2)) + u(N-1);
%     L = u1.*x_p+u2.*(1-x_p) ;            % 积分项
%     f = trapz(p.t,L);               % 计算目标函数
%     %trapz([1 2 4 9])=11; [(1+2)/2]+[(2+4)/2]+[(4+9)]/2
% end
% 
% % 状态方程
% function dy = state_eq(y,u,p)
%  %S=y(1);I=y(2);beta=par(1);gamma=par(2);
%     dy(1)=p.r*y(1)-(u(1)*y(2)+(1-y(2))*u(2))*y(1);
%     dy(2)=p.eta*y(2)*(1-y(2))*(1-y(1)/p.ET);
% end
% 
% % 约束条件
% function [c,ceq] = noncon(y,p)
%     % 得到状态量和控制量
%     x = reshape(y(p.x_index),[],p.ns);
%     u = reshape(y(p.u_index),[],p.nu);
%     
%     % 时间步长
%     h = p.tf/(p.N-1)/(p.M-1);
%     
%     % 每次子时间区段进行单次打靶法
%     states_at_nodes = zeros(p.N, p.ns);
%     for i = 1:p.N-1
%        x0 = x(i,:);
%        u0 = u(i,:);
%        states = zeros(p.M,p.ns);
%        states(1,:) = x0;
%        for j =1:p.M-1
%            k1 = state_eq(states(j,:), u0,p);
%            k2 = state_eq(states(j,:) + h./2.* k1, u0,p);
%            k3 = state_eq(states(j,:) + h./2.* k2, u0,p);
%            k4 = state_eq(states(j,:) + h.*k3, u0,p);
%            states(j+1,:) = states(j,:) + h./6.*(k1 + 2.*k2 + 2.*k3 + k4);
%        end
%        states_at_nodes(i+1,:) = states(end,:);
%     end
%     
%     % 保证各区段起始点的连续性
%     ceq_temp = x(2:end,:) - states_at_nodes(2:end,:);
%     
%     
%     % 把初始时刻的状态约束放到 ceq 中
%     ceq_temp = [ceq_temp; x(1,:) - p.x0];
%     ceq = reshape(ceq_temp, [], 1);
%     
%     % 不等式约束
%     c = [];
% end
% 
% 


function dy =xp0(t,y,par)
%par=[r eta delta0 delta1];
r=par(1);
eta=par(2);
delta0=par(3);
delta1=par(4);
ET=par(5);

dy = zeros(2,1);    % a column vector
x=y(1);
p=y(2);

dy(1)=r*x-(delta0*p+(1-p)*delta1)*x;
dy(2)=eta*p*(1-p)*(1-x/ET);
end
