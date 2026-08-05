"""
Portfolio PDF report generator — compiles a LaTeX document with pdflatex.

Requires texlive-latex-extra on the system:
    apt-get install -y texlive-latex-base texlive-latex-recommended \
                       texlive-latex-extra texlive-fonts-recommended
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

BULL_IMAGE = Path(__file__).parents[2] / "frontend" / "public" / "hero-bull.png"

_TIER_COLOR = {
    "very_low": "cspositive",
    "low": "cspositive",
    "medium": "cswarning",
    "high": "csnegative",
    "very_high": "csnegative",
}

_TIER_LABEL = {
    "very_low": "Very Low",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "very_high": "Very High",
}

_TIER_ORDER = ["very_low", "low", "medium", "high", "very_high"]


def _esc(text: str) -> str:
    """Escape LaTeX special characters in arbitrary strings."""
    for ch, repl in [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        text = text.replace(ch, repl)
    return text


def _addr_short(addr: str) -> str:
    return f"{addr[:8]}\\ldots{addr[-6:]}"


def _build_tex(wallets: list[dict], generated_at: str, has_bull: bool) -> str:
    # ── aggregates ──────────────────────────────────────────────────────────
    weighted_score = round(sum(w["score"] * w["weight"] / 100 for w in wallets))
    weighted_pd = sum(w["pd"] * w["weight"] / 100 for w in wallets) * 100
    total_weight = sum(w["weight"] for w in wallets)

    risk_counts: dict[str, int] = {}
    for w in wallets:
        t = w.get("risk_tier", "medium")
        risk_counts[t] = risk_counts.get(t, 0) + 1

    # ── risk distribution line ───────────────────────────────────────────────
    risk_parts: list[str] = []
    for tier in _TIER_ORDER:
        count = risk_counts.get(tier, 0)
        if count:
            col = _TIER_COLOR[tier]
            label = _TIER_LABEL[tier]
            risk_parts.append(
                rf"\textcolor{{{col}}}{{\textbullet}}\, {count}$\times$ {label}"
            )
    risk_dist = r"\quad ".join(risk_parts)

    # ── portfolio table rows ─────────────────────────────────────────────────
    rows: list[str] = []
    for w in wallets:
        tier = w.get("risk_tier", "medium")
        col = _TIER_COLOR.get(tier, "csmuted")
        label = _TIER_LABEL.get(tier, tier)
        rows.append(
            rf"  \ttfamily\footnotesize {_addr_short(w['address'])} & "
            rf"{w['score']} & "
            rf"\textcolor{{{col}}}{{{label}}} & "
            rf"{w['pd'] * 100:.1f}\% & "
            rf"{w['weight']:.1f}\% \\"
        )
    wallet_rows = "\n".join(rows)

    # ── individual wallet detail cards ──────────────────────────────────────
    detail_blocks: list[str] = []
    for i, w in enumerate(wallets):
        tier = w.get("risk_tier", "medium")
        col = _TIER_COLOR.get(tier, "csmuted")
        label = _TIER_LABEL.get(tier, tier)
        block = (
            rf"\noindent\textcolor{{csmuted}}{{\scriptsize Wallet {i + 1} of {len(wallets)}}}\\"
            "\n"
            rf"\noindent{{\ttfamily\small {_esc(w['address'])}}}\\"
            "\n"
            r"\vspace{0.15cm}"
            "\n"
            r"\begin{tabular}{p{2.8cm} p{2.8cm} p{2.8cm} p{2.8cm}}"
            "\n"
            r"  \textcolor{csmuted}{\scriptsize SCORE} & "
            r"\textcolor{csmuted}{\scriptsize RISK TIER} & "
            r"\textcolor{csmuted}{\scriptsize EST.\ PD} & "
            r"\textcolor{csmuted}{\scriptsize WEIGHT} \\"
            "\n"
            rf"  \textbf{{\large {w['score']}}} & "
            rf"  \textbf{{\textcolor{{{col}}}{{{label}}}}} & "
            rf"  \textbf{{{w['pd'] * 100:.1f}\%}} & "
            rf"  \textbf{{{w['weight']:.1f}\%}} \\"
            "\n"
            r"\end{tabular}"
            "\n"
            r"\vspace{0.5cm}"
            "\n"
        )
        detail_blocks.append(block)
    wallet_details = "\n".join(detail_blocks)

    # ── watermark: bull image at bottom-left, brand at bottom-right ─────────
    if has_bull:
        bull_node = (
            r"    \node[opacity=0.07, anchor=south west, inner sep=1cm]"
            "\n"
            r"      at (current page.south west)"
            "\n"
            r"      {\includegraphics[height=3cm]{bull}};"
        )
    else:
        # Fallback: stylised text bull if image missing
        bull_node = (
            r"    \node[opacity=0.08, anchor=south west, inner sep=1.2cm,"
            "\n"
            r"          font=\fontsize{28}{28}\selectfont\bfseries, text=csmuted]"
            "\n"
            r"      at (current page.south west) {\(\clubsuit\)};"
        )

    # ── assemble full document ───────────────────────────────────────────────
    tex = r"""
\documentclass[11pt, a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=2.5cm, top=3cm, bottom=3cm]{geometry}
\usepackage{booktabs}
\usepackage[table,dvipsnames]{xcolor}
\usepackage{fancyhdr}
\usepackage{graphicx}
\usepackage{eso-pic}
\usepackage{tikz}
\usepackage{tabularx}
\usepackage{array}
\usepackage{titlesec}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}

%% ── Colour palette (mirrors ChainScore CSS variables) ──────────────────────
\definecolor{csprimary}{HTML}{2563EB}
\definecolor{cspositive}{HTML}{16A34A}
\definecolor{csnegative}{HTML}{DC2626}
\definecolor{cswarning}{HTML}{D97706}
\definecolor{csmuted}{HTML}{6B7280}
\definecolor{cslight}{HTML}{F1F5F9}

%% ── Section headings ────────────────────────────────────────────────────────
\titleformat{\section}
  {\large\bfseries\color{csprimary}}
  {}{0em}{}
  [\color{csprimary}\vspace{2pt}\titlerule]
\titlespacing*{\section}{0pt}{1.5em}{0.8em}

%% ── Header / Footer ─────────────────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\headrule}{%
  \hbox to\headwidth{\color{csprimary}\leaders\hrule height\headrulewidth\hfill}%
}
\fancyhead[L]{{\small\bfseries\textcolor{csprimary}{ChainScore}}%
  \textcolor{csmuted}{\,\textbar\,}%
  {\small\textcolor{csmuted}{Portfolio Credit Report}}}
\fancyhead[R]{\small\textcolor{csmuted}{\thepage}}
\fancyfoot[C]{\scriptsize\textcolor{csmuted}{%
  Generated by ChainScore~\textbar~Confidential~\textbar~%
  Not for regulated credit decisions}}

%% ── Per-page watermark ──────────────────────────────────────────────────────
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture, overlay]
    %% Bull logo — bottom-left
BULL_NODE
    %% Brand name — bottom-right
    \node[opacity=0.09, anchor=south east, inner sep=1.2cm,
          font=\fontsize{22}{22}\selectfont\bfseries, text=csmuted]
      at (current page.south east) {ChainScore};
  \end{tikzpicture}%
}

\begin{document}

%% ═══════════════════════ TITLE ═════════════════════════════════════════════
\begin{center}
  {\fontsize{30}{36}\selectfont\bfseries\textcolor{csprimary}{ChainScore}}
  \\[0.4cm]
  {\Large\bfseries Portfolio Credit Intelligence Report}
  \\[0.3cm]
  {\small\textcolor{csmuted}{Generated on GENERATED_AT}}
\end{center}

\vspace{0.4cm}
{\color{csprimary}\rule{\textwidth}{1.5pt}}
\vspace{0.9cm}

%% ═══════════════════ EXECUTIVE SUMMARY ════════════════════════════════════
\section{Executive Summary}

\vspace{0.3cm}
\begin{center}
\begin{tabular}{p{3.4cm} p{3.4cm} p{3.4cm} p{3.4cm}}
  \multicolumn{1}{c}{\textcolor{csmuted}{\scriptsize WEIGHTED SCORE}} &
  \multicolumn{1}{c}{\textcolor{csmuted}{\scriptsize WEIGHTED PD}} &
  \multicolumn{1}{c}{\textcolor{csmuted}{\scriptsize WALLETS}} &
  \multicolumn{1}{c}{\textcolor{csmuted}{\scriptsize TOTAL WEIGHT}} \\[0.2cm]
  \multicolumn{1}{c}{{\Large\bfseries WEIGHTED_SCORE}} &
  \multicolumn{1}{c}{{\Large\bfseries WEIGHTED_PD\%}} &
  \multicolumn{1}{c}{{\Large\bfseries WALLET_COUNT}} &
  \multicolumn{1}{c}{{\Large\bfseries TOTAL_WEIGHT\%}} \\
\end{tabular}
\end{center}

\vspace{0.6cm}
\noindent\textcolor{csmuted}{\scriptsize RISK DISTRIBUTION}\quad
RISK_DIST

\vspace{1cm}

%% ═══════════════════ PORTFOLIO HOLDINGS ═══════════════════════════════════
\section{Portfolio Holdings}

\begin{tabularx}{\textwidth}{X r l r r}
  \toprule
  \textbf{Wallet Address} & \textbf{Score} & \textbf{Risk Tier} & \textbf{Est.\ PD} & \textbf{Weight} \\
  \midrule
WALLET_ROWS
  \bottomrule
\end{tabularx}

\vspace{1cm}

%% ═══════════════════ WALLET DETAILS ═══════════════════════════════════════
\section{Wallet Details}

WALLET_DETAILS

%% ═══════════════════ METHODOLOGY \& DISCLAIMER ═════════════════════════════
\section{Methodology \& Disclaimer}

\small

\noindent\textbf{Model:} LightGBM binary classifier trained on 76{,}932 liquidation events across
Aave~V2, Compound~V2, and MakerDAO (2020--2024).
Walk-forward validated AUC~0.764, KS~0.433, Gini~0.527.

\medskip
\noindent\textbf{Score:} Ranges from 0 (highest risk) to 1{,}000 (lowest risk). Derived from 43
on-chain behavioural features including protocol diversity, collateral health, and historical
liquidation exposure.

\medskip
\noindent\textbf{Probability of Default (PD):} Estimated 12-month probability of collateral
seizure by a DeFi protocol due to under-collateralisation. \emph{Not} equivalent to traditional
credit default risk.

\medskip
\noindent\textcolor{csnegative}{\bfseries Warning:} This report is provided for informational
purposes only and has \textbf{not} been reviewed or endorsed by any financial regulator.
ChainScore scores are \textbf{not suitable} for regulated credit decisions, Basel~III capital
calculations, or jurisdiction-specific lending compliance frameworks.

\vspace{1.5cm}
\noindent{\color{csmuted}\rule{\textwidth}{0.4pt}}\\[0.3cm]
\noindent\textcolor{csmuted}{\tiny
  ChainScore~\textbar~On-Chain Credit Intelligence~\textbar~
  Model Version: v2.0-cross-protocol~\textbar~
  \url{https://github.com/deerws/ChainScore}%
}

\end{document}
"""

    return (
        tex
        .replace("BULL_NODE", bull_node)
        .replace("GENERATED_AT", generated_at)
        .replace("WEIGHTED_SCORE", str(weighted_score))
        .replace("WEIGHTED_PD", f"{weighted_pd:.1f}")
        .replace("WALLET_COUNT", str(len(wallets)))
        .replace("TOTAL_WEIGHT", f"{total_weight:.1f}")
        .replace("RISK_DIST", risk_dist)
        .replace("WALLET_ROWS", wallet_rows)
        .replace("WALLET_DETAILS", wallet_details)
    )


def generate_portfolio_pdf(wallets: list[dict]) -> bytes:
    """
    Render a LaTeX portfolio report and return the compiled PDF bytes.

    Raises:
        ValueError: portfolio is empty
        RuntimeError: pdflatex not installed or compilation failed
    """
    if not wallets:
        raise ValueError("Portfolio is empty")
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex not found. Install: "
            "apt-get install -y texlive-latex-base texlive-latex-recommended "
            "texlive-latex-extra texlive-fonts-recommended"
        )

    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
    has_bull = BULL_IMAGE.exists()
    tex_source = _build_tex(wallets, generated_at, has_bull)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        if has_bull:
            shutil.copy(BULL_IMAGE, tmp / "bull.png")

        (tmp / "report.tex").write_text(tex_source, encoding="utf-8")

        compile_result = None
        for _ in range(2):  # two passes for page references
            compile_result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory", tmpdir,
                    "report.tex",
                ],
                capture_output=True,
                cwd=tmpdir,
                timeout=60,
            )

        pdf_path = tmp / "report.pdf"
        if not pdf_path.exists():
            stdout = (compile_result.stdout or b"").decode(errors="replace")
            logger.error("pdflatex compilation failed:\n%s", stdout[-3000:])
            raise RuntimeError("PDF compilation failed — check server logs for LaTeX errors")

        logger.info("Portfolio PDF compiled successfully (%d bytes)", pdf_path.stat().st_size)
        return pdf_path.read_bytes()
