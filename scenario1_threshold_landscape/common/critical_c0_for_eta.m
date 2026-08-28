function c0_min = critical_c0_for_eta(beta, gamma, q0, N, eta, S0, I0)
%CRITICAL_C0_FOR_ETA Smallest background contact level that reaches eta.

H = beta + q0 * (1 - beta);
a = beta * (1 - q0) / H;
if ~(I0 < eta && eta < I0 + a * S0)
    error('critical_c0_for_eta:invalidThreshold', ...
        'The threshold eta must satisfy I0 < eta < I0 + a*S0.');
end

growth_boundary = gamma * N / (beta * (1 - q0) * S0);
peak_gap = @(c0) normal_peak(c0, beta, gamma, q0, N, S0, I0, a) - eta;
upper = max(2 * growth_boundary, 1);
while peak_gap(upper) <= 0
    upper = 2 * upper;
end
c0_min = fzero(peak_gap, [growth_boundary, upper]);
end

function I_peak = normal_peak(c0, beta, gamma, q0, N, S0, I0, a)
S_c = gamma * N / (beta * c0 * (1 - q0));
I_peak = I0 + a * (S0 - S_c) + a * S_c * log(S_c / S0);
end
