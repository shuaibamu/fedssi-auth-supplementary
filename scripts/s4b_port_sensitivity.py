import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
df, feat, num, y12, y, const = load_rt(); tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy'); X = df[feat]
out = {}
for name, drop in [('all 82 features', []), ('without port numbers (id.orig_p, id.resp_p)', ['id.orig_p', 'id.resp_p']),
                   ('without ports, proto and service', ['id.orig_p', 'id.resp_p', 'proto', 'service'])]:
    f = [c for c in feat if c not in drop]; n_ = [c for c in num if c not in drop]
    import common
    m = common.make_model('RF', n_) if 'proto' not in drop else None
    if m is None:
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=1, random_state=SEED)
        m.fit(X.iloc[tr][f], y[tr]); p = m.predict(X.iloc[te][f])
    else:
        m.fit(X.iloc[tr][f], y[tr]); p = m.predict(X.iloc[te][f])
    r = metrics(y[te], p); out[name] = r; print(f"{name:48s} macroF1={r['macro_f1']:.5f} recall={r['recall']:.5f} FPR={r['fpr']:.5f} FN={r['fn']} FP={r['fp']}")
save(out, 'port_sensitivity.json')
