import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt(); X = df[feat]
tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy')
attacks = [c for c in df['Attack_type'].value_counts().index if c not in NORMAL]
ben_te = te[y[te] == 0]
res = {'lofo': {}, 'ordered_block_70_30': {}, 'within_session_ordered': {}}
# (a) leave-one-attack-family-out, independent benign test set (the 3,127 benign flows of the untouched test split)
for f in attacks:
    keep = tr[y12[tr] != f]; held = np.where(y12 == f)[0]
    m = make_model('RF', num).fit(X.iloc[keep], y[keep])
    ph = m.predict(X.iloc[held]); pbn = m.predict(X.iloc[ben_te])
    comb = metrics(np.r_[np.ones(len(held), int), np.zeros(len(ben_te), int)], np.r_[ph, pbn])
    res['lofo'][f] = dict(n_heldout=int(len(held)), recall_heldout=float(ph.mean()), missed=int((ph == 0).sum()),
                          benign_test_n=int(len(ben_te)), benign_blocked=int(pbn.sum()), fpr_benign=float(pbn.mean()), precision_combined=comb['precision'])
    log(f'LOFO {f}: recall {ph.mean():.4f} ({int(ph.sum())}/{len(held)}), benign blocked {int(pbn.sum())}/{len(ben_te)}')
    save(res, 'harder_validation.json')
# (b) ordered-block hold-out: first 70% of file rows train, last 30% test (attack-only tail)
n = len(df); cut = int(0.7 * n); a, b = np.arange(cut), np.arange(cut, n)
m = make_model('RF', num).fit(X.iloc[a], y[a]); pb = m.predict(X.iloc[b])
per = {}
for c in pd.unique(y12[b]):
    mm = y12[b] == c; per[c] = dict(n=int(mm.sum()), recall=float(pb[mm].mean()), in_train=bool((y12[a] == c).any()))
res['ordered_block_70_30'] = dict(n_train=len(a), n_test=len(b), test_benign=int((y[b] == 0).sum()), test_attack=int((y[b] == 1).sum()),
                                  attack_recall=float(pb[y[b] == 1].mean()), missed=int(((pb == 0) & (y[b] == 1)).sum()), per_class=per)
log(f'ordered-block: attack-only test, recall {res["ordered_block_70_30"]["attack_recall"]:.4f}, test benign={res["ordered_block_70_30"]["test_benign"]}')
# (c) within-session ordered hold-out: within every original class, earlier 75% of rows (file order) train, later 25% test
a, b = [], []
for c in df['Attack_type'].unique():
    ix = np.where(y12 == c)[0]; k = int(round(0.75 * len(ix))); a += list(ix[:k]); b += list(ix[k:])
a, b = np.array(a), np.array(b)
m = make_model('RF', num).fit(X.iloc[a], y[a]); pb = m.predict(X.iloc[b]); r = metrics(y[b], pb)
per = {c: dict(n=int((y12[b] == c).sum()), rate=float(pb[y12[b] == c].mean())) for c in df['Attack_type'].unique()}
res['within_session_ordered'] = dict(n_train=len(a), n_test=len(b), metrics=r, per_class=per)
log(f'within-session ordered: macroF1 {r["macro_f1"]:.5f} recall {r["recall"]:.5f} fpr {r["fpr"]:.5f}')
save(res, 'harder_validation.json'); log('DONE')
