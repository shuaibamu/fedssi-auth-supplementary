import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import joblib
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.isotonic import IsotonicRegression
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt(); X = df[feat]
tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy')
# (1) out-of-fold scores on the TRAINING split only (test split untouched)
oof = np.zeros(len(tr))
for k, (a, b) in enumerate(StratifiedKFold(5, shuffle=True, random_state=SEED).split(tr, y12[tr])):
    m = make_model('RF', num).fit(X.iloc[tr[a]], y[tr[a]]); oof[b] = m.predict_proba(X.iloc[tr[b]])[:, 1]
    log(f'OOF fold {k}')
grid = np.round(np.arange(0.02, 0.99, 0.01), 2); sweep = []
for t in grid:
    r = metrics(y[tr], (oof > t).astype(int)); r['tau'] = float(t); sweep.append(r)
best = max(sweep, key=lambda r: (round(r['macro_f1'], 6), -abs(r['tau'] - 0.5)))
tau = best['tau']; log(f'selected tau={tau} on training OOF; macroF1={best["macro_f1"]:.5f}')
# (2) untouched test
rf = joblib.load(f'{RES}/rf_binary_fulltrain.joblib'); st = rf.predict_proba(X.iloc[te])[:, 1]
res = {'tau_selected_on_train_oof': tau, 'test_at_0.50': metrics(y[te], (st > 0.5).astype(int)), 'test_at_selected': metrics(y[te], (st > tau).astype(int))}
# (3) calibration of the RF score
def ece(p, yy, nb=10):
    bins = np.linspace(0, 1, nb + 1); e = 0; rel = []
    for i in range(nb):
        m = (p >= bins[i]) & ((p < bins[i + 1]) | (i == nb - 1))
        if m.sum(): e += m.mean() * abs(yy[m].mean() - p[m].mean()); rel.append((float(p[m].mean()), float(yy[m].mean()), int(m.sum())))
    return float(e), rel
iso = IsotonicRegression(out_of_bounds='clip').fit(oof, y[tr])
cal = {}
for nm, p, yy in [('oof_train_raw', oof, y[tr]), ('test_raw', st, y[te]), ('test_isotonic', iso.predict(st), y[te])]:
    e, rel = ece(p, yy); cal[nm] = dict(brier=float(np.mean((p - yy) ** 2)), ece10=e, reliability=rel)
res['calibration'] = cal
# (4) split-seed robustness (5 independent stratified 75/25 splits, RF, tau=0.5)
seeds = {}
for sd in [1, 2, 3, 4, 5]:
    a, b = train_test_split(np.arange(len(df)), test_size=0.25, stratify=y12, random_state=sd)
    m = make_model('RF', num, seed=sd).fit(X.iloc[a], y[a]); r = metrics(y[b], m.predict(X.iloc[b])); seeds[sd] = r
    log(f'seed {sd}: macroF1 {r["macro_f1"]:.5f} recall {r["recall"]:.5f} fpr {r["fpr"]:.5f}')
res['seed_robustness'] = seeds
save(res, 'threshold_calibration_seeds.json'); save(sweep, 'threshold_sweep_oof.json')
np.savez_compressed(f'{RES}/oof_scores_train.npz', oof=oof, y=y[tr], test_score=st, y_test=y[te])
log('DONE')
