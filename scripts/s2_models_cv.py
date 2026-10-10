import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import joblib
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt()
X = df[feat]
tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy'); sub = np.load(f'{RES}/idx_sub30k.npy')
Xs, ys, y12s = X.iloc[sub], y[sub], y12[sub]
Xte, yte = X.iloc[te], y[te]
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
cv = {}
for name in MODEL_NAMES:
    folds = []
    for k, (a, b) in enumerate(skf.split(Xs, y12s)):          # stratified on the 12 original labels, target = binary
        m = make_model(name, num).fit(Xs.iloc[a], ys[a])       # preprocessing fitted inside the training fold
        mt = metrics(ys[b], m.predict(Xs.iloc[b])); mt['n_train'] = len(a); mt['n_val'] = len(b); folds.append(mt)
    cv[name] = folds
    log(f'CV {name}: macroF1 folds ' + ' '.join(f"{f['macro_f1']:.4f}" for f in folds))
    save(cv, 'cv_fold_scores.json')
test, sc, pr, tim = {}, {}, {}, {}
for name in MODEL_NAMES:
    t1 = time.time(); m = make_model(name, num).fit(Xs, ys); fit_t = time.time() - t1
    s = scores(m, Xte); p = m.predict(Xte).astype(int)
    r = metrics(yte, p); r['roc_auc'] = roc_auc_score(yte, s); r['pr_auc'] = average_precision_score(yte, s); r['fit_seconds'] = fit_t
    probe = Xte.iloc[:5000]; ts = []
    for _ in range(3):
        t2 = time.time(); m.predict(probe); ts.append(time.time() - t2)
    r['predict_ms_per_1000_flows'] = 1000 * float(np.median(ts)) / 5.0
    test[name] = r; sc[name] = s; pr[name] = p
    log(f'TEST {name}: ' + ' '.join(f'{k}={r[k]:.4f}' for k in ['precision','recall','f1_attack','macro_f1','fpr','roc_auc']) + f" fit={fit_t:.0f}s")
    save(test, 'test_results_same30k.json')
np.savez_compressed(f'{RES}/test_scores_same30k.npz', y=yte, y12=y12[te], **{f'score_{k}': v for k, v in sc.items()}, **{f'pred_{k}': v for k, v in pr.items()})
# deployed RF: full training split
t1 = time.time(); rf = make_model('RF', num).fit(X.iloc[tr], y[tr]); fit_t = time.time() - t1
s = scores(rf, Xte); p = rf.predict(Xte).astype(int)
r = metrics(yte, p); r['roc_auc'] = roc_auc_score(yte, s); r['pr_auc'] = average_precision_score(yte, s); r['fit_seconds'] = fit_t
save(r, 'test_results_rf_fulltrain.json'); log('RF full-train: ' + str({k: round(v, 5) for k, v in r.items() if isinstance(v, float)}))
np.savez_compressed(f'{RES}/test_scores_rf_full.npz', y=yte, score=s, pred=p, y12=y12[te])
names = list(rf.named_steps['pre'].get_feature_names_out())
imp = rf.named_steps['clf'].feature_importances_
save(dict(zip(names, imp)), 'rf_feature_importance.json')
joblib.dump(rf, f'{RES}/rf_binary_fulltrain.joblib', compress=3)
log('DONE')
