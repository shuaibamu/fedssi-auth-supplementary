import sys, json, math; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import numpy as np
from tikzlib import *
from common import load, load_rt, RES
from scipy.cluster.hierarchy import linkage, leaves_list
from sklearn.metrics import roc_curve
T = load('test_results_full.json'); S = load('stats_tests_full.json'); TC = load('threshold_calibration_seeds.json'); sweep = load('threshold_sweep_oof.json'); M = load('multiclass_and_family_results.json')
KS = ['LR', 'DT', 'kNN', 'SVM-RBF', 'GB', 'RF']; NM = {'LR': 'Logistic Regression', 'DT': 'Decision Tree', 'kNN': 'k-NN', 'SVM-RBF': 'SVM (RBF)', 'GB': 'Gradient Boosting', 'RF': 'Random Forest'}; COL = {'LR': 'cLR', 'DT': 'cDT', 'kNN': 'ckNN', 'SVM-RBF': 'cSVM', 'GB': 'cGB', 'RF': 'cRF'}
co = lambda xs, ys: ' '.join(f'({x:.6g},{y:.6g})' for x, y in zip(xs, ys))
def fig4():
    v = [T[k]['predict_ms_per_1000_flows'] for k in KS]; ymin = 10 ** math.floor(math.log10(min(v) / 2))
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=15cm,height=7.2cm,ymode=log,ymin={ymin},ymax={max(v)*4},ylabel={{Inference time (ms per 1,000 flows, log scale)}},
 title={{Per-classifier inference latency (single core, preprocessing included)}},xtick={{0,...,5}},xticklabels={{{','.join(NM[k] for k in KS)}}},x tick label style={{rotate=15,anchor=east}},enlarge x limits=0.1,ymajorgrids,grid style={{black!15}}]
"""
    for i, k in enumerate(KS): b += rf"\addplot[ybar,bar width=1.5cm,bar shift=0pt,fill={COL[k]},draw=black!70,nodes near coords,nodes near coords style={{font=\scriptsize}},/pgf/number format/.cd,fixed,precision=1] coordinates {{({i},{v[i]:.5g})}};" + "\n"
    return build('fig4', b + r"\end{axis}\end{tikzpicture}", 200)
def fig5():
    imp = load('rf_feature_importance.json'); it = sorted(imp.items(), key=lambda kv: -kv[1])[:12]; names = [tx(k.replace('num__', '').replace('cat__', '')) for k, _ in it]
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=12.5cm,height=8cm,xbar,xmin=0,symbolic y coords={{{','.join(names)}}},ytick=data,y dir=reverse,xlabel={{Gini importance (Random Forest, binary task, full training split)}},
 title={{Top-12 Random-Forest feature importances}},xmajorgrids,grid style={{black!15}},scaled x ticks=false,xticklabel style={{/pgf/number format/fixed,/pgf/number format/precision=2}},enlarge y limits=0.06,y tick label style={{font=\footnotesize}}]
\addplot[fill=cRF,draw=black!70,bar width=0.45cm] coordinates {{{' '.join(f'({v:.6g},{n})' for (k, v), n in zip(it, names))}}};
\end{{axis}}\end{{tikzpicture}}"""
    return build('fig5', b, 200)
def fig6():
    df, feat, num, y12, y, c = load_rt(); tr = np.load(f'{RES}/idx_train.npy'); C = df.iloc[tr][num].corr().abs().fillna(0).values
    D = 1 - C; iu = np.triu_indices(len(num), 1); o = leaves_list(linkage(D[iu], 'average')); Cm = C[np.ix_(o, o)]; n = len(o)
    with open(f'{TEX}/fig6_data.csv', 'w') as f:
        f.write('x,y,c\n')
        for i in range(n):
            for j in range(n): f.write(f'{j},{i},{Cm[i, j]:.3f}\n')
    fs = r"\fontsize{3.4}{3.4}\selectfont"
    nodes = ''.join(rf"\node[anchor=east,font={fs}] at (axis cs:-0.7,{k}) {{{tx(num[i])}}}; \node[anchor=east,rotate=90,font={fs}] at (axis cs:{k},{n-0.2}) {{{tx(num[i])}}};" + "\n" for k, i in enumerate(o))
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=14cm,height=14cm,clip=false,enlargelimits=false,axis on top,y dir=reverse,colorbar,colormap={{cw}}{{rgb255=(59,76,192) rgb255=(221,221,221) rgb255=(180,4,38)}},point meta min=0,point meta max=1,
 colorbar style={{ylabel={{$|$Pearson correlation$|$}},width=.35cm,ytick={{0,.2,.4,.6,.8,1}}}},xtick=\empty,ytick=\empty,tick style={{draw=none}},
 title={{Feature redundancy of RT-IoT2022 ({n} numeric features, absolute Pearson correlation, hierarchically clustered; training split)}},title style={{yshift=2pt}}]
\addplot[matrix plot*,point meta=explicit,mesh/rows={n},mesh/cols={n}] table[x=x,y=y,meta=c,col sep=comma]{{fig6_data.csv}};
{nodes}\end{{axis}}\end{{tikzpicture}}"""
    return build('fig6', b, 200)
def fig8():
    z = np.load(f'{RES}/test_scores_full.npz'); y = z['y']; tau = TC['tau_selected_on_train_oof']; grid = np.logspace(-4, 0, 140)
    W, H = 7.4, 5.4; pos = {'a': (0, 0), 'b': (9.2, 0), 'c': (0, -8.0), 'd': (9.2, -8.0)}
    def ax(k, opts): x, yy = pos[k]; return rf"\begin{{axis}}[width={W}cm,height={H}cm,at={{({x}cm,{yy}cm)}},anchor=north west,{opts}]" + "\n"
    b = r"\begin{tikzpicture}" + "\n" + ax('a', r"xmode=log,xmin=1e-4,xmax=1,ymin=0.9,ymax=1.003,xlabel={False-positive rate (log scale)},ylabel={True-positive rate},title={(a) ROC curves, held-out test split},legend pos=south east,legend cell align=left,grid=both,grid style={black!12}")
    for k in KS:
        fpr, tpr, _ = roc_curve(y, z[f'score_{k}']); t = np.interp(grid, fpr, tpr); b += rf"\addplot[{COL[k]},line width=1pt] coordinates {{{co(grid, t)}}}; \addlegendentry{{{NM[k]} (AUC {T[k]['roc_auc']:.4f})}}" + "\n"
    b += "\\end{axis}\n" + ax('b', r"xmin=0,xmax=1,ymin=-0.02,ymax=1.02,xlabel={Threshold $\tau$ (flag if score $>\tau$)},title={(b) Threshold trade-off, training out-of-fold scores},legend style={at={(0.03,0.5)},anchor=west},grid=both,grid style={black!12}")
    tt = [r['tau'] for r in sweep]
    for key, lab, c in [('precision', 'Precision', 'cBlue'), ('recall', 'Recall', 'cGreen'), ('fpr', 'False-rejection rate', 'cRed'), ('macro_f1', 'Macro-F1', 'black')]:
        b += rf"\addplot[{c},line width=1pt] coordinates {{{co(tt, [r[key] for r in sweep])}}}; \addlegendentry{{{lab}}}" + "\n"
    b += rf"\draw[purple,dashed] (axis cs:{tau},-0.02) -- (axis cs:{tau},1.02); \node[purple,anchor=west,font=\scriptsize,align=left] at (axis cs:{tau+0.02},0.3) {{selected\\$\tau={tau:.2f}$}};" + "\n\\end{axis}\n"
    rel = TC['calibration']['test_raw']['reliability']
    b += ax('c', rf"xmin=0,xmax=1,ymin=0,ymax=1,xlabel={{Mean predicted attack probability}},ylabel={{Observed attack fraction}},title={{(c) Reliability (10 bins): Brier {TC['calibration']['test_raw']['brier']:.4f}, ECE {TC['calibration']['test_raw']['ece10']:.4f}}},legend pos=north west,grid=both,grid style={{black!12}}")
    b += rf"\addplot[black,dashed] coordinates {{(0,0)(1,1)}}; \addplot[cRed,mark=*,line width=1pt] coordinates {{{co([r[0] for r in rel], [r[1] for r in rel])}}}; \addlegendentry{{Random Forest score (test)}}" + "\n\\end{axis}\n"
    bins = np.linspace(0, 1, 41); s = z['score_RF']; c0, _ = np.histogram(s[y == 0], bins); c1, _ = np.histogram(s[y == 1], bins); fix = lambda c: np.where(c == 0, 0.5, c)
    b += ax('d', r"ymode=log,ymin=1,xmin=0,xmax=1,xlabel={Random Forest attack score},ylabel={Flows (log scale)},title={(d) Score distribution, held-out test split},legend style={at={(0.5,0.97)},anchor=north},ymajorgrids,grid style={black!12}")
    for c, col, lab in [(c0, 'cBlue', 'Authorized (benign)'), (c1, 'cRed', 'Unauthorized (attack)')]:
        b += rf"\addplot[ybar interval,fill={col},fill opacity=.6,draw={col}!70!black,line width=.2pt] coordinates {{{co(bins[:-1], fix(c))} ({bins[-1]},0.5)}}; \addlegendentry{{{lab}}}" + "\n"
    b += rf"\draw[purple,dashed] (axis cs:{tau},1) -- (axis cs:{tau},1e5);" + "\n\\end{axis}\n\\end{tikzpicture}"
    return build('fig8', b, 190)
def fig9():
    cv = S['cv_summary']; b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=15cm,height=7.2cm,clip=false,ymin=0.92,ymax=1.0,ylabel={{Macro-F1 (two binary classes)}},xtick={{0,...,5}},xticklabels={{{','.join(NM[k] for k in KS)}}},x tick label style={{rotate=15,anchor=east}},enlarge x limits=0.1,
 title={{Binary gateway task: same full training split for every model\\(CV intervals are approximate: folds overlap and are not independent)}},title style={{align=center,font=\small\bfseries}},ymajorgrids,grid style={{black!15}},]
"""
    for i, k in enumerate(KS): b += rf"\addplot[ybar,bar width=1.5cm,bar shift=0pt,fill={COL[k]},draw=black!70,error bars/.cd,y dir=both,y explicit,error bar style={{black,line width=.8pt}}] coordinates {{({i},{cv[k]['mean']:.6f}) +- (0,{cv[k]['ci95_half']:.6f})}};" + "\n"
    b += rf"\addplot[only marks,mark=diamond*,mark size=3.2pt,black] coordinates {{{co(range(6), [T[k]['macro_f1'] for k in KS])}}};" + "\n"
    b += r"\node[anchor=north west,font=\footnotesize] at (rel axis cs:0.02,-0.30) {\textcolor{gray!60}{\rule{3.5mm}{2mm}}\ 5-fold CV macro-F1 (mean, approx.\ 95\% CI) \qquad $\blacklozenge$ Held-out test macro-F1};" + "\n"
    return build('fig9', b + r"\end{axis}\end{tikzpicture}", 200)
def fig10():
    labs = M['labels']; pc = M['per_class_multiclass']; bg = M['binary_gateway_by_class']; n = len(labs)
    xl = ','.join('{' + tx(l) + r'\\{\tiny (n=' + f"{pc[l]['support']})" + '}}' for l in labs)
    xl2 = ','.join('{' + tx(l) + r'\\{\tiny (' + f"{bg[l]['flagged']}/{bg[l]['n']})" + '}}' for l in labs)
    sty = r"x tick label style={rotate=40,anchor=east,align=right,font=\scriptsize},enlarge x limits=0.04,ymajorgrids,grid style={black!15}"
    b = r"\begin{tikzpicture}" + "\n" + rf"""\begin{{axis}}[at={{(0,0)}},anchor=north west,width=17cm,height=6cm,ybar,bar width=4.6pt,ymin=0.75,ymax=1.01,xtick={{0,...,{n-1}}},xticklabels={{{xl}}},{sty},
 title={{(a) Separately trained 12-class Random Forest: per-class precision, recall and F1 (test split)}},legend pos=outer north east]
"""
    for key, col, lab in [('precision', 'cBlue', 'Precision'), ('recall', 'cGreen', 'Recall'), ('f1', 'cOrange', 'F1')]: b += rf"\addplot[fill={col},draw={col}!70!black] coordinates {{{co(range(n), [pc[l][key] for l in labs])}}}; \addlegendentry{{{lab}}}" + "\n"
    att = [i for i, l in enumerate(labs) if bg[l]['kind'] == 'attack']; nor = [i for i, l in enumerate(labs) if bg[l]['kind'] != 'attack']
    b += "\\end{axis}\n" + rf"""\begin{{axis}}[at={{(0,-10.2cm)}},anchor=north west,width=17cm,height=6cm,ybar,bar width=7pt,ymode=log,log origin=infty,ymin=1e-4,ymax=1.6,xtick={{0,...,{n-1}}},xticklabels={{{xl2}}},{sty},ylabel={{Fraction flagged (log scale)}},
 title={{(b) Binary gateway: fraction flagged per original class}},legend pos=outer north east,legend cell align=left]
\addplot[fill=cRed,draw=black!60,bar shift=0pt] coordinates {{{co(att, [max(bg[labs[i]]['rate'], 1e-4) for i in att])}}}; \addlegendentry{{attack classes: recall}}
\addplot[fill=cBlue,draw=black!60,bar shift=0pt] coordinates {{{co(nor, [max(bg[labs[i]]['rate'], 1e-4) for i in nor])}}}; \addlegendentry{{normal classes: false-rejection rate}}
\end{{axis}}
\end{{tikzpicture}}"""
    return build('fig10', b, 170)
def fig11():
    cmb = np.array(M['cm_binary_gateway']); cm12 = np.array(M['cm12']); labs = M['labels']; n = 12
    def col(v, mx): return int(round(100 * math.log10(v + 1) / math.log10(mx + 1)))
    b = r"\begin{tikzpicture}[font=\footnotesize]" + "\n" + r"\node[font=\small\bfseries] at (2.6,2.2) {(a) Binary gateway (RF, $\tau=0.50$)};" + "\n"; mx = cmb.max(); cs = 2.5
    for i in range(2):
        for j in range(2):
            p = col(cmb[i, j], mx); b += rf"\fill[cBlue!{p}!white] ({j*cs},{-i*cs}) rectangle ++({cs},{-cs}); \draw[black!60] ({j*cs},{-i*cs}) rectangle ++({cs},{-cs}); \node[{'white' if p>55 else 'black'},font=\large] at ({j*cs+cs/2},{-i*cs-cs/2}) {{{cmb[i,j]:,}}};" + "\n"
    b += rf"\node[align=center] at ({cs/2},-{2*cs+0.6}) {{Admitted\\(pred.\ Authorized)}}; \node[align=center] at ({cs*1.5},-{2*cs+0.6}) {{Blocked\\(pred.\ Unauthorized)}}; \node[align=right,anchor=east] at (-0.15,-{cs/2}) {{Authorized\\(benign)}}; \node[align=right,anchor=east] at (-0.15,-{cs*1.5}) {{Unauthorized\\(attack)}};" + "\n"
    ox = 11.0; c0 = 0.62; mx2 = cm12.max(); b += rf"\node[font=\small\bfseries] at ({ox+n*c0/2},2.2) {{(b) Separately trained 12-class model (counts)}};" + "\n"
    for i in range(n):
        for j in range(n):
            v = cm12[i, j]; p = col(v, mx2); b += rf"\fill[cBlue!{p}!white] ({ox+j*c0},{-i*c0}) rectangle ++({c0},{-c0}); \draw[black!15,line width=.2pt] ({ox+j*c0},{-i*c0}) rectangle ++({c0},{-c0});"
            if v: b += rf"\node[{'white' if p>55 else 'black'},font=\fontsize{{5}}{{5}}\selectfont] at ({ox+j*c0+c0/2},{-i*c0-c0/2}) {{{v}}};"
            b += "\n"
    for i, l in enumerate(labs): b += rf"\node[anchor=east,font=\fontsize{{6}}{{6}}\selectfont] at ({ox-0.08},{-i*c0-c0/2}) {{{tx(l)}}}; \node[anchor=east,rotate=60,font=\fontsize{{6}}{{6}}\selectfont] at ({ox+i*c0+c0/2+0.12},-{n*c0+0.08}) {{{tx(l)}}};" + "\n"
    b += rf"\draw[black!60] ({ox},0) rectangle ({ox+n*c0},{-n*c0});" + "\n\\end{tikzpicture}"
    return build('fig11', b, 200)
def fig12():
    A = load('ablation.json'); keys = list(A); short = []
    for k in keys:
        if k.startswith('Full'): short.append(r'Full model\\(82 features,\\100 trees)')
        elif 'categorical' in k: short.append(r'$-$ categorical\\features')
        elif 'temporal' in k: short.append(r'$-$ temporal\\features (' + k.split('(')[1].split(':')[0] + ')')
        elif 'port' in k: short.append(r'$-$ port numbers')
        elif 'Reduced' in k: short.append(r'Reduced ensemble\\(50 trees)')
        else: short.append(r'No behavioural gate\\(baseline under\\the stated assumption)')
    n = len(keys); w = 0.34
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=16cm,height=7cm,ybar,bar width={w}cm,ymin=0,ymax=1.1,ylabel={{Score}},xtick={{0,...,{n-1}}},xticklabels={{{','.join('{'+s+'}' for s in short)}}},x tick label style={{align=center,font=\scriptsize}},enlarge x limits=0.1,
 title={{Ablation on the held-out test split (hatched bars: baseline under an explicit assumption)}},ymajorgrids,grid style={{black!15}},legend pos=north east,legend cell align=left]
\addplot[fill=cBlue,draw=black!70,bar shift=-{w/2}cm] coordinates {{{co(range(n-1), [A[k]['macro_f1'] for k in keys[:-1]])}}}; \addlegendentry{{Macro-F1 (two classes)}}
\addplot[fill=cOrange,draw=black!70,bar shift={w/2}cm] coordinates {{{co(range(n-1), [A[k]['f1_attack'] for k in keys[:-1]])}}}; \addlegendentry{{F1, Unauthorized (positive class)}}
\addplot[pattern=north east lines,pattern color=cBlue,draw=black!70,bar shift=-{w/2}cm] coordinates {{({n-1},{A[keys[-1]]['macro_f1']:.5f})}};
\addplot[pattern=north east lines,pattern color=cOrange,draw=black!70,bar shift={w/2}cm] coordinates {{({n-1},{max(A[keys[-1]]['f1_attack'],0.004):.5f})}};
"""
    return build('fig12', b + r"\end{axis}\end{tikzpicture}", 200)
def fig13():
    B = load('bench_live.json'); fields = [('throughput_tps', 'Throughput (confirmed tx/s)'), ('latency_median_s', 'Median confirmation latency (s)'), ('host_cpu_busy_fraction', 'Host CPU busy fraction (1 vCPU)')]
    b = r"\begin{tikzpicture}" + "\n"
    for i, (fld, lab) in enumerate(fields):
        b += rf"""\begin{{axis}}[at={{({i*6.9}cm,0)}},anchor=north west,width=5.8cm,height=5.4cm,xmode=log,xtick={{10,50,100}},xticklabels={{10,50,100}},minor x tick num=0,xlabel={{Concurrently enrolling devices}},ylabel={{{lab}}},ymajorgrids,grid style={{black!15}},{'ymin=0,ymax=1.05,' if 'cpu' in fld else 'ymin=0,'}legend pos=north west,legend cell align=left]
"""
        for key, col, nm in [('n4', 'cBlue', '4 validators'), ('n7', 'cRed', '7 validators')]:
            runs = B[key]['runs']; loads = sorted(set(r['load'] for r in runs)); mean = [np.mean([r[fld] for r in runs if r['load'] == L]) for L in loads]; sd = [np.std([r[fld] for r in runs if r['load'] == L], ddof=1) for L in loads]
            b += rf"\addplot[{col},mark=*,line width=1pt,error bars/.cd,y dir=both,y explicit] coordinates {{{' '.join(f'({L},{m:.5g}) +- (0,{s:.5g})' for L, m, s in zip(loads, mean, sd))}}};" + (rf" \addlegendentry{{{nm}}}" if i == 0 else '') + "\n"
            b += rf"\addplot[{col},only marks,mark=*,mark size=1pt,opacity=.35,forget plot] coordinates {{{' '.join(f'({r['load']},{r[fld]:.5g})' for r in runs)}}};" + "\n"
        b += "\\end{axis}\n"
    b += r"\node[font=\scriptsize\itshape,anchor=south west] at (0,0.7) {Measured registerDID benchmark, one network at a time (mean $\pm$ s.d. of 3 runs; dots: runs); single shared host};" + "\n\\end{tikzpicture}"
    return build('fig13', b, 190)
if __name__ == '__main__':
    for w in (sys.argv[1:] or ['4', '5', '6', '8', '9', '10', '11', '12', '13']): globals()[f'fig{w}']()
