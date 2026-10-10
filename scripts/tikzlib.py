"""Shared helpers: standalone TikZ/pgfplots figures compiled with pdflatex and rasterised for the manuscript."""
import os, re, subprocess, shutil
TEX = os.path.abspath(os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures', 'tex')); FIG = os.path.abspath(os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures'))
PRE = r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage[T1]{fontenc}\usepackage{helvet}\usepackage{amsmath,amssymb}\renewcommand{\familydefault}{\sfdefault}
\usepackage{pgfplots}\pgfplotsset{compat=1.17}\usepgfplotslibrary{groupplots}
\usetikzlibrary{arrows.meta,positioning,shadows,fit,calc,backgrounds,patterns}
\definecolor{cLR}{HTML}{7F7F7F}\definecolor{cDT}{HTML}{2CA02C}\definecolor{ckNN}{HTML}{9467BD}\definecolor{cSVM}{HTML}{8C564B}\definecolor{cGB}{HTML}{FF7F0E}\definecolor{cRF}{HTML}{D62728}
\definecolor{cBlue}{HTML}{1F77B4}\definecolor{cGreen}{HTML}{2CA02C}\definecolor{cOrange}{HTML}{FF7F0E}\definecolor{cRed}{HTML}{D62728}
\pgfplotsset{every axis/.append style={tick label style={font=\footnotesize},label style={font=\small},title style={font=\small\bfseries},legend style={font=\scriptsize,draw=none,fill=white,fill opacity=.85,text opacity=1}}}
\begin{document}
"""
END = "\n\\end{document}\n"
def tx(s):
    return str(s).replace('\\', r'\textbackslash{}').replace('_', r'\_').replace('&', r'\&').replace('%', r'\%').replace('#', r'\#')
def build(name, body, dpi=200):
    os.makedirs(TEX, exist_ok=True); p = f'{TEX}/{name}.tex'; open(p, 'w').write(PRE + body + END)
    r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'{name}.tex'], cwd=TEX, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(f'{TEX}/{name}.pdf'):
        log = r.stdout[-1800:]; print(f'!! {name} FAILED\n{log}'); return False
    subprocess.run(['pdftocairo', '-png', '-r', str(dpi), '-singlefile', f'{name}.pdf', f'{FIG}/{name}'], cwd=TEX, check=True)
    for ext in ('aux', 'log'): 
        try: os.remove(f'{TEX}/{name}.{ext}')
        except OSError: pass
    print(f'{name}: ok'); return True
