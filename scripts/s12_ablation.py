import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from sklearn.ensemble import RandomForestClassifier
df, feat, num, y12, y, const = load_rt(); tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy'); X = df[feat]
TEMPORAL = [c for c in num if c == 'flow_duration' or 'iat' in c or c.startswith('active.') or c.startswith('idle.')]
def fit_eval(drop, n_est=100, name=''):
    f = [c for c in feat if c not in drop]; n_ = [c for c in num if c not in drop]; cat = [c for c in CAT if c not in drop]
    from sklearn.compose import ColumnTransformer; from sklearn.preprocessing import OneHotEncoder; from sklearn.pipeline import Pipeline
    pre = ColumnTransformer([('num', 'passthrough', n_)] + ([('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat)] if cat else []))
    m = Pipeline([('pre', pre), ('clf', RandomForestClassifier(n_estimators=n_est, class_weight='balanced', n_jobs=1, random_state=SEED))]).fit(X.iloc[tr][f], y[tr])
    r = metrics(y[te], m.predict(X.iloc[te][f])); r['n_features'] = len(f); print(f"{name:55s} macroF1={r['macro_f1']:.5f} F1att={r['f1_attack']:.5f} recall={r['recall']:.5f} fpr={r['fpr']:.5f}"); return r
out = {'Full model (RF, all 82 features, 100 trees)': fit_eval([], name='full'),
       '- categorical features (proto, service)': fit_eval(CAT, name='-cat'),
       f'- temporal features ({len(TEMPORAL)}: duration, IAT, active, idle)': fit_eval(TEMPORAL, name='-temporal'),
       '- port numbers (id.orig_p, id.resp_p)': fit_eval(['id.orig_p', 'id.resp_p'], name='-ports'),
       'Reduced ensemble (50 trees)': fit_eval([], 50, name='50 trees')}
# baseline under an explicit assumption: with no behavioural gate every flow that carries a valid credential is admitted
yt = y[te]; allow = np.zeros_like(yt); b = metrics(yt, allow); b['assumption'] = 'every flow presents a valid credential and is admitted when no behavioural gate exists'
out['No behavioural gate (baseline under the stated assumption)'] = b; print('no-gate', {k: round(v, 5) if isinstance(v, float) else v for k, v in b.items() if k != 'assumption'})
save(out, 'ablation.json'); save(dict(temporal_features=TEMPORAL), 'ablation_temporal_set.json')
