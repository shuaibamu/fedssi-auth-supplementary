import os
"""Data-driven figures 4,5,6,8,9,10,11,12,13 (regenerated from the corrected results)."""
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from common import *
from scipy.cluster.hierarchy import linkage, leaves_list
from sklearn.metrics import roc_curve
FIG = os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures'); plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25})
NAMES = {'LR': 'Logistic Regression', 'DT': 'Decision Tree', 'kNN': 'k-NN', 'SVM-RBF': 'SVM (RBF)', 'GB': 'Gradient Boosting', 'RF': 'Random Forest'}
COL = {'LR': '#7f7f7f', 'DT': '#2ca02c', 'kNN': '#9467bd', 'SVM-RBF': '#8c564b', 'GB': '#ff7f0e', 'RF': '#d62728'}
T = load('test_results_full.json'); S = load('stats_tests_full.json'); TC = load('threshold_calibration_seeds.json'); sweep = load('threshold_sweep_oof.json'); M = load('multiclass_and_family_results.json')
def fig4():
    fig, ax = plt.subplots(figsize=(8.8, 4.6)); ks = list(NAMES); v = [T[k]['predict_ms_per_1000_flows'] for k in ks]
    b = ax.bar([NAMES[k] for k in ks], v, color=[COL[k] for k in ks]); ax.set_yscale('log'); ax.set_ylabel('Inference time (ms per 1,000 flows, log scale)')
    for r, x in zip(b, v): ax.text(r.get_x() + r.get_width() / 2, x * 1.12, f'{x:.1f}', ha='center', fontsize=9)
    ax.set_title('Per-classifier inference latency (single core, preprocessing included)'); plt.xticks(rotation=15); fig.tight_layout(); fig.savefig(f'{FIG}/fig4.png', dpi=200); plt.close()
def fig5():
    imp = load('rf_feature_importance.json'); it = sorted(imp.items(), key=lambda kv: -kv[1])[:12]
    names = [k.replace('num__', '').replace('cat__', '') for k, _ in it][::-1]; vals = [v for _, v in it][::-1]
    fig, ax = plt.subplots(figsize=(8.8, 5.4)); ax.barh(names, vals, color='#d62728'); ax.set_xlabel('Gini importance (Random Forest, binary task, full training split)'); ax.set_title('Top-12 Random-Forest feature importances')
    fig.tight_layout(); fig.savefig(f'{FIG}/fig5.png', dpi=200); plt.close()
def fig6():
    df, feat, num, y12, y, const = load_rt(); tr = np.load(f'{RES}/idx_train.npy'); C = df.iloc[tr][num].corr().abs().fillna(0).values
    D = 1 - C; iu = np.triu_indices(len(num), 1); Z = linkage(D[iu], 'average'); o = leaves_list(Z); Cm = C[np.ix_(o, o)]
    fig, ax = plt.subplots(figsize=(9.2, 8.4)); im = ax.imshow(Cm, cmap='coolwarm', vmin=0, vmax=1); ax.set_xticks(range(len(o))); ax.set_yticks(range(len(o)))
    lab = [num[i] for i in o]; ax.set_xticklabels(lab, rotation=90, fontsize=4.5); ax.set_yticklabels(lab, fontsize=4.5); ax.grid(False)
    cb = fig.colorbar(im, fraction=.04); cb.set_label('|Pearson correlation|'); ax.set_title(f'Feature redundancy of RT-IoT2022 ({len(num)} numeric features, absolute Pearson correlation,\nhierarchically clustered; training split)', fontsize=10)
    fig.tight_layout(); fig.savefig(f'{FIG}/fig6.png', dpi=190); plt.close()
def fig8():
    z = np.load(f'{RES}/test_scores_full.npz'); y = z['y']; oo = np.load(f'{RES}/oof_scores_train.npz'); tau = TC['tau_selected_on_train_oof']
    fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.8))
    a = ax[0, 0]
    for k in NAMES:
        fpr, tpr, _ = roc_curve(y, z[f'score_{k}']); a.plot(np.maximum(fpr, 1e-5), tpr, color=COL[k], lw=1.6, label=f"{NAMES[k]} (AUC {T[k]['roc_auc']:.4f})")
    a.set_xscale('log'); a.set_xlim(1e-4, 1); a.set_ylim(0.9, 1.003); a.set_xlabel('False-positive rate (log scale)'); a.set_ylabel('True-positive rate'); a.legend(fontsize=7.5, loc='lower right'); a.set_title('(a) ROC curves, held-out test split', fontsize=10)
    b = ax[0, 1]; tt = [r['tau'] for r in sweep]
    for key, lab, c in [('precision', 'Precision (attack)', '#1f77b4'), ('recall', 'Recall (attack)', '#2ca02c'), ('fpr', 'False-rejection rate (benign)', '#d62728'), ('macro_f1', 'Macro-F1', 'k')]: b.plot(tt, [r[key] for r in sweep], label=lab, color=c, lw=1.6)
    b.axvline(tau, color='purple', ls='--', lw=1); b.text(tau + .01, .35, f'selected τ = {tau:.2f}\n(training out-of-fold)', color='purple', fontsize=8); b.set_ylim(-0.02, 1.02); b.set_xlabel('Threshold τ (flag if score > τ)'); b.set_title('(b) Threshold trade-off, training out-of-fold scores', fontsize=10); b.legend(fontsize=7.5, loc='center left')
    c = ax[1, 0]; rel = TC['calibration']['test_raw']['reliability']; c.plot([0, 1], [0, 1], 'k--', lw=1); c.plot([r[0] for r in rel], [r[1] for r in rel], 'o-', color='#d62728', label='Random Forest score (test)')
    c.set_xlabel('Mean predicted attack probability'); c.set_ylabel('Observed attack fraction'); c.set_title(f"(c) Reliability (10 bins): Brier {TC['calibration']['test_raw']['brier']:.4f}, ECE {TC['calibration']['test_raw']['ece10']:.4f}", fontsize=10); c.legend(fontsize=8)
    d = ax[1, 1]; s = z['score_RF']; bins = np.linspace(0, 1, 41); d.hist(s[y == 0], bins=bins, alpha=.7, color='#1f77b4', label='Authorized (benign)'); d.hist(s[y == 1], bins=bins, alpha=.7, color='#d62728', label='Unauthorized (attack)')
    d.set_yscale('log'); d.axvline(tau, color='purple', ls='--', lw=1); d.set_xlabel('Random Forest attack score'); d.set_ylabel('Flows (log scale)'); d.set_title('(d) Score distribution, held-out test split', fontsize=10); d.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f'{FIG}/fig8.png', dpi=170); plt.close()
def fig9():
    ks = list(NAMES); cv = S['cv_summary']; fig, ax = plt.subplots(figsize=(9.6, 4.8)); x = np.arange(len(ks))
    ax.bar(x, [cv[k]['mean'] for k in ks], yerr=[cv[k]['ci95_half'] for k in ks], capsize=4, color=[COL[k] for k in ks], alpha=.85, label='5-fold CV macro-F1 (mean, approx. 95% CI)')
    ax.scatter(x, [T[k]['macro_f1'] for k in ks], marker='D', color='k', zorder=5, label='Held-out test macro-F1')
    ax.set_xticks(x); ax.set_xticklabels([NAMES[k] for k in ks], rotation=15); ax.set_ylim(0.92, 1.0); ax.set_ylabel('Macro-F1 (two binary classes)')
    ax.set_title('Binary gateway task: same full training split for every model\n(CV intervals are approximate: folds overlap and are not independent)', fontsize=10); ax.legend(fontsize=8, loc='lower right'); fig.tight_layout(); fig.savefig(f'{FIG}/fig9.png', dpi=200); plt.close()
def fig10():
    labs = M['labels']; pc = M['per_class_multiclass']; fam = M['binary_gateway_by_class']; fig, ax = plt.subplots(2, 1, figsize=(11, 8.6)); x = np.arange(len(labs)); w = .27
    for i, (k, c) in enumerate([('precision', '#1f77b4'), ('recall', '#2ca02c'), ('f1', '#ff7f0e')]): ax[0].bar(x + (i - 1) * w, [pc[l][k] for l in labs], w, label=k.capitalize() if k != 'f1' else 'F1', color=c)
    ax[0].set_xticks(x); ax[0].set_xticklabels([f'{l}\n(n={pc[l]["support"]})' for l in labs], rotation=40, ha='right', fontsize=7); ax[0].set_ylim(0.75, 1.01); ax[0].set_title('(a) Separately trained 12-class Random Forest: per-class precision, recall and F1 (test split)', fontsize=10); ax[0].legend(fontsize=8, ncol=3, loc='lower left')
    rate = [fam[l]['rate'] for l in labs]; colr = ['#d62728' if fam[l]['kind'] == 'attack' else '#1f77b4' for l in labs]
    ax[1].bar(x, rate, color=colr); ax[1].set_xticks(x); ax[1].set_xticklabels([f'{l}\n({fam[l]["flagged"]}/{fam[l]["n"]})' for l in labs], rotation=40, ha='right', fontsize=7)
    ax[1].set_ylabel('Fraction flagged'); ax[1].set_title('(b) Binary gateway: fraction flagged per original class (red: attack recall; blue: benign false-rejection rate)', fontsize=10); ax[1].set_yscale('symlog', linthresh=0.01)
    fig.tight_layout(); fig.savefig(f'{FIG}/fig10.png', dpi=170); plt.close()
def fig11():
    cmb = np.array(M['cm_binary_gateway']); cm12 = np.array(M['cm12']); labs = M['labels']; fig, ax = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [1, 1.7]})
    ax[0].imshow(np.log10(cmb + 1), cmap='Blues'); ax[0].grid(False)
    for i in range(2):
        for j in range(2): ax[0].text(j, i, f'{cmb[i, j]:,}', ha='center', va='center', fontsize=12, color='white' if cmb[i, j] > 1000 else 'black')
    ax[0].set_xticks([0, 1]); ax[0].set_yticks([0, 1]); ax[0].set_xticklabels(['Admitted\n(pred. Authorized)', 'Blocked\n(pred. Unauthorized)']); ax[0].set_yticklabels(['Authorized\n(benign)', 'Unauthorized\n(attack)']); ax[0].set_title('(a) Binary gateway (RF, τ = 0.50)', fontsize=10)
    ax[1].imshow(np.log10(cm12 + 1), cmap='Blues'); ax[1].grid(False); ax[1].set_xticks(range(12)); ax[1].set_yticks(range(12)); ax[1].set_xticklabels(labs, rotation=60, ha='right', fontsize=6.5); ax[1].set_yticklabels(labs, fontsize=6.5)
    for i in range(12):
        for j in range(12):
            if cm12[i, j]: ax[1].text(j, i, f'{cm12[i, j]}', ha='center', va='center', fontsize=6, color='white' if cm12[i, j] > 300 else 'black')
    ax[1].set_title('(b) Separately trained 12-class model (counts)', fontsize=10); fig.tight_layout(); fig.savefig(f'{FIG}/fig11.png', dpi=170); plt.close()
def fig12():
    A = load('ablation.json'); keys = list(A); fig, ax = plt.subplots(figsize=(11, 4.8)); x = np.arange(len(keys)); w = .38
    b1 = ax.bar(x - w / 2, [A[k]['macro_f1'] for k in keys], w, label='Macro-F1 (two classes)', color='#1f77b4'); b2 = ax.bar(x + w / 2, [A[k]['f1_attack'] for k in keys], w, label='F1, Unauthorized (positive class)', color='#ff7f0e')
    b1[-1].set_hatch('//'); b2[-1].set_hatch('//')
    ax.set_xticks(x); ax.set_xticklabels([k.replace(' (', '\n(').replace('- ', '− ') for k in keys], rotation=18, ha='right', fontsize=7.5); ax.set_ylim(0, 1.05); ax.set_ylabel('Score'); ax.legend(fontsize=8, loc='center right')
    ax.set_title('Ablation on the held-out test split; hatched bars: baseline under the explicit assumption that every flow carries a valid credential', fontsize=9); fig.tight_layout(); fig.savefig(f'{FIG}/fig12.png', dpi=200); plt.close()
def fig13():
    B = load('bench_live.json'); fig, ax = plt.subplots(1, 3, figsize=(15, 4.7)); cols = {'n4': '#1f77b4', 'n7': '#d62728'}
    for key, c in cols.items():
        if key not in B: continue
        runs = B[key]['runs']; loads = sorted(set(r['load'] for r in runs))
        for a, field, lab in [(ax[0], 'throughput_tps', 'Throughput (confirmed tx/s)'), (ax[1], 'latency_median_s', 'Median confirmation latency (s)'), (ax[2], 'host_cpu_busy_fraction', 'Host CPU busy fraction (1 vCPU)')]:
            m = [np.mean([r[field] for r in runs if r['load'] == L]) for L in loads]; s = [np.std([r[field] for r in runs if r['load'] == L], ddof=1) if sum(r['load'] == L for r in runs) > 1 else 0 for L in loads]
            a.errorbar(loads, m, yerr=s, marker='o', capsize=3, color=c, label=f"{key[1:]} validators"); a.scatter([r['load'] for r in runs], [r[field] for r in runs], color=c, alpha=.3, s=14)
            a.set_xlabel('Concurrently enrolling devices'); a.set_ylabel(lab); a.set_xscale('log'); a.set_xticks(loads); a.set_xticklabels(loads)
    ax[0].legend(fontsize=8); ax[1].set_title('Measured, registerDID, one network at a time (mean ± s.d. of 3 runs; dots: runs)', fontsize=9); fig.tight_layout(); fig.savefig(f'{FIG}/fig13.png', dpi=170); plt.close()
if __name__ == '__main__':
    which = sys.argv[1:] or ['4', '5', '6', '8', '9', '10', '11', '12', '13']
    for w in which:
        try: globals()[f'fig{w}'](); print('fig', w, 'ok')
        except Exception as e: print('fig', w, 'FAILED', repr(e))
