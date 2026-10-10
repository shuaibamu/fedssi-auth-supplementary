import sys, json, math; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import numpy as np
from tikzlib2 import *
from common import load, load_rt, RES
from scipy.cluster.hierarchy import linkage, leaves_list
from sklearn.metrics import roc_curve
T = load('test_results_full.json'); S = load('stats_tests_full.json'); TC = load('threshold_calibration_seeds.json'); sweep = load('threshold_sweep_oof.json'); M = load('multiclass_and_family_results.json')
KS = ['LR', 'DT', 'kNN', 'SVM-RBF', 'GB', 'RF']; NM = {'LR': 'Logistic Regression', 'DT': 'Decision Tree', 'kNN': 'k-NN', 'SVM-RBF': 'SVM (RBF)', 'GB': 'Gradient Boosting', 'RF': 'Random Forest (Ours)'}
TB = {'LR': 'tbBlue', 'DT': 'tbOrange', 'kNN': 'tbGreen', 'SVM-RBF': 'tbRed', 'GB': 'tbPurple', 'RF': 'tbBrown'}
co = lambda xs, ys: ' '.join(f'({x:.6g},{y:.6g})' for x, y in zip(xs, ys))
FR = r"axis line style={black},ymajorgrids,xmajorgrids"
def fig4():
    v = {k: T[k]['predict_ms_per_1000_flows'] for k in KS}; order = sorted(KS, key=lambda k: v[k]); top = order[-1]; n = len(order)
    yl = ','.join('{' + tx(NM[k]) + '}' for k in order)
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=14.5cm,height=7.4cm,xbar,xmode=log,log origin=infty,xmin=0.1,xmax={max(v.values())*9:.0f},ymin=-0.6,ymax={n-0.4},ytick={{0,...,{n-1}}},yticklabels={{{yl}}},y tick label style={{font=\small}},
 xlabel={{Inference latency per flow (microseconds, log scale)}},xmajorgrids,xminorgrids,grid style={{dashed,black!15}},minor grid style={{dashed,black!10}}]
"""
    for i, k in enumerate(order):
        col = 'kRed' if k == top else ('barGreen' if k == 'RF' else 'lightBlue')
        b += rf"\addplot[xbar,bar shift=0pt,fill={col},draw=black!55,bar width=0.62cm,point meta=explicit symbolic,nodes near coords,nodes near coords style={{font=\footnotesize,anchor=west}}] coordinates {{({v[k]:.4g},{i}) [{v[k]:.2f}\,$\mu$s]}};" + "\n"
    return build('fig4', b + r"\end{axis}\end{tikzpicture}", 220)
def fig5():
    imp = load('rf_feature_importance.json'); it = sorted(imp.items(), key=lambda kv: -kv[1])[:12]; names = [tx(k.replace('num__', '').replace('cat__', '')) for k, _ in it]
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=13cm,height=8.2cm,xbar,xmin=0,symbolic y coords={{{','.join(names)}}},ytick=data,y dir=reverse,xlabel={{Gini importance}},xmajorgrids,grid style={{dotted,black!30}},scaled x ticks=false,
 xticklabel style={{/pgf/number format/fixed,/pgf/number format/precision=2}},enlarge y limits=0.05,y tick label style={{font=\small}}]
\addplot[fill=darkGreen,draw=black!60,bar width=0.5cm] coordinates {{{' '.join(f'({v:.6g},{n})' for (k, v), n in zip(it, names))}}};
\end{{axis}}\end{{tikzpicture}}"""
    return build('fig5', b, 220)
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
 colorbar style={{ylabel={{$|$Pearson correlation$|$}},width=.35cm,ytick={{0,.2,.4,.6,.8,1}}}},xtick=\empty,ytick=\empty,tick style={{draw=none}},title={{\begin{{tabular}}{{c}}Feature redundancy structure of RT-IoT2022\\(absolute Pearson correlation, hierarchically clustered)\end{{tabular}}}},title style={{font=\normalsize,yshift=2pt}}]
\addplot[matrix plot*,point meta=explicit,mesh/rows={n},mesh/cols={n}] table[x=x,y=y,meta=c,col sep=comma]{{fig6_data.csv}};
{nodes}\end{{axis}}\end{{tikzpicture}}"""
    return build('fig6', b, 200)
def fig8():
    z = np.load(f'{RES}/test_scores_full.npz'); y = z['y']; tau = TC['tau_selected_on_train_oof']; g = np.unique(np.r_[0, np.logspace(-5, 0, 260), np.linspace(0, 1, 60)]); W, H = 5.9, 5.3
    pos = {'a': (0, 0), 'b': (7.9, 0), 'c': (15.8, 0), 'd': (0, -8.0), 'e': (7.9, -8.0)}
    def ax(k, opts): x, yy = pos[k]; return rf"\begin{{axis}}[width={W}cm,height={H}cm,at={{({x}cm,{yy}cm)}},anchor=north west,{opts}]" + "\n"
    curves = {}
    for k in KS: fpr, tpr, _ = roc_curve(y, z[f'score_{k}']); curves[k] = np.interp(g, fpr, tpr)
    b = r"\begin{tikzpicture}" + "\n" + ax('a', r"xmin=0,xmax=1,ymin=0,ymax=1.02,xlabel={False Positive Rate},ylabel={True Positive Rate},title={(a) ROC curves},grid=both,legend pos=south east,legend cell align=left,legend style={font=\tiny}")
    b += r"\addplot[gray,dashed,line width=1pt,forget plot] coordinates {(0,0)(1,1)};" + "\n"
    for k in KS: b += rf"\addplot[{TB[k]},line width=1.2pt] coordinates {{{co(g, curves[k])}}}; \addlegendentry{{{tx(NM[k])} (AUC={T[k]['roc_auc']:.3f})}}" + "\n"
    b += "\\end{axis}\n" + ax('b', r"xmode=log,xmin=1e-4,xmax=1,ymin=0.9,ymax=1.003,xlabel={False Positive Rate (log scale)},ylabel={True Positive Rate},title={(b) ROC curves, detail},grid=both")
    for k in KS: b += rf"\addplot[{TB[k]},line width=1.2pt] coordinates {{{co(np.maximum(g, 1e-5), curves[k])}}};" + "\n"
    b += "\\end{axis}\n" + ax('c', r"xmin=0,xmax=1,ymin=-0.02,ymax=1.02,xlabel={Threshold $\tau$ (flag if score $>\tau$)},title={(c) Threshold trade-off (training OOF)},grid=both,legend style={at={(0.03,0.5)},anchor=west,font=\tiny},legend cell align=left")
    tt = [r['tau'] for r in sweep]
    for key, lab, c in [('precision', 'Precision', 'tbBlue'), ('recall', 'Recall', 'tbGreen'), ('fpr', 'False-rejection rate', 'tbRed'), ('macro_f1', 'Macro-F1', 'black')]: b += rf"\addplot[{c},line width=1.2pt] coordinates {{{co(tt, [r[key] for r in sweep])}}}; \addlegendentry{{{lab}}}" + "\n"
    b += rf"\draw[purple,dashed] (axis cs:{tau},-0.02) -- (axis cs:{tau},1.02); \node[purple,anchor=west,font=\scriptsize,align=left] at (axis cs:{tau+0.02},0.3) {{selected\\$\tau={tau:.2f}$}};" + "\n\\end{axis}\n"
    rel = TC['calibration']['test_raw']['reliability']
    b += ax('d', rf"xmin=0,xmax=1,ymin=0,ymax=1,xlabel={{Mean predicted attack probability}},ylabel={{Observed attack fraction}},title={{(d) Reliability: Brier {TC['calibration']['test_raw']['brier']:.4f}, ECE {TC['calibration']['test_raw']['ece10']:.4f}}},grid=both")
    b += rf"\addplot[gray,dashed,line width=1pt] coordinates {{(0,0)(1,1)}}; \addplot[tbRed,mark=*,line width=1.2pt,mark size=1.8pt] coordinates {{{co([r[0] for r in rel], [r[1] for r in rel])}}};" + "\n\\end{axis}\n"
    bins = np.linspace(0, 1, 41); s = z['score_RF']; c0, _ = np.histogram(s[y == 0], bins); c1, _ = np.histogram(s[y == 1], bins); fix = lambda c: np.where(c == 0, 0.5, c)
    b += ax('e', r"ymode=log,ymin=1,xmin=0,xmax=1,xlabel={Random Forest attack score},ylabel={Flows (log scale)},title={(e) Score distribution (test)},ymajorgrids,legend style={at={(0.5,0.97)},anchor=north,font=\tiny}")
    for c, col, lab in [(c0, 'tbBlue', 'Authorized (benign)'), (c1, 'tbRed', 'Unauthorized (attack)')]: b += rf"\addplot[ybar interval,fill={col},fill opacity=.6,draw={col}!70!black,line width=.2pt] coordinates {{{co(bins[:-1], fix(c))} ({bins[-1]},0.5)}}; \addlegendentry{{{lab}}}" + "\n"
    b += rf"\draw[purple,dashed] (axis cs:{tau},1) -- (axis cs:{tau},1e5);" + "\n\\end{axis}\n\\end{tikzpicture}"
    return build('fig8', b, 190)
def fig9():
    xl = ','.join(tx(NM[k]) for k in KS); cv = S['cv_summary']
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=15.5cm,height=7cm,ybar,bar width=0.52cm,ymin=0.9,ymax=1.005,ylabel={{Score}},xtick={{0,...,5}},xticklabels={{{xl}}},x tick label style={{rotate=15,anchor=east,font=\scriptsize}},enlarge x limits=0.1,
 title={{Gateway classifier performance on RT-IoT2022 (held-out test, with cross-validation 95\% CI)}},ymajorgrids,legend style={{at={{(0.5,-0.3)}},anchor=north,font=\scriptsize,legend columns=4}},legend cell align=left]
\addplot[fill=accB,draw=black!40] coordinates {{{co(range(6), [T[k]['accuracy'] for k in KS])}}}; \addlegendentry{{Accuracy}}
\addplot[fill=f1O,draw=black!40] coordinates {{{co(range(6), [T[k]['f1_attack'] for k in KS])}}}; \addlegendentry{{F1 (Unauthorized)}}
\addplot[fill=aucG,draw=black!40] coordinates {{{co(range(6), [T[k]['roc_auc'] for k in KS])}}}; \addlegendentry{{ROC-AUC}}
\addplot[only marks,mark=x,mark size=2.6pt,line width=1pt,black,error bars/.cd,y dir=both,y explicit,error bar style={{line width=.8pt}}] coordinates {{{' '.join(f'({i},{cv[k]["mean"]:.6f}) +- (0,{cv[k]["ci95_half"]:.6f})' for i, k in enumerate(KS))}}}; \addlegendentry{{5-fold CV macro-F1, mean $\pm$ 95\% CI}}
"""
    return build('fig9', b + r"\end{axis}\end{tikzpicture}", 200)
def fig10():
    labs = sorted(M['labels']); pc = M['per_class_multiclass']; bg = M['binary_gateway_by_class']; n = len(labs); fs = r"\fontsize{7}{8}\selectfont"
    with open(f'{TEX}/fig10_data.csv', 'w') as f:
        f.write('x,y,c\n')
        for i, l in enumerate(labs):
            for j, k in enumerate(('precision', 'recall', 'f1')): f.write(f'{j},{i},{pc[l][k]:.4f}\n')
    nodes = ''
    for i, l in enumerate(labs):
        nodes += rf"\node[anchor=east,font=\small] at (axis cs:-0.55,{i}) {{{tx(l)}}};" + "\n"
        for j, k in enumerate(('precision', 'recall', 'f1')): v = pc[l][k]; nodes += rf"\node[font=\small,text={'white' if v > 0.88 else 'black'}] at (axis cs:{j},{i}) {{{v:.3f}}};" + "\n"
        r = bg[l]['rate']; att = bg[l]['kind'] == 'attack'; colr = f"red!{int(round(100*r))}!white" if att else f"blue!{max(int(round(100*min(1,r*20))),4)}!white"
        nodes += rf"\fill[{colr}] (axis cs:3.55,{i-0.5}) rectangle (axis cs:4.95,{i+0.5}); \draw[white,line width=1pt] (axis cs:3.55,{i-0.5}) rectangle (axis cs:4.95,{i+0.5}); \node[font=\scriptsize,text={'white' if att and r > 0.6 else 'black'}] at (axis cs:4.25,{i}) {{{100*r:.2f}\%}};" + "\n"
    nodes += r"\node[font=\small,anchor=south] at (axis cs:4.25,-0.62) {Binary gate:\\[-2pt]fraction flagged};" + "\n" + r"\node[font=\scriptsize,anchor=north,align=center,text width=3.4cm] at (axis cs:4.25,12.2) {red: attack recall\\blue: benign false-rejection rate (shade x20)};"
    nodes += "\n" + rf"\node[font=\small,anchor=north] at (axis cs:0,11.6) {{Precision}}; \node[font=\small,anchor=north] at (axis cs:1,11.6) {{Recall}}; \node[font=\small,anchor=north] at (axis cs:2,11.6) {{F1}}; \node[font=\small,anchor=north] at (axis cs:1,12.5) {{Metric}}; \node[font=\small,rotate=90,anchor=south] at (axis cs:-3.6,5.5) {{Attack class}};"
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=7.4cm,height=10.2cm,clip=false,enlargelimits=false,axis on top,y dir=reverse,colorbar horizontal,colormap={{rdylgn}}{{rgb255(0cm)=(165,0,38) rgb255(2.5cm)=(253,174,97) rgb255(5cm)=(255,255,191) rgb255(7.5cm)=(166,217,106) rgb255(10cm)=(0,104,55)}},point meta min=0,point meta max=1,
 colorbar style={{xlabel={{Score}},at={{(0.5,-0.27)}},anchor=north,width=7.4cm,height=.28cm,xtick={{0,.2,.4,.6,.8,1}}}},xtick=\empty,ytick=\empty,tick style={{draw=none}},title={{\begin{{tabular}}{{c}}Per-class precision / recall / F1 (12-class RF)\end{{tabular}}}},title style={{font=\normalsize,xshift=1.3cm,yshift=1pt}}]
\addplot[matrix plot*,point meta=explicit,mesh/rows={n},mesh/cols=3,mesh/ordering=rowwise,draw=white,line width=1.2pt] table[x=x,y=y,meta=c,col sep=comma]{{fig10_data.csv}};
{nodes}\end{{axis}}\end{{tikzpicture}}"""
    return build('fig10', b, 190)
def fig11():
    cmb = np.array(M['cm_binary_gateway']); cm12 = np.array(M['cm12']); labs = M['labels']; n = 12
    col = lambda v, mx: int(round(100 * math.log10(v + 1) / math.log10(mx + 1)))
    b = r"\begin{tikzpicture}[font=\small]" + "\n" + r"\node[font=\normalsize] at (2.6,0.9) {(a) Binary gateway (Random Forest, $\tau=0.50$)};" + "\n"; mx = cmb.max(); cs = 2.7
    for i in range(2):
        for j in range(2):
            p = col(cmb[i, j], mx); b += rf"\fill[blue!{p}!white!70!black!{0}] ({j*cs},{-i*cs}) rectangle ++({cs},{-cs});" if False else rf"\fill[blue!{max(p,4)}!white] ({j*cs},{-i*cs}) rectangle ++({cs},{-cs}); \node[{'white' if p>55 else 'black'},font=\Large] at ({j*cs+cs/2},{-i*cs-cs/2}) {{{cmb[i,j]:,}}};" + "\n"
    b += rf"\node[rotate=90,anchor=south,font=\large] at (-1.9,{-cs}) {{Actual}}; \node[font=\large] at ({cs},{-2*cs-1.1}) {{Predicted}}; \node[rotate=90,anchor=south] at (-0.15,{-cs/2}) {{Authorized}}; \node[rotate=90,anchor=south] at (-0.15,{-cs*1.5}) {{Unauthorized}}; \node at ({cs/2},{-2*cs-0.35}) {{Authorized}}; \node at ({cs*1.5},{-2*cs-0.35}) {{Unauthorized}};" + "\n"
    ox = 10.2; c0 = 0.62; mx2 = cm12.max(); b += rf"\node[font=\normalsize] at ({ox+n*c0/2},0.9) {{(b) Separately trained 12-class model (counts)}};" + "\n"
    for i in range(n):
        for j in range(n):
            v = cm12[i, j]; p = col(v, mx2); b += rf"\fill[blue!{max(p,3)}!white] ({ox+j*c0},{-i*c0}) rectangle ++({c0},{-c0});"
            if v: b += rf"\node[{'white' if p>55 else 'black'},font=\fontsize{{5}}{{5}}\selectfont] at ({ox+j*c0+c0/2},{-i*c0-c0/2}) {{{v}}};"
            b += "\n"
    for i, l in enumerate(labs): b += rf"\node[anchor=east,font=\fontsize{{6}}{{6}}\selectfont] at ({ox-0.08},{-i*c0-c0/2}) {{{tx(l)}}}; \node[anchor=east,rotate=60,font=\fontsize{{6}}{{6}}\selectfont] at ({ox+i*c0+c0/2+0.12},-{n*c0+0.08}) {{{tx(l)}}};" + "\n"
    b += rf"\node[rotate=90,anchor=south,font=\normalsize] at ({ox-2.7},{-n*c0/2}) {{Actual}}; \node[font=\normalsize] at ({ox+n*c0/2},-{n*c0+2.5}) {{Predicted}};" + "\n" + "\\end{tikzpicture}"
    return build('fig11', b, 200)
def fig12():
    A = load('ablation.json'); keys = list(A); short = []
    for k in keys:
        if k.startswith('Full'): short.append('Full model (RF, all 82 features)')
        elif 'categorical' in k: short.append(r'$-$ Categorical features (proto, service)')
        elif 'temporal' in k: short.append(r'$-$ Temporal features (' + k.split('(')[1].split(':')[0] + ')')
        elif 'port' in k: short.append(r'$-$ Port numbers')
        elif 'Reduced' in k: short.append('Reduced ensemble (50 trees)')
        else: short.append(r'No behavioural gate (baseline under assumption)')
    n = len(keys); yl = ','.join('{' + t + '}' for t in short)
    b = rf"""\begin{{tikzpicture}}\begin{{axis}}[width=12.5cm,height=7.6cm,xbar,xmin=0,xmax=1.3,ymin=-0.6,ymax={n-0.4},ytick={{0,...,{n-1}}},yticklabels={{{yl}}},y tick label style={{font=\footnotesize}},xlabel={{Macro-F1 on test split (F1 of the Unauthorized class in brackets)}},xmajorgrids,xtick={{0,.2,.4,.6,.8,1}}]
"""
    for i, k in enumerate(keys):
        a = A[k]; last = (i == n - 1); opt = 'pattern=north east lines,pattern color=barGreen' if last else 'fill=barGreen'
        b += rf"\addplot[xbar,bar shift=0pt,{opt},draw=black!60,bar width=0.55cm,point meta=explicit symbolic,nodes near coords,nodes near coords style={{font=\scriptsize,anchor=west}}] coordinates {{({a['macro_f1']:.4f},{i}) [{a['macro_f1']:.4f} ({a['f1_attack']:.4f})]}};" + "\n"
    return build('fig12', b + r"\end{axis}\end{tikzpicture}", 220)
def fig13():
    B = load('bench_live.json'); fields = [('throughput_tps', 'Throughput (confirmed tx/s)'), ('latency_median_s', 'Median confirmation latency (s)'), ('host_cpu_busy_fraction', 'Host CPU busy fraction (1 vCPU)')]
    b = r"\begin{tikzpicture}" + "\n"
    for i, (fld, lab) in enumerate(fields):
        b += rf"""\begin{{axis}}[at={{({i*7.3}cm,0)}},anchor=north west,width=6cm,height=5.4cm,xmin=0,xmax=110,xtick={{10,50,100}},xlabel={{Concurrently enrolling devices}},ylabel={{{lab}}},grid=both,{'ymin=0,ymax=1.05,' if 'cpu' in fld else 'ymin=0,'}legend pos=north west,legend cell align=left]
"""
        for key, col, mk, nm in [('n4', 'tbBlue', '*', '4 validators'), ('n7', 'tbRed', 'triangle*', '7 validators')]:
            runs = B[key]['runs']; loads = sorted(set(r['load'] for r in runs)); mean = [np.mean([r[fld] for r in runs if r['load'] == L]) for L in loads]; sd = [np.std([r[fld] for r in runs if r['load'] == L], ddof=1) for L in loads]
            b += rf"\addplot[{col},mark={mk},line width=1.2pt,error bars/.cd,y dir=both,y explicit] coordinates {{{' '.join(f'({L},{m:.5g}) +- (0,{s:.5g})' for L, m, s in zip(loads, mean, sd))}}};" + (rf" \addlegendentry{{{nm}}}" if i == 0 else '') + "\n"
        b += "\\end{axis}\n"
    b += r"\node[font=\footnotesize\itshape,anchor=south west] at (0,0.8) {registerDID, measured, one network at a time (mean $\pm$ s.d. of 3 runs); single shared host};" + "\n\\end{tikzpicture}"
    return build('fig13', b, 190)
if __name__ == '__main__':
    for w in (sys.argv[1:] or ['4', '5', '6', '8', '9', '10', '11', '12', '13']): globals()[f'fig{w}']()
