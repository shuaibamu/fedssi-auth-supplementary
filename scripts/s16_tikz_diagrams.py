import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from tikzlib import *
STY = r"""\tikzset{box/.style={draw,rounded corners=3pt,thick,align=center,drop shadow={shadow xshift=1.2pt,shadow yshift=-1.2pt,opacity=.35}},
 req/.style={-{Stealth[length=2.2mm]},thick,blue!70!black},res/.style={-{Stealth[length=2.2mm]},thick,dashed,green!50!black}}"""
def fig1():
    rows = [(r'\textbf{T1}\quad Impersonation\\(stolen credential)', 'Steps 13--15: holder-key binding, issuer proof,\\\\holder signature (needs non-extractable $sk_H$)', 'Protocol tests N1, N1b, N1c\\\\(live contracts)'),
            (r'\textbf{T2}\quad Replay / relay of a\\presentation', 'Steps 2--3, 14--15: single-use challenge; proof and\\\\signature bound to verifier, session, channel, scope', 'Protocol tests N2 to N4b'),
            (r'\textbf{T3}\quad Post-issuance\\credential abuse', 'Steps 16 and 19: gateway-measured flow gate\\\\and re-scoring while the session is active', 'Classifier on RT-IoT2022\\\\(component test); integrated\\\\gateway test (small)'),
            (r'\textbf{T4}\quad Sybil DID /\\trust assertion', 'Contract access control: only the verifying\\\\domain admin can write assertions', 'Contract revert test N8d'),
            (r'\textbf{T5}\quad Revocation\\evasion', 'Steps 11--13: on-chain status-list read\\\\(freshness bounded by block time)', 'Protocol tests N7, N8c')]
    b = STY + r"""
\begin{tikzpicture}[font=\small]
\node[font=\Large\bfseries] at (7.4,1.5) {Threat-to-check mapping};
\node[font=\footnotesize\itshape] at (7.4,0.85) {checks mitigate each threat under the stated assumptions; the right column names the evidence and its scope};
\node[font=\bfseries] at (0,0) {Threat}; \node[font=\bfseries] at (6.5,0) {Check in Algorithm 1}; \node[font=\bfseries] at (12.6,0) {Evidence in this paper};
"""
    for i, (a, c, e) in enumerate(rows):
        y = -1.8 - 2.15 * i
        b += rf"""\node[box,fill=red!12,minimum width=4.6cm,minimum height=1.6cm] (t{i}) at (0,{y}) {{{a}}};
\node[box,fill=green!14,minimum width=7.4cm,minimum height=1.6cm] (c{i}) at (6.5,{y}) {{\footnotesize {c}}};
\node[box,fill=blue!10,minimum width=4.5cm,minimum height=1.6cm] (e{i}) at (12.6,{y}) {{\footnotesize {e}}};
\draw[-{{Stealth}},thick,dashed,red!70!black] (t{i}) -- (c{i}); \draw[-{{Stealth}},thick] (c{i}) -- (e{i});
"""
    b += r"""\node[font=\footnotesize,anchor=west] at (-2.3,-12.1) {\textcolor{red!70!black}{- - $\rightarrow$} check addresses the threat \qquad $\longrightarrow$ evidence for the check (not a security proof)};
\end{tikzpicture}"""
    return build('fig1', b, 190)
def fig2():
    b = STY + r"""
\begin{tikzpicture}[font=\small,node distance=0pt]
\tikzset{n1/.style={box,fill=blue!10,minimum width=2.75cm,minimum height=1.45cm,font=\scriptsize},n2/.style={box,fill=yellow!25,minimum width=4.2cm,minimum height=1.55cm,font=\scriptsize},
 n3/.style={box,fill=green!14,minimum width=4.2cm,minimum height=1.55cm,font=\scriptsize},n4/.style={box,fill=orange!18,minimum width=3.1cm,minimum height=1.35cm,font=\scriptsize}}
\node[n1] (a1) at (0.2,0) {MQTT sensor\\{[}Domain A: smart city{]}}; \node[n1] (a2) at (3.2,0) {Smart bulb}; \node[n1] (a3) at (6.2,0) {IP camera\\{[}Domain B: healthcare{]}};
\node[n1] (a4) at (9.2,0) {ThingSpeak\\gateway}; \node[n1] (a5) at (12.2,0) {Industrial PLC\\{[}Domain C: industrial{]}}; \node[n1,fill=red!14,dashed] (a6) at (15.2,0) {Compromised device\\(valid credential,\\attack traffic)};
\node[n2] (b1) at (1.2,-4.2) {DID resolver +\\VC wallet}; \node[n2] (b2) at (5.7,-4.2) {Challenge and binding\\(ph: nonce, verifier, session,\\channel, scope)};
\node[n2] (b3) at (10.2,-4.2) {Traffic monitor +\\Random Forest gate\\(gateway-measured flows)}; \node[n2] (b4) at (14.7,-4.2) {Policy engine (BBS+ verify,\\claims, holder-key binding)};
\node[n3] (c1) at (1.2,-8.4) {DIDRegistry}; \node[n3] (c2) at (5.7,-8.4) {TrustAnchorRegistry\\(verifying-domain admin\\assertions)};
\node[n3] (c3) at (10.2,-8.4) {RevocationList\\(bitmap status lists)}; \node[n3] (c4) at (14.7,-8.4) {QBFT consensus\\(validators)};
\node[n4] (d1) at (0.4,-12.3) {Smart-city\\dashboard}; \node[n4] (d2) at (3.8,-12.3) {Healthcare\\portal}; \node[n4] (d3) at (7.2,-12.3) {e-Government\\portal}; \node[n4] (d4) at (10.6,-12.3) {Industrial\\SCADA}; \node[n4] (d5) at (14.0,-12.3) {Mobile / web\\apps};
\draw[-{Stealth},thick] (a1.south) -- (b1.north) node[pos=.2,right,font=\scriptsize\itshape] {did + presentation};
\draw[-{Stealth},thick,dashed] (a3.south) -- (b3.north) node[pos=.35,above right,font=\scriptsize\itshape,align=left] {on-path traffic (flows\\measured by the gateway)};
\draw[-{Stealth},thick] (b1.south) -- (c1.north) node[pos=.86,right,font=\scriptsize\itshape] {resolveDIDs()};
\draw[-{Stealth},thick] (b2.south) -- (c2.north) node[pos=.86,right,font=\scriptsize\itshape] {isTrusted()};
\draw[-{Stealth},thick] (b3.south) -- (c3.north) node[pos=.86,right,font=\scriptsize\itshape] {isRevoked()};
\draw[-{Stealth},thick,black!70] (b4.east) -- ++(1.3,0) coordinate (p) |- (d5.east) node[pos=.25,left,rotate=90,font=\scriptsize\itshape,anchor=south] {bound, short-lived token};
\draw[{Stealth}-{Stealth},thick,dashed,purple!70!black] (-1.3,-10.0) -- (16.8,-10.0) node[midway,above,font=\scriptsize,purple!70!black] {cross-domain trust assertion (administered by the verifying domain)};
\node[anchor=west,font=\bfseries,fill=white,inner sep=1.5pt] at (-1.5,1.55) {Layer 1 -- IoT edge holders (multiple administrative domains)};
\node[anchor=west,font=\bfseries,fill=white,inner sep=1.5pt] at (-1.5,-2.2) {Layer 2 -- SSI authentication gateway (verifier side)};
\node[anchor=west,font=\bfseries,fill=white,inner sep=1.5pt] at (-1.5,-6.4) {Layer 3 -- Blockchain verifiable data registry (Hyperledger Besu, QBFT)};
\node[anchor=west,font=\bfseries,fill=white,inner sep=1.5pt] at (-1.5,-10.55) {Layer 4 -- Federated verifiers / relying parties};
\end{tikzpicture}"""
    return build('fig2', b, 150)
def fig3():
    X = {'H': 0, 'V': 6.4, 'B': 11.4, 'R': 15.8}; dy = 0.84; y0 = -1.3
    steps = [('1', 'H', 'V', r'$did_H \,\|\, scope \,\|\, D_R$', 'A'), ('2', 'V', None, r'$n, sid, ts$ fresh; $ph = h(n\|V_{id}\|sid\|ts\|D_R\|scope\|ch)$', 'A'), ('3', 'V', 'H', r'$(n, V_{id}, sid, ts)$ challenge', 'A'),
             ('4', 'H', None, r'$(\pi, claims)\leftarrow$ ProofGen$(VC_H, ph)$;\; $\sigma_H\leftarrow$ Sign$(h(ph\|\pi\|claims))$', 'B'), ('5', 'H', 'V', r'$VP_H=(claims,\pi,issuer)$, $\sigma_H$', 'B'),
             ('6', 'V', 'B', r'resolveDIDs$(did_H, issuer)$', 'C'), ('7', 'B', 'V', r'$(hash_H, act_H, hash_I, act_I)$', 'C'), ('8', 'V', None, r'check doc hashes and status; extract $pk_H, pk_I$', 'C'),
             ('9', 'V', 'B', r'isTrusted$(D_R, D_I, issuer, schema)$', 'C'), ('10', 'B', 'V', r'trusted', 'C'), ('11', 'V', 'B', r'isRevoked$(listId, revIdx)$', 'C'), ('12', 'B', 'V', r'revoked', 'C'),
             ('13', 'V', None, r'trusted, not revoked, not expired, policy, holderKey $= h(pk_H)$', 'C'), ('14', 'V', None, r'ProofVerify$(\pi, pk_I, claims, ph)$', 'C'), ('15', 'V', None, r'Verify$(pk_H, \sigma_H, h(ph\|\pi\|claims))$', 'C'),
             ('16', 'V', None, r'features $f$ of $H$ measured by $V$; require $M(f)\le\tau$', 'D'), ('17', 'V', 'R', r'auth\_token $=$ Sign$_V(did\|aud\|scope\|exp\|sid\|cnf)$', 'D'), ('18', 'R', None, r'verify token fields; accept session', 'D'), ('19', 'V', None, r'every $\Delta$ s: re-score new flows; revoke $sid$ if $M>\tau$', 'D')]
    bands = {'A': ('blue!6', 'A: challenge'), 'B': ('violet!8', 'B: presentation'), 'C': ('green!6', 'C: registry reads and checks'), 'D': ('orange!10', 'D: behavioural gate, token')}
    b = STY + r"\begin{tikzpicture}[font=\footnotesize]" + "\n"
    for k, (lab, x) in {'H': ('H\\\\(Holder)', 0), 'V': ('V\\\\(SSI gateway)', 6.4), 'B': ('B\\\\(Blockchain VDR)', 11.4), 'R': ('R\\\\(Relying party)', 15.8)}.items():
        b += rf"\node[box,fill=blue!10,minimum width=2.9cm,font=\footnotesize\bfseries] (h{k}) at ({X[k]},0) {{{lab}}};" + "\n"
    n = len(steps); ybot = y0 - dy * n
    b += r"\begin{scope}[on background layer]" + "\n"
    for ph in 'ABCD':
        idx = [i for i, s in enumerate(steps) if s[4] == ph]; ya = y0 + dy * 0.5 - idx[0] * dy; yb = y0 + dy * 0.5 - (idx[-1] + 1) * dy
        b += rf"\fill[{bands[ph][0]}] (-2.0,{ya}) rectangle (18.6,{yb}); \node[anchor=north east,font=\scriptsize\itshape,gray!70!black] at (18.5,{ya-0.03}) {{{bands[ph][1]}}};" + "\n"
    b += "\\end{scope}\n"
    for k in X: b += rf"\draw[thick] ({X[k]},-0.55) -- ({X[k]},{ybot-0.1});" + "\n"
    for i, (num, a, c, t, ph) in enumerate(steps):
        y = y0 - i * dy
        if c is None:
            if a == 'R': b += rf"\node[box,fill=yellow!25,anchor=east,font=\scriptsize] at ({X['R']+0.9},{y}) {{{num}. {t}}};" + "\n"
            else: b += rf"\node[box,fill=yellow!25,anchor=west,font=\scriptsize] at ({X[a]+0.45},{y}) {{{num}. {t}}};" + "\n"
        else:
            sty = 'res' if num in ('7', '10', '12') else 'req'
            b += rf"\draw[{sty}] ({X[a]},{y}) -- ({X[c]},{y}) node[midway,above=-1pt,font=\scriptsize] {{{num}. {t}}};" + "\n"
    b += rf"\node[anchor=west,font=\scriptsize] at (-2.0,{ybot-0.55}) {{\textcolor{{blue!70!black}}{{$\longrightarrow$}} request \quad \textcolor{{green!50!black}}{{- - $\rightarrow$}} response \quad \colorbox{{yellow!25}}{{box}} local operation}};" + "\n\\end{tikzpicture}"
    return build('fig3', b, 150)
def fig7():
    rows = [('Phase 1: Data and preprocessing', ['RT-IoT2022\\\\(UCI repository)', 'Clean + one-hot encode\\\\(fitted inside folds)', 'Stratified 75/25 split\\\\(12-class strata)', 'Binary label:\\\\Authorized = 3 normal\\\\classes'], 'blue!10'),
            ('Phase 2: Framework design and smart contracts', ['Define protocol\\\\(19 steps)', 'Solidity contracts\\\\(3, one source)', 'Deploy on\\\\Besu QBFT', 'Measure gas, latency,\\\\throughput'], 'violet!10'),
            ('Phase 3: Gateway classifier', ['Feature set\\\\(80 numeric + 2 categorical)', 'Train 6 models on the\\\\identical training split', '5-fold CV inside the\\\\training split', 'Select $\\tau$ on training\\\\out-of-fold scores'], 'green!14'),
            ('Phase 4: Evaluation', ['Held-out test metrics\\\\+ paired tests', 'Harder settings\\\\(family, block, session)', 'Cross-dataset transfer\\\\(CIC-IDS2017)', 'Protocol tests +\\\\integrated gateway test'], 'orange!16')]
    b = STY + r"\begin{tikzpicture}[font=\small]" + "\n" + r"\node[font=\Large\bfseries] at (6.3,2.3) {Research Methodology Pipeline};" + "\n"
    for r, (t, bx, col) in enumerate(rows):
        y = -r * 3.6
        b += rf"\node[anchor=west,font=\bfseries] at (-1.9,{y+1.0}) {{{t}}};" + "\n"
        for i, s in enumerate(bx): b += rf"\node[box,fill={col},minimum width=3.7cm,minimum height=1.9cm,font=\footnotesize] (p{r}{i}) at ({i*4.2},{y-0.4}) {{{s}}};" + "\n"
        for i in range(3): b += rf"\draw[-{{Stealth}},thick] (p{r}{i}.east) -- (p{r}{i+1}.west);" + "\n"
    for r in range(3): b += rf"\draw[-{{Stealth}},thick] (p{r}3.south) -- ++(0,-0.6) -| ($(p{r+1}0.west)+(-0.45,0)$) -- (p{r+1}0.west);" + "\n"
    b += "\\end{tikzpicture}"
    return build('fig7', b, 170)
if __name__ == '__main__':
    for w in (sys.argv[1:] or ['1', '2', '3', '7']): globals()[f'fig{w}']()
