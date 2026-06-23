"""Validate structure-based FoldSeek annotations against InterProScan.

Subcommands:
    cath     - check FoldSeek CATH labels (final_domain_annotations.tsv) against InterProScan Gene3D hits
    pfam     - check FoldSeek Pfam hits (foldseek_parsed_results_non-cath.tsv, db == PfamSDB) against InterProScan Pfam hits
    diagnose - join FoldSeek results against the full InterProScan output and report ID-mapping / hit coverage

All three take a `match_columns_file` produced by match_names.py, mapping pipeline
IDs (e.g. "transcript=...") to InterProScan protein_accession values.
"""

import json
from pathlib import Path
from typing import cast

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


def load_interproscan_tsv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, separator="\t", quote_char=None, has_header=False, new_columns=INTERPROSCAN_COLS)


def load_match_columns(path: Path) -> dict[str, str]:
    with open(path) as f:
        return cast(dict[str, str], json.load(f))


def map_pipeline_id(
    df_pipeline: pl.DataFrame, pipeline_col: str, interpro_col: str, match_columns: dict[str, str]
) -> pl.DataFrame:
    """Add `interpro_col` to df_pipeline by mapping `pipeline_col` through match_columns."""
    return df_pipeline.with_columns(pl.col(pipeline_col).replace(match_columns).alias(interpro_col))


def compute_match_summary(df: pl.DataFrame, match_col: str, group_col: str) -> pl.DataFrame:
    """Collapse a per-row match flag into a per-group `any_match` summary.

    any_match is True if any row in the group matched, False if rows were
    comparable but none matched, and None if the group had nothing comparable
    (no row where `match_col` could be evaluated, e.g. no InterProScan hit at all).
    """
    return (
        df.group_by(group_col)
        .agg(
            pl.col(match_col).any().alias("any_match"),
            pl.col(match_col).is_not_null().sum().alias("_comparable_count"),
        )
        .with_columns(
            pl.when(pl.col("_comparable_count") == 0).then(None).otherwise(pl.col("any_match")).alias("any_match")
        )
        .drop("_comparable_count")
    )


def build_cath_comparison(
    df_pipeline: pl.DataFrame, df_interpro: pl.DataFrame, match_columns: dict[str, str]
) -> pl.DataFrame:
    pipeline_col, interpro_col = "uniprot_id", "protein_accession"

    df_interpro_gene3d = df_interpro.filter(pl.col("analysis") == "Gene3D")
    df_pipeline = map_pipeline_id(df_pipeline, pipeline_col, interpro_col, match_columns)

    df_output = df_pipeline.join(df_interpro_gene3d, on=interpro_col, how="left").select(
        pl.col("uniprot_id"),
        pl.col("cath_label"),
        pl.col("protein_accession"),
        pl.col("signature_accession"),
    )

    df_output = df_output.with_columns(
        pl.when(pl.col("signature_accession").is_not_null() & pl.col("cath_label").is_not_null())
        .then(pl.col("signature_accession").str.replace("G3DSA:", "") == pl.col("cath_label"))
        .otherwise(None)
        .alias("cath_match")
    )

    # Propagate any_match across all domains chopped from the same protein.
    df_summary = compute_match_summary(df_output, match_col="cath_match", group_col="protein_accession")
    return df_output.join(df_summary, on="protein_accession", how="left")


def build_pfam_comparison(
    df_pipeline: pl.DataFrame, df_interpro: pl.DataFrame, match_columns: dict[str, str]
) -> pl.DataFrame:
    pipeline_col, interpro_col = "query_id", "protein_accession"

    df_interpro_pfam = df_interpro.filter(pl.col("analysis") == "Pfam")
    df_pipeline = map_pipeline_id(df_pipeline, pipeline_col, interpro_col, match_columns)
    df_pipeline = df_pipeline.filter(pl.col("db") == "PfamSDB")

    df_output = df_pipeline.join(df_interpro_pfam, on=interpro_col, how="left").select(
        pl.col("query_id"),
        pl.col("target_id"),
        pl.col("protein_accession"),
        pl.col("signature_accession"),
    )

    df_output = df_output.with_columns(pl.col("target_id").str.split("_").list.last().alias("pfam_label"))

    df_output = df_output.with_columns(
        pl.when(pl.col("signature_accession").is_not_null())
        .then(pl.col("signature_accession") == pl.col("pfam_label"))
        .otherwise(None)
        .alias("pfam_match")
    )

    # Propagate any_match across all domains chopped from the same protein.
    df_summary = compute_match_summary(df_output, match_col="pfam_match", group_col="protein_accession")
    return df_output.join(df_summary, on="protein_accession", how="left")


@app.command()
def cath(
    pipeline_output_file: Path,
    interproscan_output_file: Path,
    match_columns_file: Path,
    output_file: Path,
) -> None:
    """Check FoldSeek CATH labels against InterProScan Gene3D hits."""
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None)
    df_interpro = load_interproscan_tsv(interproscan_output_file)
    match_columns = load_match_columns(match_columns_file)

    df_output = build_cath_comparison(df_pipeline, df_interpro, match_columns)
    df_output.write_csv(output_file, separator="\t")


@app.command()
def pfam(
    pipeline_output_file: Path,
    interproscan_output_file: Path,
    match_columns_file: Path,
    output_file: Path,
) -> None:
    """Check FoldSeek Pfam hits (db == PfamSDB) against InterProScan Pfam hits."""
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None)
    df_interpro = load_interproscan_tsv(interproscan_output_file)
    match_columns = load_match_columns(match_columns_file)

    df_output = build_pfam_comparison(df_pipeline, df_interpro, match_columns)
    df_output.write_csv(output_file, separator="\t")


@app.command()
def diagnose(
    pipeline_output_file: Path,
    interproscan_output_file: Path,
    match_columns_file: Path,
    output_file: Path,
    pipeline_column: str = typer.Option("query_id", help="Pipeline column to map to InterProScan protein_accession"),
) -> None:
    """Join FoldSeek results against the full InterProScan output and report ID-mapping / hit coverage."""
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None)
    df_interpro = load_interproscan_tsv(interproscan_output_file)
    match_columns = load_match_columns(match_columns_file)

    interpro_col = "protein_accession"
    df_pipeline = map_pipeline_id(df_pipeline, pipeline_column, interpro_col, match_columns)

    pipeline_ids = set(df_pipeline[pipeline_column].to_list())
    missing = pipeline_ids - set(match_columns.keys())
    print(
        f"{len(missing)} of {len(pipeline_ids)} pipeline '{pipeline_column}' values have no entry in match_columns_file"
    )
    if missing:
        print(f"  e.g. {sorted(missing)[:10]}")

    df_output = df_pipeline.join(df_interpro, on=interpro_col, how="left")
    print(f"{df_output.shape[0]} joined rows from {df_pipeline.shape[0]} pipeline rows")

    unmatched = df_output.filter(pl.col("signature_accession").is_null())
    print(f"{unmatched.shape[0]} rows have no InterProScan hit at all")

    missing_protein_accession = df_output.filter(pl.col("db").is_not_null() & pl.col("interpro_accession").is_null())
    if missing_protein_accession.shape[0] > 0:
        print(f"{missing_protein_accession.shape[0]} rows have a FoldSeek hit but no InterPro accession:")
        print(missing_protein_accession)

    df_output.write_csv(output_file, separator="\t")


if __name__ == "__main__":
    app()
