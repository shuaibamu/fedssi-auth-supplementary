import os
"""Redrawn diagrams for Revision 2: Fig.1 threat-to-check mapping, Fig.2 architecture, Fig.3 sequence diagram of the corrected Algorithm 1, Fig.7 methodology."""
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
FIG = os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures')
def box(ax, x, y, w, h, t, fc='#E6E6FF', ec='k', fs=8.5, ls='-', bold=False, lw=1.1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.004,rounding_size=0.012', fc=fc, ec=ec, lw=lw, ls=ls)); ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=fs, fontweight='bold' if bold else 'normal')
def arr(ax, p, q, ls='-', c='k', lw=1.1, style='-|>', ms=10, cs='arc3'):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, ls=ls, color=c, lw=lw, connectionstyle=cs))
def canvas(w, h):
    fig = plt.figure(figsize=(w, h)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off'); return fig, ax
def fig1():
    fig, ax = canvas(11, 7.6); ax.text(.5, .965, 'Threat-to-check mapping', ha='center', fontsize=14, fontweight='bold'); ax.text(.5, .93, 'checks mitigate each threat under the stated assumptions; the right column names the evidence and its scope', ha='center', fontsize=9, style='italic')
    for x, t in [(.145, 'Threat'), (.52, 'Check in Algorithm 1'), (.855, 'Evidence in this paper')]: ax.text(x, .885, t, ha='center', fontsize=10.5, fontweight='bold')
    rows = [('T1  Impersonation\n(stolen credential)', 'Steps 13-15: holder-key binding, issuer proof,\nholder signature (needs non-extractable sk_H)', 'Protocol tests N1, N1b, N1c\n(live contracts)'),
            ('T2  Replay / relay of a\npresentation', 'Steps 2-3, 14-15: single-use challenge; proof and\nsignature bound to verifier, session, channel, scope', 'Protocol tests N2 to N4b'),
            ('T3  Post-issuance\ncredential abuse', 'Steps 16 and 19: gateway-measured flow gate\nand re-scoring while the session is active', 'Classifier on RT-IoT2022\n(component test); integrated\ngateway test (small)'),
            ('T4  Sybil DID /\ntrust assertion', 'Contract access control: only the verifying\ndomain admin can write assertions', 'Contract revert test N8d'),
            ('T5  Revocation\nevasion', 'Steps 11-13: on-chain status-list read\n(freshness bounded by block time)', 'Protocol tests N7, N8c')]
    ys = [.76, .60, .44, .28, .12]
    for (a, b, c), y in zip(rows, ys):
        box(ax, .02, y, .25, .11, a, fc='#FFE0E0', fs=9, bold=True); box(ax, .33, y, .38, .11, b, fc='#DFF5DF', fs=8.6); box(ax, .77, y, .21, .11, c, fc='#E6E6FF', fs=8.6)
        arr(ax, (.27, y + .055), (.33, y + .055), ls='--', c='#b00000'); arr(ax, (.71, y + .055), (.77, y + .055))
    ax.text(.02, .035, '- - ->  check addresses the threat      ——>  evidence for the check (not a security proof)', fontsize=8.5); fig.savefig(f'{FIG}/fig1.png', dpi=130); plt.close()
def fig2():
    fig, ax = canvas(14.5, 9.6); ys = {1: .80, 2: .56, 3: .32, 4: .09}; H = .10
    for k, t in [(1, 'Layer 1 - IoT edge holders (multiple administrative domains)'), (2, 'Layer 2 - SSI authentication gateway (verifier side)'), (3, 'Layer 3 - Blockchain verifiable data registry (Hyperledger Besu, QBFT)'), (4, 'Layer 4 - Federated verifiers / relying parties')]: ax.text(.01, ys[k] + H + .03, t, fontsize=12, fontweight='bold')
    l1 = [('MQTT sensor\n[Domain A: smart city]', '#E6E6FF'), ('Smart bulb', '#E6E6FF'), ('IP camera\n[Domain B: healthcare]', '#E6E6FF'), ('ThingSpeak\ngateway', '#E6E6FF'), ('Industrial PLC\n[Domain C: industrial]', '#E6E6FF'), ('Compromised device\n(valid credential,\nattack traffic)', '#FFD6D6')]
    for i, (t, c) in enumerate(l1): box(ax, .03 + i * .16, ys[1], .14, H, t, fc=c, fs=9, ls='--' if c == '#FFD6D6' else '-')
    l2 = ['DID resolver +\nVC wallet', 'Challenge, binding\n(ph: nonce, verifier,\nsession, channel, scope)', 'Traffic monitor +\nRandom Forest gate\n(gateway-measured flows)', 'Policy engine\n(BBS+ verify, claims,\nholder-key binding)']
    for i, t in enumerate(l2): box(ax, .05 + i * .235, ys[2], .2, H, t, fc='#FFFBCF', fs=9)
    l3 = ['DIDRegistry', 'TrustAnchorRegistry\n(verifier-domain admin\nassertions)', 'RevocationList\n(bitmap status lists)', 'QBFT consensus\n(validators)']
    for i, t in enumerate(l3): box(ax, .05 + i * .235, ys[3], .2, H, t, fc='#DFF5DF', fs=9)
    l4 = ['Smart-city\ndashboard', 'Healthcare\nportal', 'e-Government\nportal', 'Industrial\nSCADA', 'Mobile / web\napps']
    for i, t in enumerate(l4): box(ax, .04 + i * .19, ys[4], .16, H, t, fc='#FFE8CC', fs=9)
    arr(ax, (.10, ys[1]), (.15, ys[2] + H)); ax.text(.095, ys[1] - .045, 'did + presentation', fontsize=8, style='italic')
    arr(ax, (.35, ys[1]), (.58, ys[2] + H), ls='--'); ax.text(.40, ys[1] - .03, 'on-path traffic (flows measured by the gateway)', fontsize=8, style='italic')
    arr(ax, (.15, ys[2]), (.15, ys[3] + H)); ax.text(.16, ys[2] - .05, 'resolveDIDs()', fontsize=8, style='italic')
    arr(ax, (.385, ys[2]), (.385, ys[3] + H)); ax.text(.395, ys[2] - .05, 'isTrusted()', fontsize=8, style='italic'); arr(ax, (.62, ys[2]), (.62, ys[3] + H)); ax.text(.63, ys[2] - .05, 'isRevoked()', fontsize=8, style='italic')
    arr(ax, (.972, ys[2] + H / 2), (.972, ys[4] + H), c='#444'); ax.text(.968, ys[3] + .13, 'bound, short-lived token', fontsize=8, style='italic', rotation=90, ha='right', va='center')
    arr(ax, (.06, ys[3] - .03), (.94, ys[3] - .03), ls='--', c='#8b0057', style='<|-|>'); ax.text(.5, ys[3] - .027, 'cross-domain trust assertion (administered by the verifying domain)', ha='center', fontsize=9, color='#8b0057')
    fig.savefig(f'{FIG}/fig2.png', dpi=150); plt.close()
def fig3():
    fig, ax = canvas(10.8, 10.4); X = {'H': .12, 'V': .42, 'B': .70, 'R': .92}; top = .955; bot = .045
    for k, t in [('H', 'H\n(Holder)'), ('V', 'V\n(SSI gateway)'), ('B', 'B\n(Blockchain VDR)'), ('R', 'R\n(Relying party)')]: box(ax, X[k] - .075, top, .15, .04, t, fs=8.5, bold=True); ax.plot([X[k], X[k]], [bot, top], color='k', lw=.9)
    steps = [('1', 'H', 'V', 'did_H || scope || D_R', 'A'), ('2', 'V', None, 'n, sid, ts; ph = h(n||V_id||sid||ts||D_R||scope||ch)', 'A'), ('3', 'V', 'H', '(n, V_id, sid, ts)  challenge', 'A'),
             ('4', 'H', None, 'ProofGen(VC_H, ph);  sigma_H = Sign(h(ph||pi||claims))', 'B'), ('5', 'H', 'V', 'VP_H = (claims, pi, issuer), sigma_H', 'B'),
             ('6', 'V', 'B', 'resolveDIDs(did_H, issuer_did)', 'C'), ('7', 'B', 'V', '(hash_H, act_H, hash_I, act_I)', 'C'), ('8', 'V', None, 'doc hashes, status; extract pk_H, pk_I', 'C'),
             ('9', 'V', 'B', 'isTrusted(D_R, D_I, issuer, schema)', 'C'), ('10', 'B', 'V', 'trusted', 'C'), ('11', 'V', 'B', 'isRevoked(listId, revIdx)', 'C'), ('12', 'B', 'V', 'revoked', 'C'),
             ('13', 'V', None, 'trusted, not revoked, not expired, policy, holderKey = h(pk_H)', 'C'), ('14', 'V', None, 'ProofVerify(pi, pk_I, claims, ph)', 'C'), ('15', 'V', None, 'Verify(pk_H, sigma_H, h(ph||pi||claims))', 'C'),
             ('16', 'V', None, 'features f of H measured by V; require M(f) <= tau', 'D'), ('17', 'V', 'R', 'auth_token = Sign_V(did||aud||scope||exp||sid||cnf)', 'D'), ('18', 'R', None, 'verify token fields; accept', 'D'), ('19', 'V', None, 'every Delta s: re-score new flows; revoke sid if M > tau', 'D')]
    n = len(steps); dy = (top - bot - .03) / n; bands = {'A': '#EEF3FF', 'B': '#F4EEFF', 'C': '#F1FAF1', 'D': '#FFF5E8'}; names = {'A': 'A: challenge', 'B': 'B: presentation', 'C': 'C: registry reads and checks', 'D': 'D: behavioural gate, token'}
    for ph in 'ABCD':
        idx = [i for i, s in enumerate(steps) if s[4] == ph]; y0 = top - .02 - (idx[-1] + 1) * dy; y1 = top - .02 - idx[0] * dy; ax.add_patch(plt.Rectangle((.0, y0), 1, y1 - y0, fc=bands[ph], ec='none', zorder=0)); ax.text(.995, y1 - .008, names[ph], ha='right', va='top', fontsize=7.5, color='#555', style='italic')
    for i, (num, a, b, t, ph) in enumerate(steps):
        y = top - .02 - (i + .55) * dy
        if b is None:
            label = f'{num}. {t}'; wbox = min(.70, .0056 * len(label) + .035)
            x0 = (X['R'] + .07 - wbox) if a == 'R' else (X[a] - .02)
            box(ax, x0, y - dy * .36, wbox, dy * .72, label, fc='#FFFBCF', fs=7.4)
        else:
            arr(ax, (X[a], y), (X[b], y), ls='--' if num in ('7', '10', '12') else '-', c='#1a7f1a' if num in ('7', '10', '12') else '#1a1aaa', ms=9); ax.text((X[a] + X[b]) / 2, y + dy * .12, f'{num}. {t}', ha='center', fontsize=7.4, color='#1a1aaa' if num not in ('7', '10', '12') else '#1a7f1a')
    fig.savefig(f'{FIG}/fig3.png', dpi=135); plt.close()
def fig7():
    fig, ax = canvas(9.4, 8.6); rows = [('Phase 1: Data and preprocessing', ['RT-IoT2022\n(UCI repository)', 'Clean + one-hot encode\n(fitted inside folds)', 'Stratified 75/25 split\n(12-class strata)', 'Binary label:\nAuthorized = 3 normal\nclasses'], '#E6E6FF'),
            ('Phase 2: Framework design and smart contracts', ['Define protocol\n(19 steps)', 'Solidity contracts\n(3, one source)', 'Deploy on\nBesu QBFT', 'Measure gas, latency,\nthroughput'], '#F0E6F0'),
            ('Phase 3: Gateway classifier', ['Feature set\n(80 numeric + 2 categorical)', 'Train 6 models on the\nidentical training split', '5-fold CV inside the\ntraining split', 'Select tau on training\nout-of-fold scores'], '#DFFFDF'),
            ('Phase 4: Evaluation', ['Held-out test metrics\n+ paired tests', 'Harder settings\n(family, block, session)', 'Cross-dataset transfer\n(CIC-IDS2017)', 'Protocol tests +\nintegrated gateway test'], '#FFEEDD')]
    ys = [.78, .56, .34, .12]; fig.suptitle('Research methodology pipeline', fontsize=14, fontweight='bold', y=.985)
    for (t, bx, c), y in zip(rows, ys):
        ax.text(.03, y + .15, t, fontsize=10.5, fontweight='bold')
        for i, s_ in enumerate(bx):
            box(ax, .03 + i * .24, y, .21, .13, s_, fc=c, fs=8.4)
            if i < 3: arr(ax, (.24 + i * .24, y + .065), (.27 + i * .24, y + .065))
    for y in ys[:-1]:
        yn = y - .22; ax.plot([.855, .855], [y, y - .035], color='k', lw=1.1); ax.plot([.855, .012], [y - .035, y - .035], color='k', lw=1.1); ax.plot([.012, .012], [y - .035, yn + .065], color='k', lw=1.1); arr(ax, (.012, yn + .065), (.03, yn + .065))
    fig.savefig(f'{FIG}/fig7.png', dpi=135); plt.close()
if __name__ == '__main__':
    import sys
    for w in (sys.argv[1:] or ['1', '2', '3', '7']):
        try: globals()[f'fig{w}'](); print('fig', w, 'ok')
        except Exception as e: print('fig', w, 'FAILED', repr(e))
