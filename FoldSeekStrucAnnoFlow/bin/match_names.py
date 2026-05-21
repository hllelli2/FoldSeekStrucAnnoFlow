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
    output_file: Path,
    pipeline_column: str = typer.Option(
        "uniprot_id", help="Column name in pipeline output to match against InterProScan"
    ),
) -> None:
    """Match transcript names from pipeline output to InterProScan results."""
    # Load data
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None, columns=[pipeline_column])
    df_interpro = pl.read_csv(
        interproscan_output_file,
        separator="\t",
        quote_char=None,
        has_header=False,
        new_columns=["protein_accession"],
        columns=[0],  # only read the first column by index
    )
    # give df_interpro the expected column names if not already present
    # if not all(col in df_interpro.columns for col in INTERPROSCAN_COLS):
    #     df_interpro.columns = INTERPROSCAN_COLS

    # Assume 'transcript_id' in pipeline and 'protein_id' in InterProScan
    matches = match_polars_columns(
        df_transcripts=df_pipeline, df_others=df_interpro, transcript_col=pipeline_column, other_col="protein_accession"
    )

    # if matches is empty.

    if not matches:
        print("No matches found. Check input files and column names.")
        raise ValueError("No matches found.")

    with open(output_file, "w") as f:
        json.dump(matches, f, indent=2)


def build_lcs_index(keys: list[str]) -> dict:
    """Pre-process keys into suffix structures for fast matching."""
    index = {}
    for key in keys:
        # Store all substrings of length >= min_len as lookup entries
        for start in range(len(key)):
            for end in range(start + 4, len(key) + 1):  # min length 4
                sub = key[start:end]
                if sub not in index:
                    index[sub] = []
                index[sub].append(key)
    return index


def longest_common_substring(s1: str, s2: str) -> str:
    """Find the longest common substring between two strings."""
    shorter, longer = (s1, s2) if len(s1) <= len(s2) else (s2, s1)
    best = ""
    for start in range(len(shorter)):
        for end in range(len(shorter), start, -1):
            candidate = shorter[start:end]
            if len(candidate) <= len(best):
                break  # Can't beat current best from this start
            if candidate in longer:
                best = candidate
                break
    return best


def match_indexes(
    transcripts: list[str],
    others: list[str],
    min_match_len: int = 6,
    suffix_index: dict = None,
) -> dict[str, str | None]:
    if suffix_index is None:
        suffix_index = build_lcs_index(others)

    results = {}
    for t in transcripts:
        best_match = None
        best_len = min_match_len - 1

        for length in range(len(t), best_len, -1):
            if length <= best_len:
                break
            found = False
            for start in range(len(t) - length + 1):
                sub = t[start : start + length]
                if sub in suffix_index:
                    for candidate in suffix_index[sub]:
                        lcs = longest_common_substring(t, candidate)
                        if len(lcs) > best_len:
                            best_len = len(lcs)
                            best_match = candidate
                    found = True
                    break
            if found:
                break

        results[t] = best_match  # <-- correctly inside the outer loop
    return results


def match_polars_columns(
    df_transcripts: pl.DataFrame | pl.Series,
    df_others: pl.DataFrame | pl.Series,
    transcript_col: str = None,
    other_col: str = None,
) -> pl.Series:
    """
    Match two Polars columns/Series using longest common substring.

    Can accept either a Series directly or a DataFrame + column name.
    Returns a Series of matched values (null where no match found).
    """
    # Unwrap to Python lists — LCS logic is pure Python
    if isinstance(df_transcripts, pl.Series):
        transcripts = df_transcripts.to_list()
    else:
        transcripts = df_transcripts[transcript_col].to_list()

    if isinstance(df_others, pl.Series):
        others = df_others.drop_nulls().to_list()
    else:
        others = df_others[other_col].drop_nulls().to_list()

    # Build index once, match all transcripts
    suffix_index = build_lcs_index(others)
    matches = match_indexes(transcripts, others, suffix_index=suffix_index)

    return matches


if __name__ == "__main__":
    app()
