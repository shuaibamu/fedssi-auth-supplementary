"""BBS+ signatures (Au-Susilo-Mu) and selective-disclosure proof of knowledge over BLS12-381.
Prototype for the FedSSI-Auth protocol tests (py_arkworks_bls12381 backend). The proof carries a
'presentation header' ph that is hashed into the Fiat-Shamir challenge, so a proof is valid only for the
(nonce, verifier, session, channel, scope) encoded in ph.
NOTE: research prototype; not constant-time and not a substitute for an audited library."""
import hashlib, secrets
from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT

R = 52435875175126190479447740508185965837690552500527637822603658699938581184513  # BLS12-381 scalar field order
def _sc(i): return Scalar(i % R)
def hash_to_scalar(*parts):
    h = hashlib.sha256()
    for p in parts:
        b = p if isinstance(p, bytes) else str(p).encode()
        h.update(len(b).to_bytes(4, 'big') + b)
    return _sc(int.from_bytes(h.digest(), 'big'))
def rand_scalar():
    while True:
        v = secrets.randbelow(R)
        if v: return _sc(v)
def msg_scalar(label, value): return hash_to_scalar(b'FedSSI-BBS-msg', label, value)

G1 = G1Point(); G2 = G2Point()
_H = {}
def gen(i):
    """nothing-up-my-sleeve generators h_i via hash-to-curve (no known discrete-log relations)"""
    if i not in _H: _H[i] = G1Point.hash_to_curve(f'FedSSI-BBS+-generator-{i}'.encode(), b'FEDSSI-BBS-PLUS-V1')
    return _H[i]

def keygen():
    x = rand_scalar(); return x, G2 * x

def _B(msgs, s):
    B = G1 + gen(0) * s
    for i, m in enumerate(msgs, start=1): B = B + gen(i) * m
    return B

def sign(sk, msgs):
    e, s = rand_scalar(), rand_scalar()
    A = _B(msgs, s) * (sk + e).inverse()
    return A, e, s

def verify(pk, msgs, sig):
    A, e, s = sig
    return GT.pairing(A, pk + G2 * e) == GT.pairing(_B(msgs, s), G2)

def _pt(p): return p.to_compressed_bytes()
def _challenge(ph, Ap, Abar, d, T1, T2, revealed):
    return hash_to_scalar(b'FedSSI-BBS-proof', ph, _pt(Ap), _pt(Abar), _pt(d), _pt(T1), _pt(T2),
                          b'|'.join(str(i).encode() + b':' + int(m).to_bytes(32, 'big') for i, m in sorted(revealed.items())))

def proof_gen(sig, msgs, reveal_idx, ph):
    A, e, s = sig; L = len(msgs); reveal = set(reveal_idx); hidden = [i for i in range(1, L + 1) if i not in reveal]
    B = _B(msgs, s); r1, r2 = rand_scalar(), rand_scalar(); r3 = r1.inverse()
    Ap = A * r1; Abar = Ap * (-e) + B * r1; d = B * r1 - gen(0) * r2; sp = s - r2 * r3
    re_, rr2, rr3, rsp = rand_scalar(), rand_scalar(), rand_scalar(), rand_scalar(); rm = {i: rand_scalar() for i in hidden}
    T1 = Ap * (-re_) + gen(0) * rr2
    T2 = d * rr3 - gen(0) * rsp
    for i in hidden: T2 = T2 - gen(i) * rm[i]
    revealed = {i: msgs[i - 1] for i in reveal}
    c = _challenge(ph, Ap, Abar, d, T1, T2, revealed)
    return dict(Ap=Ap, Abar=Abar, d=d, c=c, e_hat=re_ + c * e, r2_hat=rr2 + c * r2, r3_hat=rr3 + c * r3, sp_hat=rsp + c * sp,
                m_hat={i: rm[i] + c * msgs[i - 1] for i in hidden}, L=L)

def proof_verify(pk, proof, revealed, ph):
    """revealed: {index(1-based): message scalar}. Returns True iff proof is valid for these revealed messages and header ph."""
    try:
        Ap, Abar, d, c = proof['Ap'], proof['Abar'], proof['d'], proof['c']; L = proof['L']
        if Ap == G1Point.identity(): return False
        if GT.pairing(Ap, pk) != GT.pairing(Abar, G2): return False
        hidden = [i for i in range(1, L + 1) if i not in revealed]
        if set(hidden) != set(proof['m_hat'].keys()): return False
        T1 = Ap * (-proof['e_hat']) + gen(0) * proof['r2_hat'] - (Abar - d) * c
        base = G1
        for i, m in revealed.items(): base = base + gen(i) * m
        T2 = d * proof['r3_hat'] - gen(0) * proof['sp_hat']
        for i in hidden: T2 = T2 - gen(i) * proof['m_hat'][i]
        T2 = T2 - base * c
        return _challenge(ph, Ap, Abar, d, T1, T2, revealed) == c
    except Exception:
        return False

if __name__ == '__main__':
    import time
    sk, pk = keygen(); msgs = [msg_scalar('a', i) for i in range(8)]
    sig = sign(sk, msgs); assert verify(pk, msgs, sig); assert not verify(pk, msgs[:-1] + [msg_scalar('x', 1)], sig)
    ph = b'header'; t = time.time(); pf = proof_gen(sig, msgs, [1, 2, 3, 8], ph); tg = time.time() - t
    rev = {i: msgs[i - 1] for i in [1, 2, 3, 8]}
    t = time.time(); ok = proof_verify(pk, pf, rev, ph); tv = time.time() - t
    bad_ph = proof_verify(pk, pf, rev, b'other'); bad_rev = proof_verify(pk, pf, {**rev, 2: msg_scalar('z', 9)}, ph)
    print('sign/verify ok; proof ok', ok, 'wrong-ph', bad_ph, 'tampered-reveal', bad_rev, f'gen {tg*1000:.1f} ms verify {tv*1000:.1f} ms')
