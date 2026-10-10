"""Start/stop an n-validator Hyperledger Besu QBFT network on localhost (one network at a time)."""
import subprocess, time, json, os, shutil, signal, sys, glob
from web3 import Web3
BESU = os.environ.get('BESU_BIN', os.path.expanduser('~/besu-24.12.2/bin/besu'))
def _cfg(n, chain_id, period):
    return {"genesis": {"config": {"chainId": chain_id, "berlinBlock": 0, "qbft": {"blockperiodseconds": period, "epochlength": 30000, "requesttimeoutseconds": 4}},
            "nonce": "0x0", "timestamp": "0x58ee40ba", "gasLimit": "0x1fffffffffffff", "difficulty": "0x1", "coinbase": "0x0000000000000000000000000000000000000000", "alloc": {}},
            "blockchain": {"nodes": {"generate": True, "count": n}}}
class Net:
    def __init__(self, n, base=os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'netdata'), chain_id=1337, period=2, rpc_base=8545, p2p_base=30303, heap='256m'):
        self.n, self.dir, self.procs, self.period, self.rpc_base, self.p2p_base, self.heap, self.chain_id = n, f'{base}/n{n}', [], period, rpc_base, p2p_base, heap, chain_id
        self.rpc = f'http://127.0.0.1:{rpc_base}'
    def start(self):
        shutil.rmtree(self.dir, ignore_errors=True); os.makedirs(self.dir)
        json.dump(_cfg(self.n, self.chain_id, self.period), open(f'{self.dir}/cfg.json', 'w'))
        r = subprocess.run([BESU, 'operator', 'generate-blockchain-config', f'--config-file={self.dir}/cfg.json', f'--to={self.dir}/net', '--private-key-file-name=key'], capture_output=True, text=True)
        assert os.path.exists(f'{self.dir}/net/genesis.json'), r.stderr[-500:]
        g = json.load(open(f'{self.dir}/net/genesis.json')); g['alloc'] = {}; json.dump(g, open(f'{self.dir}/net/genesis.json', 'w'))
        keys = sorted(glob.glob(f'{self.dir}/net/keys/*/key')); enode0 = None
        env = dict(os.environ, JAVA_OPTS=f'-Xmx{self.heap} -Xms64m', BESU_OPTS=f'-Xmx{self.heap} -Xms64m')
        for i, kp in enumerate(keys):
            nd = f'{self.dir}/node{i}'; os.makedirs(f'{nd}/data')
            cmd = [BESU, f'--genesis-file={self.dir}/net/genesis.json', f'--node-private-key-file={kp}', f'--data-path={nd}/data',
                   f'--p2p-port={self.p2p_base + i}', f'--rpc-http-port={self.rpc_base + i}', '--rpc-http-enabled', '--rpc-http-api=ETH,NET,QBFT,ADMIN',
                   '--host-allowlist=*', '--rpc-http-cors-origins=*', '--min-gas-price=0', '--sync-min-peers=1', '--logging=WARN']
            if enode0: cmd.append(f'--bootnodes={enode0}')
            self.procs.append(subprocess.Popen(cmd, stdout=open(f'{nd}/log.txt', 'w'), stderr=subprocess.STDOUT, env=env, start_new_session=True))
            if i == 0:
                w = Web3(Web3.HTTPProvider(self.rpc, request_kwargs={'timeout': 5})); t0 = time.time()
                while time.time() - t0 < 180:
                    try: enode0 = w.provider.make_request('admin_nodeInfo', [])['result']['enode']; break
                    except Exception: time.sleep(2)
                assert enode0, 'node0 did not start'
        w = Web3(Web3.HTTPProvider(self.rpc, request_kwargs={'timeout': 5})); t0 = time.time()
        while time.time() - t0 < 300:
            try:
                if w.eth.block_number >= 2 and (self.n == 1 or w.net.peer_count >= self.n - 1): return w
            except Exception: pass
            time.sleep(2)
        raise RuntimeError('network did not reach block 2 with full peering')
    def stop(self):
        for p in self.procs:
            try: os.killpg(p.pid, signal.SIGTERM)
            except Exception: pass
        time.sleep(3)
        for p in self.procs:
            try: os.killpg(p.pid, signal.SIGKILL)
            except Exception: pass
        self.procs = []
