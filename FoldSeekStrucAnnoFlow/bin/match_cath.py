from pathlib import Path

import polars as pl
import typer

app = typer.Typer()


CATH_DESCRIPTION_COLUMN_NAME = "CATH_annotation"


@app.command()
def main(pipeline_output_file: Path = typer.Argument(..., help="Path to the pipeline output file")) -> None:
    print(f"Loading pipeline output from: {pipeline_output_file}")
    cath_names_df = load_cath_names()
    df = load_tsv(pipeline_output_file)
    print(df.columns)
    if CATH_DESCRIPTION_COLUMN_NAME in df.columns:
        print("CATH annotation column already exists in the pipeline output. Skipping CATH matching.")
        return

    # Replace string "None" with actual null first
    df = df.with_columns(pl.col("cath_label").replace("None", None))

    # Then join
    df = df.with_columns(pl.col("cath_label").str.extract(r"^(\d+\.\d+\.\d+\.\d+)", 1).alias("cath_label")).join(
        cath_names_df.select(["cath_label", CATH_DESCRIPTION_COLUMN_NAME]), on="cath_label", how="left"
    )

    df.write_csv(
        pipeline_output_file,  # .with_suffix(".cath.tsv"),
        separator="\t",
    )


def load_tsv(file_path: Path) -> pl.DataFrame:
    df = pl.read_csv(file_path, has_header=True, separator="\t")
    return df


def load_cath_names() -> pl.DataFrame:
    cath_names_file = Path(__file__).parent.parent / "assets" / "cath-names.txt"
    cath_names_df = pl.read_csv(cath_names_file, has_header=False, skip_lines=16, separator="\t")
    cath_names_df = (
        cath_names_df.with_columns(
            pl.col("column_1").str.split("    ")  # 4 spaces
        )
        .with_columns(
            pl.col("column_1").list.to_struct(fields=["cath_label", "pdb_file", CATH_DESCRIPTION_COLUMN_NAME])
        )
        .unnest("column_1")
        .with_columns(pl.col(CATH_DESCRIPTION_COLUMN_NAME).str.strip_chars(":"))
    )
    return cath_names_df


if __name__ == "__main__":
    app()
