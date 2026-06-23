from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl
import typer

app = typer.Typer()

MATCH_CATEGORIES = ["true", "false", "no_data"]
MATCH_LABELS = {"true": "Match", "false": "Mismatch", "no_data": "No InterProScan data"}
MATCH_COLORS = {"true": "#2ca02c", "false": "#d62728", "no_data": "#7f7f7f"}


def any_match_counts(comparison_file: Path) -> dict[str, int]:
    """Count proteins by any_match outcome, one count per protein_accession."""
    df = pl.read_csv(comparison_file, separator="\t", quote_char=None)
    df = df.unique(subset=["protein_accession"]).with_columns(pl.col("any_match").cast(pl.Utf8).fill_null("no_data"))
    counts = dict(zip(*df["any_match"].value_counts().sort("any_match")))
    return {category: counts.get(category, 0) for category in MATCH_CATEGORIES}


def plot_match_summary(ax: "plt.Axes", counts: dict[str, int], title: str) -> None:
    values = [counts[category] for category in MATCH_CATEGORIES]
    colors = [MATCH_COLORS[category] for category in MATCH_CATEGORIES]
    labels = [MATCH_LABELS[category] for category in MATCH_CATEGORIES]
    total = sum(values)

    bars = ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.set_ylabel("Proteins")
    for bar, value in zip(bars, values):
        pct = 100 * value / total if total else 0
        ax.annotate(
            f"{value} ({pct:.0f}%)",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
        )


@app.command()
def main(
    cath_comparison_file: Path,
    pfam_comparison_file: Path,
    output_file: Path,
) -> None:
    """Plot CATH and Pfam vs InterProScan any_match summaries side by side."""
    cath_counts = any_match_counts(cath_comparison_file)
    pfam_counts = any_match_counts(pfam_comparison_file)

    fig, (cath_ax, pfam_ax) = plt.subplots(1, 2, figsize=(10, 5))
    plot_match_summary(cath_ax, cath_counts, "CATH vs InterProScan Gene3D")
    plot_match_summary(pfam_ax, pfam_counts, "Pfam vs InterProScan Pfam")
    fig.tight_layout()
    fig.savefig(output_file, dpi=150)


if __name__ == "__main__":
    app()
