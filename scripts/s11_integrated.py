"""Integrated gateway test on the live contracts: credential state x traffic class, post-issuance compromise, latency breakdown."""
import sys, time, json, statistics, random; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import joblib, protocol as P
from besu_net import Net
from chain_registry import ChainRegistry
t0 = time.time()
def log(m): print(f'[{time.time()-t0:6.0f}s] {m}', flush=True)
df, feat, num, y12, y, const = load_rt(); te = np.load(f'{RES}/idx_test.npy'); X = df[feat]
rf = joblib.load(f'{RES}/rf_binary_fulltrain.joblib'); tau = 0.50  # operating point fixed before any test-split evaluation (library default); see Section 4.5
scorer = lambda flows: rf.predict_proba(flows)[:, 1]
rng = random.Random(SEED); NP = np.random.default_rng(SEED)
ben_pool = te[y[te] == 0]; att_idx = {c: te[y12[te] == c] for c in pd.unique(y12[te]) if c not in NORMAL}; fams = list(att_idx)
def flows_benign(k=3): return X.iloc[NP.choice(ben_pool, k, replace=False)]
def flows_attack(k=3): f = rng.choice(fams); return X.iloc[NP.choice(att_idx[f], k, replace=False)], f
net = Net(1, period=1); w3 = net.start(); log('chain up')
try:
    reg = ChainRegistry(w3); docs = P.DocStore(); NOW = int(time.time())
    reg.register_domain('D_R', 'adminR'); reg.register_domain('D_I', 'adminI')
    A = P.Issuer('did:ex:issuerA', 'D_I', reg, docs, admin='0xissuerA'); Bz = P.Issuer('did:ex:issuerB', 'D_I', reg, docs, admin='0xissuerB')
    reg.create_list('list-A', '0xissuerA'); reg.create_list('list-B', '0xissuerB'); reg.flush()
    reg.add_assertion('D_R', 'D_I', A.did, P.SCHEMA_HASH, NOW + 86400, 'adminR', 0)           # issuer A trusted by verifier domain, B is not
    base = dict(schema=P.SCHEMA, deviceClass='air-quality', maxBitrate='1kbps', validUntil=NOW + 86400, listId='list-A', manufacturer='Helsinki Sensors Oy', serial='AQ-0', postcode='00100')
    pools = {k: [] for k in ('valid', 'revoked', 'expired', 'untrusted_issuer', 'stolen_credential')}
    for i in range(8): h = P.Holder(f'did:ex:v{i}', reg, docs, admin=f'0xh{i}'); h.request_credential(A, base); pools['valid'].append(h)
    for i in range(4):
        h = P.Holder(f'did:ex:r{i}', reg, docs, admin=f'0xr{i}'); h.request_credential(A, base); pools['revoked'].append(h)
    reg.flush()
    for h in pools['revoked']: reg.revoke_index('list-A', h.vc['attrs']['revIdx'], '0xissuerA')
    for i in range(4): h = P.Holder(f'did:ex:e{i}', reg, docs, admin=f'0xe{i}'); h.request_credential(A, dict(base, validUntil=NOW - 5)); pools['expired'].append(h)
    for i in range(4): h = P.Holder(f'did:ex:u{i}', reg, docs, admin=f'0xu{i}'); h.request_credential(Bz, dict(base, listId='list-B')); pools['untrusted_issuer'].append(h)
    for i in range(4): h = P.Holder(f'did:ex:s{i}', reg, docs, admin=f'0xs{i}'); pools['stolen_credential'].append(h)      # attacker-registered DIDs, no credential of their own
    reg.flush(); log('setup done')
    gw = P.Gateway('gw-1', 'D_R', reg, docs, scorer=scorer, tau=tau, window=3)
    N = 40; cells = {}; chid = b'tls-exporter-itest'
    for cred in pools:
        for traffic in ('benign', 'malicious'):
            outc = {}; 
            for t in range(N):
                h = rng.choice(pools[cred]); fl, fam = (flows_benign(), None) if traffic == 'benign' else flows_attack()
                c = gw.challenge(NOW)
                if cred == 'stolen_credential': victim = rng.choice(pools['valid']); vp = h.present(c, 'read:air', chid, vc=victim.vc)
                else: vp = h.present(c, 'read:air', chid)
                tok, why, T = gw.authenticate(vp, c['sid'], chid, 'read:air', flows=fl, now=NOW)
                outc[why] = outc.get(why, 0) + 1
            cells[f'{cred}|{traffic}'] = outc; log(f'{cred:18s} x {traffic:9s}: {outc}')
    save(dict(tau=tau, trials_per_cell=N, window_flows=3, cells=cells), 'integrated_matrix.json')
    # --- post-issuance compromise (T3): valid credential, benign window at admission, attack flows afterwards
    comp = []; 
    for t in range(100):
        h = rng.choice(pools['valid']); c = gw.challenge(NOW); vp = h.present(c, 'read:air', chid)
        tok, why, T = gw.authenticate(vp, c['sid'], chid, 'read:air', flows=flows_benign(), now=NOW)
        if tok is None: comp.append(dict(admitted=False, reason=why)); continue
        n_fed, dur, blocked = 0, 0.0, False
        for step in range(10):
            fl, fam = flows_attack(1); n_fed += 1; dur += float(fl['flow_duration'].iloc[0]); st, sc = gw.monitor(c['sid'], fl)
            if st == 'revoked': blocked = True; break
        ok_rp, rw = P.rp_verify_token(tok, gw.pk, 'D_R', 'read:air', NOW + 1, revoked_sids={c['sid']} if gw.sessions[c['sid']]['revoked'] else ())
        comp.append(dict(admitted=True, blocked=blocked, flows_until_block=n_fed, observed_flow_seconds=dur, rp_accepts_after_revocation=ok_rp))
    adm = [r for r in comp if r['admitted']]
    summ = dict(sessions=len(comp), admitted=len(adm), not_admitted=len(comp) - len(adm), blocked=sum(r['blocked'] for r in adm),
                flows_until_block_median=statistics.median(r['flows_until_block'] for r in adm), flows_until_block_max=max(r['flows_until_block'] for r in adm),
                observed_seconds_median=statistics.median(r['observed_flow_seconds'] for r in adm), observed_seconds_p95=sorted(r['observed_flow_seconds'] for r in adm)[int(0.95 * len(adm)) - 1],
                rp_accepts_after_revocation=sum(r['rp_accepts_after_revocation'] for r in adm))
    save(summ, 'integrated_postissuance.json'); log('post-issuance: ' + json.dumps(summ))
    # --- latency breakdown and sequential throughput (valid sessions, benign window, live eth_call reads)
    stages = {}; tp = []; gen = []; tot = []
    for t in range(200):
        h = rng.choice(pools['valid']); c = gw.challenge(NOW); fl = flows_benign()
        t1 = time.perf_counter(); vp = h.present(c, 'read:air', chid); gen.append((time.perf_counter() - t1) * 1000)
        t2 = time.perf_counter(); tok, why, T = gw.authenticate(vp, c['sid'], chid, 'read:air', flows=fl, now=NOW); el = time.perf_counter() - t2
        if tok:
            tot.append(el * 1000)
            for k, v in T.items(): stages.setdefault(k, []).append(v)
    lat = dict(n=len(tot), holder_present_ms_median=statistics.median(gen), gateway_total_ms_median=statistics.median(tot), gateway_total_ms_p95=sorted(tot)[int(0.95 * len(tot)) - 1],
               sessions_per_second_single_thread=1000 / statistics.mean(tot), stages_ms_median={k: statistics.median(v) for k, v in stages.items()})
    save(lat, 'integrated_latency.json'); log('latency: ' + json.dumps(lat))
finally:
    net.stop()
log('DONE')
