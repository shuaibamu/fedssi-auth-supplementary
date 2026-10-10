import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import joblib
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt(); X = df[feat]
tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy')
labels = list(df['Attack_type'].value_counts().index)
pre_rf = make_model('RF', num).fit(X.iloc[tr], y12[tr]); p12 = pre_rf.predict(X.iloc[te])     # separately trained 12-class model
P, R, F, S = precision_recall_fscore_support(y12[te], p12, labels=labels, zero_division=0)
per_class = {c: dict(precision=float(P[i]), recall=float(R[i]), f1=float(F[i]), support=int(S[i])) for i, c in enumerate(labels)}
cm12 = confusion_matrix(y12[te], p12, labels=labels)
macro12 = float(F.mean())
# multiclass predictions viewed through the binary gate: blocked iff predicted class is an attack class
blocked_mc = (~pd.Series(p12).isin(NORMAL)).astype(int).values
binary_view_of_mc = metrics(y[te], blocked_mc)
# binary gateway (RF binary trained on the same split)
rfb = joblib.load(f'{RES}/rf_binary_fulltrain.joblib'); pb = rfb.predict(X.iloc[te]).astype(int)
fam = {}
for c in labels:
    m = (y12[te] == c); fam[c] = dict(n=int(m.sum()), flagged=int(pb[m].sum()), kind='normal' if c in NORMAL else 'attack',
                                      rate=float(pb[m].mean()))     # attack: recall ; normal: false-rejection rate
cmb = confusion_matrix(y[te], pb, labels=[0, 1])
ssh = (y12[te] == 'Metasploit_Brute_Force_SSH')
res = dict(labels=labels, per_class_multiclass=per_class, macro_f1_12class=macro12, cm12=cm12.tolist(),
           binary_view_of_multiclass=binary_view_of_mc, binary_gateway_by_class=fam, cm_binary_gateway=cmb.tolist(),
           ssh=dict(n=int(ssh.sum()), multiclass_predictions={k: int(v) for k, v in pd.Series(p12[ssh]).value_counts().items()},
                    multiclass_still_blocked=int(blocked_mc[ssh].sum()), binary_gateway_blocked=int(pb[ssh].sum())))
save(res, 'multiclass_and_family_results.json')
log(f'12-class macro-F1 {macro12:.4f}; SSH F1 {per_class["Metasploit_Brute_Force_SSH"]["f1"]:.4f}; SSH preds {res["ssh"]}')
log('binary gate by class: ' + str({c: (v["flagged"], v["n"]) for c, v in fam.items()}))
