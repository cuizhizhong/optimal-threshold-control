function Figure_1_phase_plane
% Figure 1: phase portrait for the exact proportional two-rate model.
% The file is self-contained and saves ../figures/Figure_1_phase_plane.jpg.

beta1_bar = 1.0;
q = 0.8;
beta2_bar = q * beta1_bar;
gamma = 0.3;
S0 = 0.99;
I0 = 0.01;
K = 0.15;

S_h = gamma / beta2_bar;
I_lf = @(S) I0 + q .* (S0 - S) + (gamma / beta1_bar) .* log(S ./ S0);
S1 = fzero(@(S) I_lf(S) - K, [S_h, S0]);
S_inf_lf = fzero(@(S) I_lf(S), [1e-9, S_h]);
I_crit = @(S) K + q .* (S_h - S) + (gamma / beta1_bar) .* log(S ./ S_h);
S_inf_opt = fzero(@(S) I_crit(S), [1e-9, S_h]);

S_lf = linspace(S0, S_inf_lf, 900);
S_pre = linspace(S0, S1, 350);
S_bnd = linspace(S1, S_h, 250);
S_post = linspace(S_h, S_inf_opt, 450);
S_opt = [S_pre, S_bnd(2:end), S_post(2:end)];
I_opt = [I_lf(S_pre), K * ones(1, numel(S_bnd)-1), I_crit(S_post(2:end))];

figure('Color','w','Position',[100 100 900 610]);
plot(S_lf, I_lf(S_lf), '--', 'LineWidth', 2.0); hold on;
plot(S_opt, I_opt, 'LineWidth', 2.4);
plot([0, 1.02], [K, K], ':', 'LineWidth', 1.5);
ylim_now = [0, max(1.12 * max(I_lf(S_lf)), 1.25 * K)];
plot([S_h, S_h], ylim_now, ':', 'LineWidth', 1.5);
scatter([S0, S1, S_h, S_inf_opt], [I0, K, K, 0], 36, 'filled');
text(S1 + 0.015, K + 0.008, 'entry');
text(S_h - 0.10, K + 0.008, 'release');
xlabel('Susceptible fraction S');
ylabel('Infectious fraction I');
xlim([0, 1.02]); ylim(ylim_now);
grid on; box on;
legend({'Laissez-faire','Optimal path','Capacity K','S_h = gamma / beta2bar'}, 'Location','northeast');

out = fullfile(fileparts(mfilename('fullpath')), '..', 'figures', 'Figure_1_phase_plane.jpg');
print(gcf, out, '-djpeg', '-r300');
fprintf('Saved %s\n', out);
end
