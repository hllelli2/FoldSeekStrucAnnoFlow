import json
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


@app.command()
def main(
    pipeline_output_file: Path,
    interproscan_output_file: Path,
    match_columns_file: Path,
    output_file: Path,
):
    """Match transcript names from pipeline output to InterProScan results."""
    # Load data
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None)
    df_interpro = pl.read_csv(
        interproscan_output_file,
        separator="\t",
        quote_char=None,
        has_header=False,
        new_columns=INTERPROSCAN_COLS,
    )

    with open(match_columns_file) as f:
        match_columns = json.load(f)

    df_interpro_pfam = df_interpro.filter(pl.col("analysis") == "Pfam")

    pipeline_col = "query_id"
    interpro_col = "protein_accession"

    df_pipeline = df_pipeline.with_columns(pl.col(pipeline_col).replace(match_columns).alias(interpro_col))

    df_pipeline = df_pipeline.filter(pl.col("db") == "PfamSDB")

    df_output = df_pipeline.join(
        df_interpro_pfam,
        on=interpro_col,
        how="left",
    )

    # subset based on specific columns which are : cath_label, protein_accession, signature_accession

    df_output = df_output.select(
        pl.col("query_id"),
        pl.col("target_id"),
        pl.col("protein_accession"),
        pl.col("signature_accession"),
    )

    #     # In the signature_accession column, I want to remove the G3DSA: out of the G3DSA:3.90.79.10
    df_output = df_output.with_columns(pl.col("target_id").str.split("_").list.last().alias("pfam_label"))
    df_output = df_output.with_columns(
        pl.when(pl.col("signature_accession").is_not_null())
        .then(pl.col("signature_accession") == pl.col("pfam_label"))
        .otherwise(None)
        .alias("pfam_match")
    )
    print(df_output.head())


#     df_summary = df_output.group_by("uniprot_id").agg(
#         pl.col("cath_match").drop_nulls().any().alias("any_match"),
#         pl.col("cath_label").filter(pl.col("signature_accession").is_not_null()).drop_nulls().len().alias("label_count")
#     ).with_columns(
#         pl.when(pl.col("label_count") == 0)
#         .then(None)
#         .otherwise(pl.col("any_match"))
#         .alias("any_match")
# ).drop("label_count")


#     df_summary.write_csv(output_file, separator="\t")


if __name__ == "__main__":
    app()
