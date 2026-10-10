import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import glob, csv
t0 = time.time()
def log(m): print(f'[{time.time()-t0:7.0f}s] {m}', flush=True)
# (RT-IoT2022 field, CIC-IDS2017 field, direction, unit RT, unit CIC, factor applied to CIC to reach RT unit, definition)
S, US, N, B, PPS = 's', 'us', 'count', 'bytes', 'pkts/s'
M = [
('flow_duration','Flow Duration','bidirectional',S,US,1e-6,'time from first to last packet of the flow'),
('fwd_pkts_tot','Total Fwd Packets','forward',N,N,1,'packets sent initiator->responder'),
('bwd_pkts_tot','Total Backward Packets','backward',N,N,1,'packets sent responder->initiator'),
('fwd_pkts_payload.tot','Total Length of Fwd Packets','forward',B,B,1,'sum of forward payload bytes'),
('bwd_pkts_payload.tot','Total Length of Bwd Packets','backward',B,B,1,'sum of backward payload bytes'),
('fwd_pkts_payload.max','Fwd Packet Length Max','forward',B,B,1,'max forward payload length'),
('fwd_pkts_payload.min','Fwd Packet Length Min','forward',B,B,1,'min forward payload length'),
('fwd_pkts_payload.avg','Fwd Packet Length Mean','forward',B,B,1,'mean forward payload length'),
('fwd_pkts_payload.std','Fwd Packet Length Std','forward',B,B,1,'std. dev. forward payload length'),
('bwd_pkts_payload.max','Bwd Packet Length Max','backward',B,B,1,'max backward payload length'),
('bwd_pkts_payload.min','Bwd Packet Length Min','backward',B,B,1,'min backward payload length'),
('bwd_pkts_payload.avg','Bwd Packet Length Mean','backward',B,B,1,'mean backward payload length'),
('bwd_pkts_payload.std','Bwd Packet Length Std','backward',B,B,1,'std. dev. backward payload length'),
('flow_pkts_per_sec','Flow Packets/s','bidirectional',PPS,PPS,1,'packets per second over the flow'),
('flow_iat.avg','Flow IAT Mean','bidirectional',US,US,1,'mean inter-arrival time, all packets'),
('flow_iat.std','Flow IAT Std','bidirectional',US,US,1,'std. dev. inter-arrival time, all packets'),
('flow_iat.max','Flow IAT Max','bidirectional',US,US,1,'max inter-arrival time, all packets'),
('flow_iat.min','Flow IAT Min','bidirectional',US,US,1,'min inter-arrival time, all packets'),
('fwd_iat.tot','Fwd IAT Total','forward',US,US,1,'sum of forward inter-arrival times'),
('fwd_iat.avg','Fwd IAT Mean','forward',US,US,1,'mean forward inter-arrival time'),
('fwd_iat.std','Fwd IAT Std','forward',US,US,1,'std. dev. forward inter-arrival time'),
('fwd_iat.max','Fwd IAT Max','forward',US,US,1,'max forward inter-arrival time'),
('fwd_iat.min','Fwd IAT Min','forward',US,US,1,'min forward inter-arrival time'),
('bwd_iat.tot','Bwd IAT Total','backward',US,US,1,'sum of backward inter-arrival times'),
('bwd_iat.avg','Bwd IAT Mean','backward',US,US,1,'mean backward inter-arrival time'),
('bwd_iat.std','Bwd IAT Std','backward',US,US,1,'std. dev. backward inter-arrival time'),
('bwd_iat.max','Bwd IAT Max','backward',US,US,1,'max backward inter-arrival time'),
('bwd_iat.min','Bwd IAT Min','backward',US,US,1,'min backward inter-arrival time'),
('fwd_PSH_flag_count','Fwd PSH Flags','forward',N,N,1,'forward packets with PSH set'),
('bwd_PSH_flag_count','Bwd PSH Flags','backward',N,N,1,'backward packets with PSH set'),
('fwd_URG_flag_count','Fwd URG Flags','forward',N,N,1,'forward packets with URG set'),
('bwd_URG_flag_count','Bwd URG Flags','backward',N,N,1,'backward packets with URG set (constant 0 in RT-IoT2022, inert)'),
('fwd_header_size_tot','Fwd Header Length','forward',B,B,1,'sum of forward header bytes'),
('bwd_header_size_tot','Bwd Header Length','backward',B,B,1,'sum of backward header bytes'),
('fwd_pkts_per_sec','Fwd Packets/s','forward',PPS,PPS,1,'forward packets per second'),
('bwd_pkts_per_sec','Bwd Packets/s','backward',PPS,PPS,1,'backward packets per second'),
('flow_pkts_payload.min','Min Packet Length','bidirectional',B,B,1,'min payload length, all packets'),
('flow_pkts_payload.max','Max Packet Length','bidirectional',B,B,1,'max payload length, all packets'),
('flow_pkts_payload.avg','Packet Length Mean','bidirectional',B,B,1,'mean payload length, all packets'),
('flow_pkts_payload.std','Packet Length Std','bidirectional',B,B,1,'std. dev. payload length, all packets'),
('flow_FIN_flag_count','FIN Flag Count','bidirectional',N,N,1,'packets with FIN set'),
('flow_SYN_flag_count','SYN Flag Count','bidirectional',N,N,1,'packets with SYN set'),
('flow_RST_flag_count','RST Flag Count','bidirectional',N,N,1,'packets with RST set'),
('flow_ACK_flag_count','ACK Flag Count','bidirectional',N,N,1,'packets with ACK set'),
('flow_CWR_flag_count','CWE Flag Count','bidirectional',N,N,1,'packets with CWR set'),
('flow_ECE_flag_count','ECE Flag Count','bidirectional',N,N,1,'packets with ECE set'),
('down_up_ratio','Down/Up Ratio','bidirectional','ratio','ratio',1,'backward/forward packet ratio'),
('fwd_subflow_pkts','Subflow Fwd Packets','forward',N,N,1,'average forward packets per subflow'),
('fwd_subflow_bytes','Subflow Fwd Bytes','forward',B,B,1,'average forward bytes per subflow'),
('bwd_subflow_pkts','Subflow Bwd Packets','backward',N,N,1,'average backward packets per subflow'),
('bwd_subflow_bytes','Subflow Bwd Bytes','backward',B,B,1,'average backward bytes per subflow'),
('fwd_init_window_size','Init_Win_bytes_forward','forward',B,B,1,'initial TCP window, forward'),
('bwd_init_window_size','Init_Win_bytes_backward','backward',B,B,1,'initial TCP window, backward'),
('active.avg','Active Mean','bidirectional',US,US,1,'mean active period before idle'),
('active.std','Active Std','bidirectional',US,US,1,'std. dev. active period'),
('active.max','Active Max','bidirectional',US,US,1,'max active period'),
('active.min','Active Min','bidirectional',US,US,1,'min active period'),
('idle.avg','Idle Mean','bidirectional',US,US,1,'mean idle period before active'),
('idle.std','Idle Std','bidirectional',US,US,1,'std. dev. idle period'),
('idle.max','Idle Max','bidirectional',US,US,1,'max idle period'),
('idle.min','Idle Min','bidirectional',US,US,1,'min idle period'),
]
assert len(M) == 61, len(M)
RTF = [m[0] for m in M]; CICF = [m[1] for m in M]; FAC = {m[1]: m[5] for m in M}
df, feat, num, y12, y, const = load_rt()
tr = np.load(f'{RES}/idx_train.npy'); te = np.load(f'{RES}/idx_test.npy')
assert all(c in df.columns for c in RTF)
unmatched_rt = [c for c in num if c not in RTF] + [c for c in CAT]
with open(f'{RES}/table_feature_mapping_61.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['rt_iot2022_field','cic_ids2017_field','direction','unit_rt','unit_cic','factor_applied_to_cic','definition']); w.writerows(M)
from sklearn.ensemble import RandomForestClassifier
Xtr = df.iloc[tr][RTF]; rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=1, random_state=SEED).fit(Xtr, y[tr])
ind = metrics(y[te], rf.predict(df.iloc[te][RTF]))                 # in-domain control with the same 61 features
log(f'in-domain 61-feature control: macroF1 {ind["macro_f1"]:.5f} recall {ind["recall"]:.5f} fpr {ind["fpr"]:.5f}')
rt_max = Xtr.max().to_dict()
def prep(ch, harmonize):
    X = ch[CICF].astype('float64'); infn = int(np.isinf(X.values).sum()); nann = int(np.isnan(X.values).sum())
    X = X.replace([np.inf, -np.inf], np.nan)
    for c, r in zip(CICF, RTF): X[c] = X[c].fillna(rt_max[r] if infn else 0)   # +inf (zero-duration rates) -> RT training max
    X = X.fillna(0)
    if harmonize:
        for c in CICF: X[c] = X[c] * FAC[c]
    X.columns = RTF
    return X, infn, nann
files = sorted(glob.glob(f'{ROOT}/data/cic/*.csv')); out = {}; shift_rows = None
for fp in files:
    name = os.path.basename(fp).replace('.pcap_ISCX.csv', '')
    agg = {v: {} for v in ('naive', 'harmonized')}; labs = {}; infs = 0; nans = 0; n = 0
    for ch in pd.read_csv(fp, chunksize=200000, usecols=lambda c: c.strip() in CICF + ['Label'], skipinitialspace=True, encoding='latin-1'):
        ch.columns = [c.strip() for c in ch.columns]; lab = ch['Label'].str.strip().str.replace('\ufffd', '-', regex=False).str.replace('\x96', '-', regex=False)
        isat = (lab != 'BENIGN').values; n += len(ch)
        for l, c_ in lab.value_counts().items(): labs[l] = labs.get(l, 0) + int(c_)
        for v in ('naive', 'harmonized'):
            X, i_, n_ = prep(ch, v == 'harmonized'); p = rf.predict(X)
            if v == 'naive': infs += i_; nans += n_
            a = agg[v]
            for l in lab.unique():
                mm = (lab == l).values; d = a.setdefault(l, [0, 0]); d[0] += int(mm.sum()); d[1] += int(p[mm].sum())
        if shift_rows is None and name.startswith('Monday'):
            Xh, _, _ = prep(ch, True); shift_rows = Xh[isat == False].median().to_dict()
    res = dict(n=n, labels=labs, nonfinite_cells=dict(inf=infs, nan=nans))
    for v in ('naive', 'harmonized'):
        a = agg[v]; tn = a.get('BENIGN', [0, 0]); ben_n, ben_fl = tn[0], tn[1]
        att_n = sum(x[0] for k, x in a.items() if k != 'BENIGN'); att_fl = sum(x[1] for k, x in a.items() if k != 'BENIGN')
        tp, fn, fp, tn_ = att_fl, att_n - att_fl, ben_fl, ben_n - ben_fl
        prec = tp / (tp + fp) if tp + fp else float('nan'); rec = tp / att_n if att_n else float('nan'); fpr = fp / ben_n if ben_n else float('nan')
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float('nan')
        res[v] = dict(tp=tp, fn=fn, fp=fp, tn=tn_, precision=prec, recall=rec, fpr=fpr, f1=f1, benign_blocked=fp, benign_total=ben_n,
                      per_label={k: dict(n=x[0], flagged=x[1], rate=x[1] / x[0]) for k, x in a.items()})
    ap = att_n / n if n else float('nan')
    res['flag_everything'] = dict(precision=ap, recall=1.0 if att_n else float('nan'), fpr=1.0 if ben_n else float('nan'), f1=2 * ap / (1 + ap) if att_n else float('nan'), benign_blocked=ben_n)
    out[name] = res; save(dict(files=out, in_domain_control=ind, unmatched_rt_fields=unmatched_rt, benign_median_shift_cic_monday=shift_rows), 'cic_transfer.json')
    log(f'{name}: n={n} harmonized: rec={res["harmonized"]["recall"]:.4f} fpr={res["harmonized"]["fpr"]:.4f} | naive: rec={res["naive"]["recall"]:.4f} fpr={res["naive"]["fpr"]:.4f}')
rt_ben_med = df[y == 0][RTF].median().to_dict()
with open(f'{RES}/table_feature_shift_benign_medians.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['rt_field', 'rt_benign_median', 'cic_monday_benign_median_in_rt_units'])
    for r in RTF: w.writerow([r, rt_ben_med[r], shift_rows[r]])
save(dict(files=out, in_domain_control=ind, unmatched_rt_fields=unmatched_rt, benign_median_shift_cic_monday=shift_rows), 'cic_transfer.json'); log('DONE')
