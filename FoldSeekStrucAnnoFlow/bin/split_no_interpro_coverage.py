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


def split_no_coverage_hits(
    df_foldseek: pl.DataFrame,
    df_interpro_raw: pl.DataFrame,
    match_columns: dict[str, str],
    source_dbs: str = DEFAULT_SOURCE_DBS,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Among FoldSeek hits (from the given structural databases) for proteins with no
    Gene3D/Pfam hit, split the rows into two finer-grained cases:
      - no InterProScan hit in *any* analysis
      - some other InterProScan hit (e.g. PANTHER/SUPERFAMILY), just not Gene3D/Pfam

    `df_interpro_raw` and `match_columns` must come from the *unfiltered* InterProScan
    output. A protein whose only hits are outside Gene3D/Pfam is absent from the
    Gene3D/Pfam-filtered file (see filter_interproscan_results.py) and from any
    match_columns built against it, so that file alone can't tell the two cases apart.
    """
    dbs = [d.strip() for d in source_dbs.split(",") if d.strip()]
    df_foldseek = df_foldseek.filter(pl.col("db").is_in(dbs))
    df_foldseek = df_foldseek.with_columns(pl.col("query_id").replace(match_columns).alias("protein_accession"))

    any_hit_proteins = df_interpro_raw["protein_accession"].drop_nulls().to_list()
    gene3d_proteins = df_interpro_raw.filter(pl.col("analysis") == "Gene3D")["protein_accession"].drop_nulls().to_list()
    pfam_proteins = df_interpro_raw.filter(pl.col("analysis") == "Pfam")["protein_accession"].drop_nulls().to_list()

    df_foldseek = df_foldseek.with_columns(
        pl.col("protein_accession").is_in(gene3d_proteins).fill_null(False).alias("has_gene3d"),
        pl.col("protein_accession").is_in(pfam_proteins).fill_null(False).alias("has_pfam"),
        pl.col("protein_accession").is_in(any_hit_proteins).fill_null(False).alias("has_any_interpro_hit"),
    )

    no_coverage = df_foldseek.filter(~pl.col("has_gene3d") & ~pl.col("has_pfam"))
    no_interpro_hit = no_coverage.filter(~pl.col("has_any_interpro_hit"))
    no_pfam_or_gene3d = no_coverage.filter(pl.col("has_any_interpro_hit"))
    return no_interpro_hit, no_pfam_or_gene3d


@app.command()
def main(
    foldseek_non_cath_file: Path,
    interproscan_raw_file: Path,
    match_columns_file: Path,
    no_interpro_hit_file: Path,
    no_pfam_gene3d_file: Path,
    source_dbs: str = typer.Option(
        DEFAULT_SOURCE_DBS,
        help="Comma-separated FoldSeek 'db' values to treat as structural-only sources "
        "(default: pdb + both AFDB variants).",
    ),
) -> None:
    """Split FoldSeek hits with no Gene3D/Pfam coverage into 'no InterProScan hit at
    all' vs 'has other InterProScan hits, just not Gene3D/Pfam', writing each to its
    own CSV.

    interproscan_raw_file and match_columns_file must be the *unfiltered* InterProScan
    output and a match_columns.json built against it (via match_names.py) - not the
    Gene3D/Pfam-filtered file used elsewhere in this pipeline, which can't distinguish
    the two cases.
    """
    df_foldseek = pl.read_csv(foldseek_non_cath_file, separator="\t", quote_char=None)
    df_interpro_raw = load_interproscan_tsv(interproscan_raw_file)
    match_columns = load_match_columns(match_columns_file)

    no_interpro_hit, no_pfam_gene3d = split_no_coverage_hits(df_foldseek, df_interpro_raw, match_columns, source_dbs)

    no_interpro_hit.write_csv(no_interpro_hit_file)
    no_pfam_gene3d.write_csv(no_pfam_gene3d_file)

    print(
        f"{no_interpro_hit.shape[0]} hit rows ({no_interpro_hit['query_id'].n_unique()} proteins) have no "
        f"InterProScan hit in any analysis -> {no_interpro_hit_file}"
    )
    print(
        f"{no_pfam_gene3d.shape[0]} hit rows ({no_pfam_gene3d['query_id'].n_unique()} proteins) have other "
        f"InterProScan hits but no Gene3D/Pfam -> {no_pfam_gene3d_file}"
    )


if __name__ == "__main__":
    app()
