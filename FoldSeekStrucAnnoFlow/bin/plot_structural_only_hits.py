from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl
import typer

app = typer.Typer()

COVERAGE_CATEGORIES = ["Gene3D only", "Pfam only", "Both", "No coverage (gap)"]
COVERAGE_COLORS = {
    "Gene3D only": "#1f77b4",
    "Pfam only": "#ff7f0e",
    "Both": "#2ca02c",
    "No coverage (gap)": "#7f7f7f",
}


def _protein_key(df: pl.DataFrame) -> pl.DataFrame:
    """Add a `_protein_key` column: protein_accession, falling back to query_id
    when it's null (couldn't be mapped to InterProScan at all), so each unmapped
    case still counts as its own protein instead of collapsing into one null bucket.
    """
    return df.with_columns(pl.coalesce(pl.col("protein_accession"), pl.col("query_id")).alias("_protein_key"))


def overall_coverage_counts(df: pl.DataFrame) -> dict[str, int]:
    """Count proteins by Gene3D/Pfam coverage category, one count per protein -
    deduplicated across all source dbs combined (pdb/afdb50/afdb_swissprot)."""
    deduped = _protein_key(df).unique(subset=["_protein_key"])

    return {
        "Gene3D only": deduped.filter(pl.col("has_gene3d") & ~pl.col("has_pfam")).shape[0],
        "Pfam only": deduped.filter(~pl.col("has_gene3d") & pl.col("has_pfam")).shape[0],
        "Both": deduped.filter(pl.col("has_gene3d") & pl.col("has_pfam")).shape[0],
        "No coverage (gap)": deduped.filter(~pl.col("has_gene3d") & ~pl.col("has_pfam")).shape[0],
    }


def gap_proteins_by_db(df: pl.DataFrame) -> tuple[dict[str, int], int]:
    """Of the proteins with no Gene3D/Pfam coverage (deduplicated across all source
    dbs), how many did each individual db find? Counts can overlap across dbs,
    since the same gap protein is often hit by more than one of them.

    Returns (counts per db, total distinct gap proteins).
    """
    gaps = _protein_key(df).filter(pl.col("no_interpro_domain_hit"))
    total_gap_proteins = gaps["_protein_key"].n_unique()

    by_db = gaps.group_by("db").agg(pl.col("_protein_key").n_unique().alias("count")).sort("db")
    return {row["db"]: row["count"] for row in by_db.to_dicts()}, total_gap_proteins


def plot_coverage_breakdown(ax: "plt.Axes", counts: dict[str, int]) -> None:
    values = [counts[category] for category in COVERAGE_CATEGORIES]
    colors = [COVERAGE_COLORS[category] for category in COVERAGE_CATEGORIES]
    total = sum(values)

    bars = ax.bar(COVERAGE_CATEGORIES, values, color=colors)
    ax.set_title(
        f"InterProScan coverage of the {total} structurally-hit proteins\n(deduplicated across pdb/afdb50/afdb_swissprot)"
    )
    ax.set_ylabel("Proteins")
    ax.tick_params(axis="x", labelrotation=15)
    for bar, value in zip(bars, values):
        pct = 100 * value / total if total else 0
        ax.annotate(
            f"{value} ({pct:.0f}%)",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
        )


def plot_gap_proteins_by_db(ax: "plt.Axes", counts_by_db: dict[str, int], total_gap_proteins: int) -> None:
    dbs = list(counts_by_db.keys())
    values = list(counts_by_db.values())

    bars = ax.bar(dbs, values, color="#d62728")
    ax.axhline(total_gap_proteins, color="black", linestyle="--", linewidth=1)
    ax.set_title(
        f"Which source dbs found the {total_gap_proteins} no-coverage proteins\n(can overlap across dbs)", fontsize=11
    )
    ax.set_ylabel("No-coverage proteins found")
    ax.set_ylim(0, total_gap_proteins * 1.25 if total_gap_proteins else 1)
    for bar, value in zip(bars, values):
        pct = 100 * value / total_gap_proteins if total_gap_proteins else 0
        ax.annotate(
            f"{value}/{total_gap_proteins} ({pct:.0f}%)",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
            xytext=(0, 4),
            textcoords="offset points",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1},
        )


@app.command()
def main(
    structural_only_hits_file: Path,
    output_file: Path,
) -> None:
    """Plot InterProScan coverage of FoldSeek hits from structural-only databases (e.g. PDB/AFDB)."""
    df = pl.read_csv(structural_only_hits_file, separator="\t", quote_char=None)

    gap_counts_by_db, total_gap_proteins = gap_proteins_by_db(df)

    fig, (coverage_ax, gap_ax) = plt.subplots(1, 2, figsize=(11, 5))
    plot_coverage_breakdown(coverage_ax, overall_coverage_counts(df))
    plot_gap_proteins_by_db(gap_ax, gap_counts_by_db, total_gap_proteins)
    fig.tight_layout()
    fig.savefig(output_file, dpi=150)


if __name__ == "__main__":
    app()
