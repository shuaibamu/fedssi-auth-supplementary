import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from tikzlib2 import *
def fig1():
    rows = [(r'\textbf{T1}\\Impersonation\\(stolen credentials)', 'Steps 13--15: holder-key\\\\binding, issuer proof,\\\\holder signature\\\\(requires non-extractable $sk_H$)', 'Protocol tests\\\\N1, N1b, N1c\\\\(live contracts)'),
            (r'\textbf{T2}\\Replay / relay\\(captured presentation)', 'Steps 2--3, 14--15: single-use\\\\challenge; $ph$ binds verifier,\\\\session, channel, scope', 'Protocol tests\\\\N2 to N4b'),
            (r'\textbf{T3}\\Post-issuance\\credential abuse', 'Steps 16, 19:\\\\gateway-measured flow gate\\\\and re-scoring ($M_\\theta(f)>\\tau$)', 'Classifier on RT-IoT2022\\\\(component test);\\\\integrated test (small)'),
            (r'\textbf{T4}\\Sybil DID /\\trust assertion', 'Verifying-domain admin only\\\\(contract access control)', 'Contract revert test\\\\N8d'),
            (r'\textbf{T5}\\Revocation\\evasion', 'Steps 11--13: on-chain\\\\status-list read\\\\(freshness: one block)', 'Protocol tests\\\\N7, N8c')]
    b = r"\begin{tikzpicture}[font=\small]" + "\n" + r"\node[font=\bfseries\small] at (0,1.15) {Threats (T1--T5)}; \node[font=\bfseries\small] at (6.6,1.15) {Check in Algorithm 1 (step \#)}; \node[font=\bfseries\small] at (12.9,1.15) {Evidence in this paper (scope)};" + "\n"
    for i, (a, c, e) in enumerate(rows):
        y = -i * 2.15
        b += rf"""\node[node,fill=pinkb,minimum width=3.5cm,minimum height=1.55cm,font=\footnotesize] (t{i}) at (0,{y}) {{{a}}};
\node[node,fill=greenb,minimum width=5.0cm,minimum height=1.55cm,font=\footnotesize] (c{i}) at (6.6,{y}) {{{c}}};
\node[node,fill=lav,minimum width=3.6cm,minimum height=1.55cm,font=\footnotesize\itshape] (e{i}) at (12.9,{y}) {{{e}}};
\draw[-{{Stealth[length=2.6mm]}},thick,dashed,dred] (t{i}) -- (c{i}); \draw[-{{Stealth[length=2.6mm]}},thick] (c{i}) -- (e{i});
"""
    b += r"""\draw[-{Stealth[length=2.6mm]},thick,dashed,dred] (-1.6,-9.7) -- (0.6,-9.7); \node[anchor=west,font=\footnotesize] at (0.8,-9.7) {mitigated by the check};
\draw[-{Stealth[length=2.6mm]},thick] (5.2,-9.7) -- (7.2,-9.7); \node[anchor=west,font=\footnotesize] at (7.4,-9.7) {produces evidence (not a proof)};
\end{tikzpicture}"""
    return build('fig1', b, 200)
def fig2():
    dx = 2.95
    b = r"""\begin{tikzpicture}[font=\small]
\tikzset{n1/.style={node,fill=lav,minimum width=2.45cm,minimum height=1.25cm,font=\small},n2/.style={node,fill=yelb,minimum width=2.6cm,minimum height=1.25cm,font=\footnotesize},
 n3/.style={node,fill=greenb,minimum width=2.6cm,minimum height=1.25cm,font=\footnotesize},n4/.style={node,fill=peach,minimum width=2.45cm,minimum height=1.1cm,font=\small},
 lbl/.style={font=\footnotesize\itshape,fill=white,inner sep=1pt}}
"""
    dev = ['MQTT\\\\Sensor', 'Smart\\\\Bulb', 'IP\\\\Camera', 'ThingSpeak\\\\Gateway', 'Industrial\\\\PLC']
    for i, t in enumerate(dev): b += rf"\node[n1] (d{i}) at ({i*dx},0) {{{t}}};" + "\n"
    b += rf"\node[n1,fill=pinkb,dashed,font=\small\bfseries] (d5) at ({5*dx},0) {{Compromised\\device}};" + "\n"
    b += r"""\node[domblue,font=\small\itshape] at (0,-1.15) {[Domain A: smart city]}; \node[domblue,font=\small\itshape] at (5.9,-1.15) {[Domain B: healthcare]}; \node[domblue,font=\small\itshape] at (11.8,-1.15) {[Domain C: industrial]};
"""
    l2 = ['DID resolver\\\\+ VC wallet', 'Trust + status\\\\checks', 'Challenge +\\\\binding ($ph$)', 'Traffic monitor\\\\+ RF gate', 'Policy engine\\\\(BBS+, holder key)']
    for i, t in enumerate(l2): b += rf"\node[n2] (g{i}) at ({i*dx},-4.3) {{{t}}};" + "\n"
    l3 = ['DIDRegistry', 'TrustAnchor\\\\Registry', 'RevocationList', 'QBFT consensus\\\\(Besu)']
    for i, t in enumerate(l3): b += rf"\node[n3] (r{i}) at ({i*dx},-7.6) {{{t}}};" + "\n"
    l4 = ['Smart-city\\\\dashboard', 'Healthcare\\\\portal', 'e-Government\\\\portal', 'Industrial\\\\SCADA', 'Mobile / web\\\\apps']
    for i, t in enumerate(l4): b += rf"\node[n4] (v{i}) at ({i*dx},-10.6) {{{t}}};" + "\n"
    ar = r"-{Stealth[length=2.6mm]},thick"
    b += rf"""\draw[{ar}] (d0.south) -- (g0.north) node[pos=.4,right,lbl] {{did + presentation}};
\draw[{ar}] (d1.south) -- (g2.north) node[pos=.4,right,lbl] {{challenge}};
\draw[{ar}] (d2.south) -- (g3.north) node[pos=.4,right,lbl] {{flow}};
\draw[{ar}] (g0.south) -- (r0.north) node[pos=.3,right,lbl] {{resolveDIDs()}};
\draw[{ar}] (g1.south) -- (r1.north) node[pos=.3,right,lbl] {{isTrusted()}};
\draw[{ar}] (g1.south east) -- (r2.north west) node[pos=.3,above right,lbl] {{isRevoked()}};
\draw[{ar},black!70] (g4.east) -- ++(1.15,0) |- (v4.east) node[pos=.25,above,rotate=90,lbl] {{bound, short-lived token}};
\draw[{ar},dashed,crimson,thick,{{Stealth[length=2.6mm]}}-{{Stealth[length=2.6mm]}}] (-1.4,-11.7) -- (13.6,-11.7) node[midway,above,font=\small\itshape,crimson,fill=white,inner sep=1pt] {{cross-domain trust assertion (administered by the verifying domain)}};
\node[anchor=west,font=\large\bfseries,fill=white,inner sep=1pt] at (-1.4,1.25) {{Layer 1 -- IoT Edge Holders (multi-domain)}};
\node[anchor=west,font=\large\bfseries,fill=white,inner sep=1pt] at (-1.4,-2.95) {{Layer 2 -- SSI Authentication Gateway}};
\node[anchor=west,font=\large\bfseries,fill=white,inner sep=1pt] at (-1.4,-6.45) {{Layer 3 -- Blockchain Verifiable Data Registry}};
\node[anchor=west,font=\large\bfseries,fill=white,inner sep=1pt] at (-1.4,-9.4) {{Layer 4 -- Federated Verifiers / Relying Parties}};
\end{{tikzpicture}}"""
    return build('fig2', b, 170)
def fig3():
    X = {'H': 0, 'V': 6.6, 'B': 11.8, 'R': 16.4}; dy = 0.9; y0 = -1.5
    S = [('1', 'H', 'V', r'did$_H \,\|\,$ scope $\,\|\, D_R$', ''), ('2', 'V', None, r'$n, sid, ts$ fresh; $ph = h(n\|V_{id}\|sid\|ts\|D_R\|scope\|ch)$ \ (T2)', ''), ('3', 'V', 'H', r'$(n, V_{id}, sid, ts)$ challenge', ''),
         ('4', 'H', None, r'$(\pi, claims)\leftarrow$ ProofGen$(VC_H, ph)$;\ $\sigma_H\leftarrow$ Sign$(h(ph\|\pi\|claims))$', ''), ('5', 'H', 'V', r'$VP_H=(claims,\pi,issuer)$, $\sigma_H$', ''),
         ('6', 'V', 'B', r'resolveDIDs$(did_H, issuer)$', ''), ('7', 'B', 'V', r'$(hash_H, act_H, hash_I, act_I)$', 'res'), ('8', 'V', None, r'doc hashes, active flags; extract $pk_H, pk_I$ \ (T5)', ''),
         ('9', 'V', 'B', r'isTrusted$(D_R, D_I, issuer, schema)$', ''), ('10', 'B', 'V', r'trusted $\in\{$true, false$\}$', 'res'), ('11', 'V', 'B', r'isRevoked$(listId, revIdx)$', ''), ('12', 'B', 'V', r'revoked $\in\{$true, false$\}$', 'res'),
         ('13', 'V', None, r'trusted, not revoked, not expired, policy, holderKey $=h(pk_H)$ \ (T1, T5)', ''), ('14', 'V', None, r'ProofVerify$(\pi, pk_I, claims, ph)$ \ (T1, T2)', ''), ('15', 'V', None, r'Verify$(pk_H, \sigma_H, h(ph\|\pi\|claims))$ \ (T1)', ''),
         ('16', 'V', None, r'features $f$ measured by $V$; require $M_\theta(f)\le\tau$ \ (T3)', ''), ('17', 'V', 'R', r'auth\_token $=$ Sign$_V(did\|aud\|scope\|exp\|sid\|cnf)$', ''), ('18', 'R', None, r'verify token fields; accept session', ''),
         ('19', 'V', None, r'every $\Delta$ s: re-score new flows; revoke $sid$ if $M_\theta>\tau$ \ (T3)', '')]
    b = r"\begin{tikzpicture}[font=\footnotesize]" + "\n"
    for k, lab in {'H': 'H\\\\(Holder)', 'V': 'V\\\\(SSI Gateway)', 'B': 'B\\\\(Blockchain VDR)', 'R': 'R\\\\(Relying Party)'}.items(): b += rf"\node[draw,thick,fill=lav,minimum width=2.9cm,minimum height=1.0cm,align=center,font=\small\bfseries] at ({X[k]},0) {{{lab}}};" + "\n"
    ybot = y0 - dy * len(S)
    for k in X: b += rf"\draw[thick] ({X[k]},-0.5) -- ({X[k]},{ybot});" + "\n"
    for i, (num, a, c, t, sty) in enumerate(S):
        y = y0 - i * dy
        if c is None:
            if a == 'R': b += rf"\node[draw,rounded corners=1.5pt,fill=yelb,anchor=east,font=\footnotesize\itshape,inner sep=3pt] at ({X['R']+1.0},{y}) {{{num}.\ {t}}};" + "\n"
            else: b += rf"\node[draw,rounded corners=1.5pt,fill=yelb,anchor=west,font=\footnotesize\itshape,inner sep=3pt] at ({X[a]+0.5},{y}) {{{num}.\ {t}}};" + "\n"
        else:
            col = 'resgreen' if sty == 'res' else 'reqblue'; st = 'res' if sty == 'res' else 'req'
            b += rf"\draw[{st}] ({X[a]},{y}) -- ({X[c]},{y}) node[midway,above=-0.5pt,font=\footnotesize\itshape,text={col}] {{{num}.\ {t}}};" + "\n"
    ly = ybot - 0.7
    b += rf"""\draw[req] (-1.2,{ly}) -- (0.6,{ly}); \node[anchor=west,font=\footnotesize] at (0.7,{ly}) {{\textbf{{Solid arrow}} = request}};
\draw[res] (5.2,{ly}) -- (7.0,{ly}); \node[anchor=west,font=\footnotesize] at (7.1,{ly}) {{\textbf{{Dashed arrow}} = response}};
\node[draw,rounded corners=1.5pt,fill=yelb,minimum width=0.7cm,minimum height=0.4cm] at (12.0,{ly}) {{}}; \node[anchor=west,font=\footnotesize] at (12.5,{ly}) {{\textbf{{Yellow box}} = op.}};
\node[anchor=west,font=\footnotesize] at (15.2,{ly}) {{\textbf{{Tn}} = threat mitigated}};
\end{{tikzpicture}}"""
    return build('fig3', b, 150)
def fig7():
    rows = [('Phase 1: Data \\& Preprocessing', ['RT-IoT2022\\\\(UCI)', 'Clean +\\\\One-hot Encode', 'Stratified\\\\75/25 Split', 'Binary Label\\\\Auth/Unauth'], ['lav'] * 4),
            ('Phase 2: Framework Design \\& Smart-Contract Deployment', ['Define\\\\Auth Protocol (19 steps)', 'Solidity SCs:\\\\DID/Trust/Revoc', 'Deploy on\\\\Besu QBFT', 'Benchmark\\\\Gas/Latency/Throughput'], ['mauve'] * 4),
            ('Phase 3: ML Authentication Filter Training', ['Feature Set\\\\(80 num + 2 cat)', 'Train 6 Models\\\\LR/DT/kNN/SVM/GB/RF', '5-fold CV\\\\(training split only)', 'Select $\\tau$ on\\\\OOF scores'], ['yelb', 'greenb', 'greenb', 'greenb']),
            ('Phase 4: Evaluation \\& Comparative Analysis', ['Test Metrics\\\\+ Paired Tests', 'Harder Settings\\\\(family/block/session)', 'Cross-dataset\\\\Transfer (CIC-IDS2017)', 'Protocol + Integrated\\\\Gateway Test'], ['peach'] * 4)]
    b = r"\begin{tikzpicture}[font=\small]" + "\n" + r"\tikzset{pb/.style={node,minimum width=3.2cm,minimum height=1.3cm,font=\footnotesize,drop shadow={shadow xshift=1.3pt,shadow yshift=-1.3pt,opacity=.4}}}" + "\n"
    for r, (t, bx, cols) in enumerate(rows):
        y = -r * 3.35
        b += rf"\node[anchor=west,font=\bfseries\normalsize] at (-1.6,{y+1.2}) {{{t}}};" + "\n"
        if r == 3: b += rf"\fill[black!3,rounded corners=4pt,draw=black!20] (-1.85,{y-0.95}) rectangle (13.0,{y+0.72});" + "\n"
        for i, s in enumerate(bx): b += rf"\node[pb,fill={cols[i]}] (p{r}{i}) at ({i*3.75},{y}) {{{s}}};" + "\n"
        for i in range(3): b += rf"\draw[-{{Stealth[length=2.2mm]}},thick,black!75] (p{r}{i}.east) -- (p{r}{i+1}.west);" + "\n"
    for r in range(3): b += rf"\draw[-{{Stealth[length=2.2mm]}},thick,black!75] (p{r}3.south) -- ++(0,-0.55) -| ($(p{r+1}0.west)+(-0.4,0)$) -- (p{r+1}0.west);" + "\n"
    b += r"""\draw[-{Stealth[length=2.4mm]},thick,dashed,red!75] (p32.north) -- (p22.south); \node[red!75,font=\scriptsize\itshape,anchor=west] at ([xshift=0.12cm,yshift=0.42cm]p32.north) {transfer check on CIC-IDS2017};
\end{tikzpicture}"""
    return build('fig7', b, 190)
if __name__ == '__main__':
    for w in (sys.argv[1:] or ['1', '2', '3', '7']): globals()[f'fig{w}']()
