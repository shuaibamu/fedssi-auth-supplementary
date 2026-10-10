import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from featmap import M, RTF, CICF, FAC
import glob
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt(); tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy')
TIMING = [m[0] for m in M if m[3] in ('s', 'us', 'pkts/s')]; NONTIME = [r for r in RTF if r not in TIMING]
log(f'{len(TIMING)} timing/rate features, {len(NONTIME)} non-timing features')
Xtr = df.iloc[tr][RTF]; rf61 = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=1, random_state=SEED).fit(Xtr, y[tr])
rfnt = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=1, random_state=SEED).fit(Xtr[NONTIME], y[tr])
ind_nt = metrics(y[te], rfnt.predict(df.iloc[te][NONTIME])); log(f'in-domain non-timing model macroF1 {ind_nt["macro_f1"]:.5f}')
rt_max = Xtr.max().to_dict()
def prep(ch):
    X = ch[CICF].astype('float64').replace([np.inf, -np.inf], np.nan)
    for c, r in zip(CICF, RTF): X[c] = X[c].fillna(rt_max[r])
    for c in CICF: X[c] = X[c] * FAC[c]
    X.columns = RTF; return X
rng = np.random.default_rng(SEED); S_X, S_y, S_lab = [], [], []; per = {}
for fp in sorted(glob.glob(f'{ROOT}/data/cic/*.csv')):
    name = os.path.basename(fp).replace('.pcap_ISCX.csv', ''); sc61, scnt, labs = [], [], []
    for ch in pd.read_csv(fp, chunksize=200000, usecols=lambda c: c.strip() in CICF + ['Label'], skipinitialspace=True, encoding='latin-1'):
        ch.columns = [c.strip() for c in ch.columns]; lab = ch['Label'].str.strip().str.replace('\ufffd', '-', regex=False).str.replace('\x96', '-', regex=False).values
        X = prep(ch); sc61.append(rf61.predict_proba(X)[:, 1].astype('float32')); scnt.append(rfnt.predict_proba(X[NONTIME])[:, 1].astype('float32')); labs.append(lab)
        k = rng.random(len(X)) < 0.10; S_X.append(X[k].astype('float32')); S_y.append((lab[k] != 'BENIGN').astype(int)); S_lab.append(lab[k])
    per[name] = dict(s61=np.concatenate(sc61), snt=np.concatenate(scnt), lab=np.concatenate(labs)); log(f'scored {name} ({len(per[name]["lab"])})')
out = dict(auc={}, rebaseline={}, nontiming={})
allsc = np.concatenate([v['s61'] for v in per.values()]); allyb = np.concatenate([(v['lab'] != 'BENIGN').astype(int) for v in per.values()]); allnt = np.concatenate([v['snt'] for v in per.values()])
out['auc']['pooled_61'] = float(roc_auc_score(allyb, allsc)); out['auc']['pooled_nontiming'] = float(roc_auc_score(allyb, allnt))
for n, v in per.items():
    yb = (v['lab'] != 'BENIGN').astype(int)
    if 0 < yb.sum() < len(yb): out['auc'][n] = dict(auc61=float(roc_auc_score(yb, v['s61'])), auc_nontiming=float(roc_auc_score(yb, v['snt'])))
log('AUC ' + str({k: (round(v, 4) if isinstance(v, float) else {a: round(b, 4) for a, b in v.items()}) for k, v in out['auc'].items()}))
# (2) benign-only re-baselining: tau = q-th percentile of benign scores in the FIRST HALF of Monday; evaluate on everything else
mon = per['Monday-WorkingHours']; half = len(mon['lab']) // 2; cal = mon['s61'][:half]
for q in (0.95, 0.99, 0.999):
    tau = float(np.quantile(cal, q)); res = {'tau': tau, 'days': {}}; fp = tot = 0
    for n, v in per.items():
        s = v['s61'][half:] if n.startswith('Monday') else v['s61']; lab = v['lab'][half:] if n.startswith('Monday') else v['lab']
        ben = lab == 'BENIGN'; att = ~ben
        res['days'][n] = dict(benign_n=int(ben.sum()), fpr=float((s[ben] > tau).mean()) if ben.any() else None, attack_n=int(att.sum()), recall=float((s[att] > tau).mean()) if att.any() else None,
                              per_label={l: dict(n=int((lab == l).sum()), recall=float((s[lab == l] > tau).mean())) for l in np.unique(lab) if l != 'BENIGN'})
    out['rebaseline'][str(q)] = res
log('rebaseline q=0.99: ' + str({n: (round(d['fpr'], 4) if d['fpr'] is not None else None, round(d['recall'], 4) if d['recall'] is not None else None) for n, d in out['rebaseline']['0.99']['days'].items()}))
# (3) non-timing-feature model (threshold 0.5) on CIC, per day
for n, v in per.items():
    yb = (v['lab'] != 'BENIGN').astype(int); p = (v['snt'] > 0.5).astype(int)
    out['nontiming'][n] = dict(recall=float(p[yb == 1].mean()) if yb.any() else None, fpr=float(p[yb == 0].mean()) if (yb == 0).any() else None, n=int(len(yb)))
out['nontiming']['in_domain_RT'] = ind_nt
# (4) in-domain CIC control (random 70/30 of a pooled 10% sample) and (5) reverse direction CIC->RT
SX = pd.concat(S_X); Sy = np.concatenate(S_y); idx = rng.permutation(len(SX)); k = int(0.7 * len(idx))
rc = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=1, random_state=SEED).fit(SX.iloc[idx[:k]], Sy[idx[:k]])
dom = metrics(Sy[idx[k:]], rc.predict(SX.iloc[idx[k:]])); out['cic_in_domain_control'] = dict(n_train=k, n_test=len(idx) - k, **dom)
log(f'CIC in-domain control: macroF1 {dom["macro_f1"]:.5f} recall {dom["recall"]:.5f} fpr {dom["fpr"]:.5f}')
Xrt = df.iloc[te][RTF].copy(); Xrt['flow_duration'] = Xrt['flow_duration'] * 1e6      # RT seconds -> CIC microseconds
rev = metrics(y[te], rc.predict(Xrt)); out['reverse_cic_to_rt'] = rev; log(f'reverse CIC->RT: recall {rev["recall"]:.4f} fpr {rev["fpr"]:.4f} macroF1 {rev["macro_f1"]:.4f}')
save(out, 'cic_controls.json'); log('DONE')
