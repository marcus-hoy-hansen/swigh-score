#!/usr/bin/env python3
"""
Generate an HTML report from a combined swigh exhaustive V/J TSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from dataclasses import dataclass
from html import escape
from pathlib import Path
from statistics import median


@dataclass
class CloneRow:
    index: int
    count: int
    v_gene: str
    v_match_sequence: str
    v_identity: float
    v_sw_score: int
    v_aligned_bases: int
    v_swigh_score: float
    j_gene: str
    j_match_sequence: str
    j_identity: float
    j_sw_score: int
    j_aligned_bases: int
    j_swigh_score: float
    original_sequence: str

    @property
    def read_length(self) -> int:
        return len(self.original_sequence)

    @property
    def combined_swigh(self) -> float:
        return self.v_swigh_score + self.j_swigh_score

    @property
    def v_identity_pct(self) -> float:
        return self.v_identity * 100.0

    @property
    def j_identity_pct(self) -> float:
        return self.j_identity * 100.0


@dataclass
class LocalScore:
    percent: float
    sw_score: int
    match_span: int
    swigh_score: float

    def read_coverage_pct(self, read_length: int) -> float:
        if read_length <= 0:
            return 0.0
        return 100.0 * self.match_span / read_length


@dataclass
class ClonalSummary:
    query_sequence: str
    matched_sequence: str
    top_match_count: int
    total_collapsed_reads: int
    burden_98_count: int
    burden_98_pct: float
    top_similarity_pct: float
    top_sw_score: int
    top_aligned_bases: int
    top_swigh_score: float
    v_gene: str
    j_gene: str
    v_identity_pct: float
    j_identity_pct: float
    v_swigh_score: float
    j_swigh_score: float
    histogram_rows: list[tuple[float, int, float]]

    @property
    def query_length(self) -> int:
        return len(self.query_sequence)

    @property
    def matched_length(self) -> int:
        return len(self.matched_sequence)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HTML clone report")
    parser.add_argument("tsv", type=Path, help="Combined V/J exhaustive TSV")
    parser.add_argument("--output", type=Path, help="Output HTML path")
    parser.add_argument("--sample", default="", help="Sample name for title")
    parser.add_argument("--top", type=int, default=10, help="Number of top clones")
    parser.add_argument("--fastp-json", type=Path, default=None, help="Optional fastp JSON")
    parser.add_argument("--clonal-sequence", default="", help="Optional user-supplied clonal sequence")
    parser.add_argument("--clonal-out", type=Path, default=None, help="Optional swigh-score output for the clonal sequence")
    parser.add_argument("--clonal-vj-tsv", type=Path, default=None, help="Optional exhaustive V/J TSV for the clonal sequence")
    return parser.parse_args()


def load_rows(path: Path) -> list[CloneRow]:
    rows: list[CloneRow] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for raw in reader:
            rows.append(
                CloneRow(
                    index=int(raw["Index"]),
                    count=int(raw["Count"]),
                    v_gene=raw["V_gene"],
                    v_match_sequence=raw["V_match_sequence"],
                    v_identity=float(raw["V_identity"]),
                    v_sw_score=int(raw["V_SW_score"]),
                    v_aligned_bases=int(raw["V_aligned_bases"]),
                    v_swigh_score=float(raw["V_Swigh_score"]),
                    j_gene=raw["J_gene"],
                    j_match_sequence=raw["J_match_sequence"],
                    j_identity=float(raw["J_identity"]),
                    j_sw_score=int(raw["J_SW_score"]),
                    j_aligned_bases=int(raw["J_aligned_bases"]),
                    j_swigh_score=float(raw["J_Swigh_score"]),
                    original_sequence=raw["Original_sequence"],
                )
            )
    return rows


def load_clonal_summary(
    query_sequence: str, clonal_out: Path | None, clonal_vj_tsv: Path | None
) -> ClonalSummary | None:
    if not query_sequence or clonal_out is None or clonal_vj_tsv is None:
        return None
    if not clonal_out.exists() or not clonal_vj_tsv.exists():
        return None

    thresholds = [1.00, 0.99, 0.98, 0.97, 0.96, 0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.10, 0.00]
    total_collapsed_reads = 0
    best_fields: list[str] | None = None
    similarity_counts: list[tuple[float, int]] = []
    with clonal_out.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            fields = line.split()
            if len(fields) < 6:
                continue
            if best_fields is None:
                best_fields = fields[:6]
            count = int(fields[5])
            similarity = float(fields[1])
            total_collapsed_reads += count
            similarity_counts.append((similarity, count))
    if best_fields is None or total_collapsed_reads <= 0:
        return None

    matched_sequence = best_fields[0]
    top_similarity_pct = float(best_fields[1]) * 100.0
    top_sw_score = int(best_fields[2])
    top_aligned_bases = int(best_fields[3])
    top_swigh_score = float(best_fields[4])
    top_match_count = int(best_fields[5])
    burden_98_count = sum(count for similarity, count in similarity_counts if similarity >= 0.98)
    histogram_rows = [
        (
            threshold,
            sum(count for similarity, count in similarity_counts if similarity >= threshold),
            100.0 * sum(count for similarity, count in similarity_counts if similarity >= threshold) / total_collapsed_reads,
        )
        for threshold in thresholds
    ]

    clonal_rows = load_rows(clonal_vj_tsv)
    if not clonal_rows:
        return None
    clonal_row = clonal_rows[0]

    return ClonalSummary(
        query_sequence=query_sequence,
        matched_sequence=matched_sequence,
        top_match_count=top_match_count,
        total_collapsed_reads=total_collapsed_reads,
        burden_98_count=burden_98_count,
        burden_98_pct=100.0 * burden_98_count / total_collapsed_reads,
        top_similarity_pct=top_similarity_pct,
        top_sw_score=top_sw_score,
        top_aligned_bases=top_aligned_bases,
        top_swigh_score=top_swigh_score,
        v_gene=clonal_row.v_gene,
        j_gene=clonal_row.j_gene,
        v_identity_pct=clonal_row.v_identity_pct,
        j_identity_pct=clonal_row.j_identity_pct,
        v_swigh_score=clonal_row.v_swigh_score,
        j_swigh_score=clonal_row.j_swigh_score,
        histogram_rows=histogram_rows,
    )


def load_fastp_stats(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    with path.open() as handle:
        data = json.load(handle)
    summary = data.get("summary", {})
    before = summary.get("before_filtering", {})
    after = summary.get("after_filtering", {})
    filtering = data.get("filtering_result", {})
    return {
        "Raw read pairs": f"{before.get('total_reads', 0):,}",
        "Post-fastp read pairs": f"{after.get('total_reads', 0):,}",
        "Passed filter": f"{filtering.get('passed_filter_reads', 0):,}",
        "Low-quality discarded": f"{filtering.get('low_quality_reads', 0):,}",
    }


def rank_rows(rows: list[CloneRow]) -> list[CloneRow]:
    return sorted(
        rows,
        key=lambda row: (row.count, row.combined_swigh, row.v_swigh_score, row.j_swigh_score),
        reverse=True,
    )


def seq_preview(seq: str, width: int = 26) -> str:
    if len(seq) <= width * 2:
        return seq
    return f"{seq[:width]}...{seq[-width:]}"


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def run_swscore(query: str, reference: str) -> LocalScore:
    cmd = [str(script_dir() / "bin" / "SWscore"), query, reference]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    fields = result.stdout.strip().split("\t")
    if len(fields) != 5:
        raise ValueError(f"Unexpected SWscore output: {result.stdout!r}")
    return LocalScore(
        percent=float(fields[1]),
        sw_score=int(fields[2]),
        match_span=int(fields[3]),
        swigh_score=float(fields[4]),
    )


def build_local_scores(rows: list[CloneRow]) -> dict[int, dict[str, LocalScore]]:
    scores: dict[int, dict[str, LocalScore]] = {}
    for row in rows[:10]:
        scores[row.index] = {
            "v": run_swscore(row.original_sequence, row.v_match_sequence),
            "j": run_swscore(row.original_sequence, row.j_match_sequence),
            "vj": run_swscore(row.original_sequence, row.v_match_sequence + row.j_match_sequence),
        }
    return scores


def sort_top_rows_by_vj_local(
    rows: list[CloneRow], local_scores: dict[int, dict[str, LocalScore]], top_n: int = 10
) -> list[CloneRow]:
    top_rows = rows[:top_n]
    return sorted(
        top_rows,
        key=lambda row: (
            local_scores[row.index]["vj"].percent,
            local_scores[row.index]["vj"].match_span,
            row.count,
        ),
        reverse=True,
    )


def make_bar_chart(rows: list[CloneRow], width: int = 1120, height: int = 420) -> str:
    chart_rows = rows[:10]
    if not chart_rows:
        return ""
    left, right, top, bottom = 68, 24, 30, 78
    plot_w, plot_h = width - left - right, height - top - bottom
    max_count = max(row.count for row in chart_rows) or 1
    bar_w = plot_w / len(chart_rows)
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Top clone abundance bar chart">']
    pieces.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>')
    pieces.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#1f2937"/>')
    for tick in range(6):
        frac = tick / 5
        y = top + plot_h - frac * plot_h
        label = int(round(max_count * frac))
        pieces.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#ece7dc"/>')
        pieces.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end" font-size="13" fill="#4b5563">{label}</text>')
    for i, row in enumerate(chart_rows):
        x = left + i * bar_w + bar_w * 0.1
        h = (row.count / max_count) * plot_h
        y = top + plot_h - h
        pieces.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.8:.1f}" height="{h:.1f}" rx="6" fill="#b45309"/>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="13" fill="#111827">{row.count}</text>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{top + plot_h + 20}" text-anchor="middle" font-size="12" fill="#374151">#{row.index}</text>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{top + plot_h + 38}" text-anchor="middle" font-size="11" fill="#6b7280">{escape(row.v_gene)}</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def make_scatter(rows: list[CloneRow], width: int = 1120, height: int = 440) -> str:
    if not rows:
        return ""
    left, right, top, bottom = 70, 30, 24, 58
    plot_w, plot_h = width - left - right, height - top - bottom
    max_x = max(row.v_swigh_score for row in rows) or 1.0
    max_y = max(row.j_swigh_score for row in rows) or 1.0
    max_count = max(row.count for row in rows) or 1
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="V and J swigh score scatter plot">']
    pieces.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>')
    pieces.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#1f2937"/>')
    pieces.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#1f2937"/>')
    for tick in range(6):
        frac = tick / 5
        x = left + frac * plot_w
        y = top + plot_h - frac * plot_h
        pieces.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#f1ede6"/>')
        pieces.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#f1ede6"/>')
        pieces.append(f'<text x="{x}" y="{top + plot_h + 22}" text-anchor="middle" font-size="12" fill="#4b5563">{max_x * frac:.0f}</text>')
        pieces.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end" font-size="12" fill="#4b5563">{max_y * frac:.0f}</text>')
    for row in rows[:200]:
        x = left + (row.v_swigh_score / max_x) * plot_w
        y = top + plot_h - (row.j_swigh_score / max_y) * plot_h
        r = 4 + 10 * math.sqrt(row.count / max_count)
        pieces.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#0f766e" fill-opacity="0.58" stroke="#134e4a"/>')
    pieces.append(f'<text x="{left + plot_w / 2}" y="{height - 10}" text-anchor="middle" font-size="14" fill="#111827">V Swigh score</text>')
    pieces.append(f'<text x="18" y="{top + plot_h / 2}" transform="rotate(-90 18 {top + plot_h / 2})" text-anchor="middle" font-size="14" fill="#111827">J Swigh score</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def make_length_chart(rows: list[CloneRow], width: int = 1120, height: int = 360) -> str:
    top_rows = rows[:10]
    if not top_rows:
        return ""
    left, right, top, bottom = 68, 24, 28, 56
    plot_w, plot_h = width - left - right, height - top - bottom
    max_len = max(row.read_length for row in top_rows) or 1
    bar_w = plot_w / len(top_rows)
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Top clone read length chart">']
    pieces.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>')
    pieces.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#1f2937"/>')
    for i, row in enumerate(top_rows):
        x = left + i * bar_w + bar_w * 0.12
        h = (row.read_length / max_len) * plot_h
        y = top + plot_h - h
        pieces.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.76:.1f}" height="{h:.1f}" rx="6" fill="#2563eb"/>')
        pieces.append(f'<text x="{x + bar_w * 0.38:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="13" fill="#111827">{row.read_length}</text>')
        pieces.append(f'<text x="{x + bar_w * 0.38:.1f}" y="{top + plot_h + 20}" text-anchor="middle" font-size="12" fill="#374151">#{row.index}</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def build_table(rows: list[CloneRow], local_scores: dict[int, dict[str, LocalScore]]) -> str:
    total = sum(row.count for row in rows) or 1
    display_rows = sort_top_rows_by_vj_local(rows, local_scores)
    header = (
        "<tr><th>Rank</th><th>Clone</th><th>Count</th><th>% of reads</th><th>V gene</th><th>J gene</th>"
        "<th>V local %</th><th>V local span</th>"
        "<th>J local %</th><th>J local span</th>"
        "<th>VJ local %</th><th>VJ local span</th><th>VJ read cover %</th>"
        "<th>Read length</th><th>Sequence</th></tr>"
    )
    body = []
    for rank, row in enumerate(display_rows, start=1):
        pct = 100 * row.count / total
        local = local_scores[row.index]
        body.append(
            "<tr>"
            f"<td>{rank}</td><td>#{row.index}</td><td>{row.count:,}</td><td>{pct:.2f}</td>"
            f"<td>{escape(row.v_gene)}</td><td>{escape(row.j_gene)}</td>"
            f"<td>{local['v'].percent * 100:.1f}</td><td>{local['v'].match_span}</td>"
            f"<td>{local['j'].percent * 100:.1f}</td><td>{local['j'].match_span}</td>"
            f"<td>{local['vj'].percent * 100:.1f}</td><td>{local['vj'].match_span}</td><td>{local['vj'].read_coverage_pct(row.read_length):.1f}</td>"
            f"<td>{row.read_length}</td><td><code>{escape(seq_preview(row.original_sequence))}</code></td>"
            "</tr>"
        )
    return "<table>" + header + "".join(body) + "</table>"


def build_clone_panes(rows: list[CloneRow], local_scores: dict[int, dict[str, LocalScore]]) -> str:
    display_rows = sort_top_rows_by_vj_local(rows, local_scores)
    panes = []
    for rank, row in enumerate(display_rows, start=1):
        local = local_scores[row.index]
        panes.append(
            '<details class="clone-pane">'
            f'<summary><span>#{rank} Clone #{row.index}</span><span>{row.count:,} reads | {escape(row.v_gene)} / {escape(row.j_gene)}</span></summary>'
            '<div class="clone-pane-body">'
            f'<p><strong>Original sequence:</strong> <code>{escape(row.original_sequence)}</code></p>'
            '<div class="mini-grid">'
            f'<div><span>V local %</span><strong>{local["v"].percent * 100:.1f}%</strong></div>'
            f'<div><span>J local %</span><strong>{local["j"].percent * 100:.1f}%</strong></div>'
            f'<div><span>VJ local %</span><strong>{local["vj"].percent * 100:.1f}%</strong></div>'
            f'<div><span>V local span</span><strong>{local["v"].match_span}</strong></div>'
            f'<div><span>J local span</span><strong>{local["j"].match_span}</strong></div>'
            f'<div><span>VJ local span</span><strong>{local["vj"].match_span}</strong></div>'
            f'<div><span>VJ read cover</span><strong>{local["vj"].read_coverage_pct(row.read_length):.1f}%</strong></div>'
            '</div>'
            '<div class="seq-grid">'
            f'<div><h4>V matched sequence</h4><pre>{escape(row.v_match_sequence)}</pre></div>'
            f'<div><h4>J matched sequence</h4><pre>{escape(row.j_match_sequence)}</pre></div>'
            '</div>'
            '</div></details>'
        )
    return "".join(panes)


def make_clonal_histogram(clonal: ClonalSummary | None, width: int = 1120, height: int = 360) -> str:
    if clonal is None or not clonal.histogram_rows:
        return ""
    rows = clonal.histogram_rows
    left, right, top, bottom = 68, 24, 30, 92
    plot_w, plot_h = width - left - right, height - top - bottom
    max_count = max(count for _, count, _ in rows) or 1
    bar_w = plot_w / len(rows)
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Clonal burden histogram by identity cutoff">']
    pieces.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>')
    pieces.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#1f2937"/>')
    for tick in range(6):
        frac = tick / 5
        y = top + plot_h - frac * plot_h
        label = int(round(max_count * frac))
        pieces.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#ece7dc"/>')
        pieces.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end" font-size="13" fill="#4b5563">{label}</text>')
    for i, (threshold, count, pct) in enumerate(rows):
        x = left + i * bar_w + bar_w * 0.1
        h = (count / max_count) * plot_h
        y = top + plot_h - h
        pieces.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.8:.1f}" height="{h:.1f}" rx="6" fill="#be123c"/>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="11" fill="#111827">{pct:.1f}%</text>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{top + plot_h + 20}" text-anchor="middle" font-size="11" fill="#374151">&gt;={threshold:.2f}</text>')
        pieces.append(f'<text x="{x + bar_w * 0.4:.1f}" y="{top + plot_h + 38}" text-anchor="middle" font-size="10" fill="#6b7280">{count:,}</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def build_clonal_overview(clonal: ClonalSummary | None) -> str:
    if clonal is None:
        return ""
    return (
        '<section class="hero hero-clonal"><div>'
        '<h2>Clonal sequence overview</h2>'
        f'<p class="lead">Clonal burden is defined here as reads with <strong>&gt;=98% identity</strong> to the supplied sequence. '
        f'That burden is <strong>{clonal.burden_98_count:,}</strong> collapsed reads '
        f'(<strong>{clonal.burden_98_pct:.2f}%</strong> of {clonal.total_collapsed_reads:,} collapsed reads). '
        f'The direct clonal annotation is V=<strong>{escape(clonal.v_gene)}</strong>, '
        f'J=<strong>{escape(clonal.j_gene)}</strong>.</p>'
        f'<p><strong>Query sequence ({clonal.query_length} bp):</strong> <code>{escape(clonal.query_sequence)}</code></p>'
        f'<p><strong>Top observed matching read ({clonal.matched_length} bp):</strong> <code>{escape(clonal.matched_sequence)}</code></p>'
        '</div><div class="metrics">'
        f'<div><span>98% burden</span><strong>{clonal.burden_98_pct:.2f}%</strong></div>'
        f'<div><span>98% read count</span><strong>{clonal.burden_98_count:,}</strong></div>'
        f'<div><span>Top-read count</span><strong>{clonal.top_match_count:,}</strong></div>'
        f'<div><span>Top-read identity</span><strong>{clonal.top_similarity_pct:.1f}%</strong></div>'
        f'<div><span>Aligned bases</span><strong>{clonal.top_aligned_bases}</strong></div>'
        f'<div><span>SW score</span><strong>{clonal.top_sw_score}</strong></div>'
        f'<div><span>Swigh score</span><strong>{clonal.top_swigh_score:.2f}</strong></div>'
        f'<div><span>V identity</span><strong>{clonal.v_identity_pct:.1f}%</strong></div>'
        f'<div><span>J identity</span><strong>{clonal.j_identity_pct:.1f}%</strong></div>'
        f'<div><span>V Swigh</span><strong>{clonal.v_swigh_score:.2f}</strong></div>'
        f'<div><span>J Swigh</span><strong>{clonal.j_swigh_score:.2f}</strong></div>'
        '</div></section>'
    )


def build_clonal_warning(clonal: ClonalSummary | None) -> str:
    if clonal is None or clonal.top_similarity_pct >= 50.0:
        return ""
    return (
        '<section class="warning-banner" role="alert">'
        '<strong>Warning:</strong> '
        f'The closest observed match to the supplied clonal sequence is only '
        f'<strong>{clonal.top_similarity_pct:.1f}% identity</strong>. '
        'Interpret clonal burden and annotation outputs with caution.'
        '<div class="warning-hint">A wrong locus selection is one possible explanation. '
        'Check whether <code>--locus igh</code>, <code>--locus igk</code>, or <code>--locus igl</code> matches the assay and clonal sequence you supplied.</div>'
        '</section>'
    )


def build_html(
    sample: str,
    rows: list[CloneRow],
    top_n: int,
    fastp_stats: dict[str, str],
    clonal: ClonalSummary | None,
) -> str:
    ranked = rank_rows(rows)
    top = ranked[:top_n]
    local_scores = build_local_scores(ranked)
    total_unique = len(ranked)
    total_reads = sum(row.count for row in ranked)
    read_lengths = [row.read_length for row in ranked]
    dominant = top[0] if top else None
    top_reads = sum(row.count for row in top)
    summary_cards = {
        "Unique clones": f"{total_unique:,}",
        "Collapsed reads": f"{total_reads:,}",
        "Top 10 read share": f"{(100 * top_reads / total_reads) if total_reads else 0:.2f}%",
        "Median read length": f"{median(read_lengths) if read_lengths else 0}",
    }
    summary_cards.update(fastp_stats)
    card_html = "".join(
        f'<div class="card"><div class="label">{escape(k)}</div><div class="value">{escape(v)}</div></div>'
        for k, v in summary_cards.items()
    )
    clonal_overview_html = build_clonal_overview(clonal)
    clonal_warning_html = build_clonal_warning(clonal)
    dominant_html = ""
    if dominant is not None:
        dominant_html = (
            '<section class="hero"><div><h2>Top clone</h2>'
            f'<p class="lead">Clone #{dominant.index} is the dominant rearrangement with <strong>{dominant.count:,}</strong> collapsed reads, '
            f'V=<strong>{escape(dominant.v_gene)}</strong>, J=<strong>{escape(dominant.j_gene)}</strong>.</p></div>'
            '<div class="metrics">'
            f'<div><span>V local %</span><strong>{local_scores[dominant.index]["v"].percent * 100:.1f}%</strong></div>'
            f'<div><span>J local %</span><strong>{local_scores[dominant.index]["j"].percent * 100:.1f}%</strong></div>'
            f'<div><span>VJ local %</span><strong>{local_scores[dominant.index]["vj"].percent * 100:.1f}%</strong></div>'
            f'<div><span>V local span</span><strong>{local_scores[dominant.index]["v"].match_span}</strong></div>'
            f'<div><span>J local span</span><strong>{local_scores[dominant.index]["j"].match_span}</strong></div>'
            f'<div><span>VJ read cover</span><strong>{local_scores[dominant.index]["vj"].read_coverage_pct(dominant.read_length):.1f}%</strong></div>'
            '</div></section>'
        )
    title = f"{sample} Clone Report" if sample else "Clone Report"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f3eb;
      --paper: #fffdf8;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #e5dccf;
      --soft: #faf5ee;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #f2e8da 0, transparent 28%), linear-gradient(180deg, #f7f3eb 0%, #efe7d8 100%);
    }}
    .wrap {{ max-width: 1320px; margin: 0 auto; padding: 28px 20px 56px; }}
    h1, h2, h3, h4 {{ margin: 0 0 12px; line-height: 1.1; }}
    h1 {{ font-size: 40px; letter-spacing: -0.03em; }}
    .sub {{ margin: 8px 0 24px; color: var(--muted); font-size: 17px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 18px; }}
    .card, .panel, .hero, .clone-pane {{ background: var(--paper); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 10px 26px rgba(80, 53, 19, 0.07); }}
    .card {{ padding: 16px 18px; }}
    .card .label, .mini-grid span {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .card .value {{ margin-top: 8px; font-size: 28px; font-weight: 700; }}
    .warning-banner {{
      margin: 18px 0 0;
      padding: 16px 18px;
      border-radius: 18px;
      border: 2px solid #b91c1c;
      background: linear-gradient(180deg, #fef2f2 0%, #fee2e2 100%);
      color: #7f1d1d;
      box-shadow: 0 10px 26px rgba(127, 29, 29, 0.10);
      font-size: 17px;
      line-height: 1.4;
    }}
    .warning-banner strong {{ color: #991b1b; }}
    .warning-hint {{
      margin-top: 10px;
      font-size: 15px;
      color: #7f1d1d;
    }}
    .hero {{ display: grid; grid-template-columns: 1.8fr 1fr; gap: 18px; padding: 22px; margin: 20px 0; }}
    .lead {{ font-size: 18px; margin: 0; }}
    .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
    .metrics div, .mini-grid div {{ background: var(--soft); border-radius: 14px; padding: 12px; border: 1px solid #eadfcd; }}
    .metrics span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .metrics strong {{ display: block; margin-top: 6px; font-size: 24px; }}
    .wide-grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; margin: 20px 0; }}
    .grid-two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }}
    .panel {{ padding: 18px; overflow: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; font-size: 12px; color: #7c2d12; word-break: break-all; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #fcfaf6; border: 1px solid #eadfcd; border-radius: 14px; padding: 12px; font-size: 12px; line-height: 1.35; overflow: auto; }}
    .clone-pane {{ margin: 14px 0; }}
    .clone-pane summary {{ display: flex; justify-content: space-between; gap: 12px; cursor: pointer; padding: 16px 18px; font-weight: 700; }}
    .clone-pane-body {{ padding: 0 18px 18px; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }}
    .mini-grid strong {{ display: block; margin-top: 6px; font-size: 16px; }}
    .seq-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .foot {{ margin-top: 16px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 980px) {{
      .hero, .grid-two, .seq-grid {{ grid-template-columns: 1fr; }}
      .mini-grid {{ grid-template-columns: 1fr 1fr; }}
      .clone-pane summary {{ display: block; }}
    }}
    @media (max-width: 780px) {{
      h1 {{ font-size: 32px; }}
      .mini-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{escape(title)}</h1>
    <p class="sub">Top {top_n} clone-focused report from combined V/J exhaustive clonotyping. Percentages are length-normalized identity values from the TSV output.</p>
    {clonal_warning_html}
    {clonal_overview_html}
    <section class="cards">{card_html}</section>
    <section class="wide-grid">
      <div class="panel">
        <h3>Clonal identity histogram</h3>
        <p>Collapsed-read counts and fractions at each identity cutoff, matching the threshold ladder from <code>swigh-report</code>.</p>
        {make_clonal_histogram(clonal)}
      </div>
    </section>
    {dominant_html}
    <section class="panel">
      <h2>Top clone table</h2>
      {build_table(ranked, local_scores)}
    </section>
    <section class="wide-grid">
      <div class="panel">
        <h3>Abundance of top 10 clones</h3>
        {make_bar_chart(ranked)}
      </div>
      <div class="panel">
        <h3>V vs J Swigh score</h3>
        {make_scatter(ranked)}
      </div>
    </section>
    <section class="grid-two">
      <div class="panel">
        <h3>Read length of top 10 clones</h3>
        {make_length_chart(ranked)}
      </div>
      <div class="panel">
        <h3>Interpretation notes</h3>
        <p><strong>V local %, J local %, and VJ local %</strong> are computed with <code>bin/SWscore</code> on the top clones, which better matches a local-alignment interpretation than the exhaustive TSV identity field.</p>
        <p><strong>Local span</strong> is the matched span returned by <code>SWscore</code> for that comparison. <strong>VJ read cover %</strong> is the VJ local span divided by total read length.</p>
        <p class="foot">This report does not depend on EMBOSS.</p>
      </div>
    </section>
    <section class="panel">
      <h2>Top 10 clone panes</h2>
      {build_clone_panes(top, local_scores)}
    </section>
  </div>
</body>
</html>"""


def main() -> None:
    args = parse_args()
    rows = load_rows(args.tsv)
    if not rows:
        raise SystemExit("No rows found in TSV")
    sample = args.sample or args.tsv.stem.replace(".igl.vj.exhaustive", "")
    output = args.output or args.tsv.with_suffix(".html")
    clonal = load_clonal_summary(args.clonal_sequence, args.clonal_out, args.clonal_vj_tsv)
    html = build_html(sample, rows, args.top, load_fastp_stats(args.fastp_json), clonal)
    output.write_text(html)
    print(output)


if __name__ == "__main__":
    main()
