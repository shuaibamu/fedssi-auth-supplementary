"""Repeated, sequential (one network at a time) registerDID benchmark on QBFT networks with n validators. Host: see host.json."""
import sys, time, json, statistics, subprocess, os, platform; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from besu_net import Net
from chain_registry import ChainRegistry, K
from web3 import Web3
from eth_account import Account
t0 = time.time()
def log(m): print(f'[{time.time()-t0:6.0f}s] {m}', flush=True)
def cpu_times():
    v = list(map(int, open('/proc/stat').readline().split()[1:])); return sum(v), v[3] + v[4]
def mem_used_mb():
    d = dict((l.split(':')[0], int(l.split()[1])) for l in open('/proc/meminfo')); return (d['MemTotal'] - d['MemAvailable']) / 1024
host = dict(vcpus=os.cpu_count(), mem_total_mb=round(dict((l.split(':')[0], int(l.split()[1])) for l in open('/proc/meminfo'))['MemTotal'] / 1024),
            kernel=platform.release(), java=subprocess.run(['java', '-version'], capture_output=True, text=True).stderr.splitlines()[0], besu='24.12.2', jvm_heap_per_node='256m (-Xmx200m used for n>=7)',
            consensus='QBFT, block period 2 s', gas_price=0, block_gas_limit='0x1fffffffffffff')
save(host, 'host.json'); log(str(host))
LOADS = [10, 50, 100]; REPS = 3; out = {}
for n in (4, 7):
    net = Net(n, period=2, heap='200m' if n >= 7 else '256m'); w3 = net.start(); log(f'n={n} up (block {w3.eth.block_number}, peers {w3.net.peer_count}, mem used {mem_used_mb():.0f} MB)')
    try:
        reg = ChainRegistry(w3); dc = reg.c['DIDRegistry']; cid = w3.eth.chain_id; runs = []
        # read-path latency (eth_call) on this network
        rl = []; fn = dc.functions.resolveDIDs(K('a'), K('b'))
        for _ in range(100): t = time.perf_counter(); fn.call(); rl.append((time.perf_counter() - t) * 1000)
        out[f'n{n}'] = dict(read_resolveDIDs_ms=dict(median=statistics.median(rl), p95=sorted(rl)[94]), runs=[])
        for rep in range(REPS):
            for load in LOADS:
                accts = [Account.create() for _ in range(load)]
                txs = []
                for a in accts:
                    did = K(f'did:bench:{n}:{rep}:{load}:{a.address}'); fnx = dc.functions.registerDID(did, K('doc'))
                    tx = fnx.build_transaction({'from': a.address, 'nonce': 0, 'gas': 120000, 'gasPrice': 0, 'chainId': cid}); txs.append(a.sign_transaction(tx).raw_transaction)
                c0, i0 = cpu_times(); m0 = mem_used_mb(); ts = time.time(); hashes, sent = [], []
                for raw in txs: sent.append(time.time()); hashes.append(w3.eth.send_raw_transaction(raw))
                t_submit = time.time() - ts; conf = {}; deadline = time.time() + 180
                while len(conf) < load and time.time() < deadline:
                    for i, h in enumerate(hashes):
                        if i in conf: continue
                        try: r = w3.eth.get_transaction_receipt(h)
                        except Exception: r = None
                        if r is not None: conf[i] = (time.time(), r.status, r.gasUsed, r.blockNumber)
                    time.sleep(0.05)
                c1, i1 = cpu_times(); lat = [conf[i][0] - sent[i] for i in conf if conf[i][1] == 1]; ok = len(lat); wall = max(conf[i][0] for i in conf) - sent[0] if conf else float('nan')
                rec = dict(n=n, rep=rep + 1, load=load, submitted=load, confirmed=ok, failed=load - ok, submit_wall_s=t_submit, total_wall_s=wall, throughput_tps=ok / wall if wall == wall else 0,
                           latency_median_s=statistics.median(lat) if lat else None, latency_p95_s=sorted(lat)[max(0, int(0.95 * len(lat)) - 1)] if lat else None, latency_max_s=max(lat) if lat else None,
                           blocks_used=len(set(conf[i][3] for i in conf)), gas_per_tx=statistics.mean(conf[i][2] for i in conf) if conf else None,
                           host_cpu_busy_fraction=1 - (i1 - i0) / (c1 - c0), mem_used_mb=m0)
                out[f'n{n}']['runs'].append(rec); save(out, 'bench_live.json')
                log(f"n={n} rep={rep+1} load={load}: {ok}/{load} confirmed, {rec['throughput_tps']:.2f} tx/s, median {rec['latency_median_s']:.1f}s, p95 {rec['latency_p95_s']:.1f}s, CPU busy {rec['host_cpu_busy_fraction']:.2f}")
                time.sleep(6)
    finally:
        net.stop(); time.sleep(5)
log('DONE')
