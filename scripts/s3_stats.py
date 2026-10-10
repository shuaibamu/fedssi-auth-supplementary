import sys; SUF = sys.argv[1] if len(sys.argv) > 1 else '_full'; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from scipy import stats
cv = load(f'cv_fold_scores{SUF}.json'); z = np.load(f'{RES}/test_scores{SUF}.npz')
y = z['y']; n_train, n_val = cv['RF'][0]['n_train'], cv['RF'][0]['n_val']
out = {'cv_summary': {}, 'pairwise': {}}
tcrit = stats.t.ppf(0.975, 4)
for m in MODEL_NAMES:
    v = np.array([f['macro_f1'] for f in cv[m]]); a = np.array([f['f1_attack'] for f in cv[m]])
    out['cv_summary'][m] = dict(folds_macro_f1=v.tolist(), mean=v.mean(), sd=v.std(ddof=1), ci95_half=tcrit * v.std(ddof=1) / np.sqrt(5),
                                folds_f1_attack=a.tolist(), mean_f1_attack=a.mean(), ci95_half_f1_attack=tcrit * a.std(ddof=1) / np.sqrt(5))
rf = np.array([f['macro_f1'] for f in cv['RF']]); prf = z['pred_RF']
raw = []
for m in MODEL_NAMES:
    if m == 'RF': continue
    pm = z[f'pred_{m}']
    err_rf, err_m = prf != y, pm != y
    b = int((err_m & ~err_rf).sum())   # other model wrong, RF right
    c = int((err_rf & ~err_m).sum())   # RF wrong, other model right
    p_exact = stats.binomtest(min(b, c), b + c, 0.5).pvalue if b + c > 0 else 1.0
    chi = (abs(b - c) - 1) ** 2 / (b + c) if b + c > 0 else 0.0
    p_chi = 1 - stats.chi2.cdf(chi, 1) if b + c > 0 else 1.0
    d = rf - np.array([f['macro_f1'] for f in cv[m]])
    t_naive = d.mean() / (d.std(ddof=1) / np.sqrt(5)) if d.std(ddof=1) > 0 else np.inf
    p_naive = 2 * (1 - stats.t.cdf(abs(t_naive), 4))
    corr = (1 / 5 + n_val / n_train)                                   # Nadeau-Bengio corrected resampled t-test
    t_corr = d.mean() / np.sqrt(corr * d.var(ddof=1)) if d.var(ddof=1) > 0 else np.inf
    p_corr = 2 * (1 - stats.t.cdf(abs(t_corr), 4))
    out['pairwise'][m] = dict(rf_wrong_other_right=c, other_wrong_rf_right=b, n_test_errors_rf=int(err_rf.sum()), n_test_errors_other=int(err_m.sum()),
                              mcnemar_exact_p=p_exact, mcnemar_chi2=chi, mcnemar_chi2_p=p_chi, cv_mean_diff=d.mean(),
                              t_naive=t_naive, p_naive=p_naive, t_corrected=t_corr, p_corrected=p_corr)
    raw.append((m, p_exact, p_naive, p_corr))
def holm(ps):
    o = np.argsort(ps); adj = np.empty(len(ps)); run = 0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1, run)
    return adj
for j, key in [(1, 'mcnemar_exact_holm'), (2, 'p_naive_holm'), (3, 'p_corrected_holm')]:
    adj = holm([r[j] for r in raw])
    for (m, *_), a in zip(raw, adj): out['pairwise'][m][key] = float(a)
save(out, f'stats_tests{SUF}.json')
for m in MODEL_NAMES:
    s = out['cv_summary'][m]; print(f"{m:8s} CV macro-F1 {s['mean']:.4f} +/- {s['ci95_half']:.4f}")
for m, d in out['pairwise'].items(): print(m, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in d.items()})
