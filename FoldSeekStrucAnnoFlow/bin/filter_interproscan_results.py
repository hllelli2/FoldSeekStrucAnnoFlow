from pathlib import Path

import polars as pl
import typer

app = typer.Typer()

INTERPROSCAN_COLS = [
    "protein_accession",
    "md5",
    "length",
    "analysis",
    "signature_accession",
    "signature_description",
    "start",
    "stop",
    "score",
    "status",
    "date",
    "interpro_accession",
    "interpro_description",
    "go_annotations",
    "pathways",
]

DEFAULT_KEEP_ANALYSES = "Gene3D,Pfam"


def filter_interproscan(df: pl.DataFrame, keep_analyses: str = DEFAULT_KEEP_ANALYSES) -> pl.DataFrame:
    """Keep only the given comma-separated InterProScan 'analysis' values."""
    analyses = [a.strip() for a in keep_analyses.split(",") if a.strip()]
    return df.filter(pl.col("analysis").is_in(analyses))


@app.command()
def main(
    interproscan_output_file: Path,
    output_file: Path,
    keep_analyses: str = typer.Option(
        DEFAULT_KEEP_ANALYSES,
        help="Comma-separated InterProScan 'analysis' values to keep. Everything else is dropped "
        "(e.g. PANTHER/SUPERFAMILY/CDD and disorder/feature predictors like MobiDBLite and Coils).",
    ),
) -> None:
    """Filter a raw InterProScan TSV down to a chosen set of analyses (Gene3D + Pfam by default)."""
    df = pl.read_csv(
        interproscan_output_file,
        separator="\t",
        quote_char=None,
        has_header=False,
        new_columns=INTERPROSCAN_COLS,
    )

    before = df.shape[0]
    df = filter_interproscan(df, keep_analyses)
    print(f"Kept {df.shape[0]} of {before} rows for analyses: {keep_analyses}")

    # Headerless, like the raw InterProScan TSV, so it's a drop-in replacement downstream.
    df.write_csv(output_file, separator="\t", include_header=False)


if __name__ == "__main__":
    app()
