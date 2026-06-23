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

DEFAULT_SOURCE_DBS = "pdb,afdb50,afdb_swissprot"


def load_interproscan_tsv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, separator="\t", quote_char=None, has_header=False, new_columns=INTERPROSCAN_COLS)


def load_match_columns(path: Path) -> dict[str, str]:
    with open(path) as f:
        return cast(dict[str, str], json.load(f))


def find_structural_only_hits(
    df_foldseek: pl.DataFrame,
    df_interpro: pl.DataFrame,
    match_columns: dict[str, str],
    source_dbs: str = DEFAULT_SOURCE_DBS,
) -> pl.DataFrame:
    """Flag FoldSeek hits (from the given structural databases) by whether their
    protein has a Gene3D and/or Pfam hit anywhere in InterProScan.

    `df_interpro` should already be restricted to Gene3D/Pfam (see
    filter_interproscan_results.py) - this only checks presence, not whether the
    structural hit's own label agrees with InterProScan's.
    """
    dbs = [d.strip() for d in source_dbs.split(",") if d.strip()]
    df_foldseek = df_foldseek.filter(pl.col("db").is_in(dbs))
    df_foldseek = df_foldseek.with_columns(pl.col("query_id").replace(match_columns).alias("protein_accession"))

    gene3d_proteins = df_interpro.filter(pl.col("analysis") == "Gene3D")["protein_accession"].drop_nulls().to_list()
    pfam_proteins = df_interpro.filter(pl.col("analysis") == "Pfam")["protein_accession"].drop_nulls().to_list()

    # fill_null(False): an unmapped protein_accession (null) has no *confirmed*
    # Gene3D/Pfam hit either, so it should count as a gap, not propagate null.
    return df_foldseek.with_columns(
        pl.col("protein_accession").is_in(gene3d_proteins).fill_null(False).alias("has_gene3d"),
        pl.col("protein_accession").is_in(pfam_proteins).fill_null(False).alias("has_pfam"),
    ).with_columns((~pl.col("has_gene3d") & ~pl.col("has_pfam")).alias("no_interpro_domain_hit"))


@app.command()
def main(
    foldseek_non_cath_file: Path,
    interproscan_output_file: Path,
    match_columns_file: Path,
    output_file: Path,
    source_dbs: str = typer.Option(
        DEFAULT_SOURCE_DBS,
        help="Comma-separated FoldSeek 'db' values to treat as structural-only sources "
        "(default: pdb + both AFDB variants).",
    ),
) -> None:
    """Find FoldSeek hits (e.g. vs PDB/AFDB) for proteins with no Gene3D/Pfam hit in InterProScan."""
    df_foldseek = pl.read_csv(foldseek_non_cath_file, separator="\t", quote_char=None)
    df_interpro = load_interproscan_tsv(interproscan_output_file)
    match_columns = load_match_columns(match_columns_file)

    df_output = find_structural_only_hits(df_foldseek, df_interpro, match_columns, source_dbs)
    df_output.write_csv(output_file, separator="\t")

    # protein_accession is null for proteins match_names.py couldn't map at all; fall back to
    # query_id so each of those still counts as its own distinct case instead of collapsing
    # into a single "null" bucket under n_unique().
    protein_key = pl.coalesce(pl.col("protein_accession"), pl.col("query_id"))
    total = df_output.select(protein_key.alias("k"))["k"].n_unique()
    gaps = df_output.filter(pl.col("no_interpro_domain_hit")).select(protein_key.alias("k"))["k"].n_unique()
    unmapped_gaps = df_output.filter(pl.col("no_interpro_domain_hit") & pl.col("protein_accession").is_null())[
        "query_id"
    ].n_unique()
    print(
        f"{gaps} of {total} proteins with a [{source_dbs}] FoldSeek hit have no Gene3D or Pfam hit in InterProScan "
        f"({unmapped_gaps} of those could not be mapped to an InterProScan entry at all)."
    )


if __name__ == "__main__":
    app()
