import json
import re
from pathlib import Path

import polars as pl
import typer

app = typer.Typer()

# Pipeline IDs look like "transcript=GENE-tN_M_sample_X_NN" (one row per chopped
# domain/sample). InterProScan reports one row per protein, "GENE-tN_M-pK". Both
# share the "GENE-tN_M" transcript stem, so the mapping between them is exact -
# not a fuzzy guess - once that stem is isolated.
_SAMPLE_SUFFIX_RE = re.compile(r"_sample_\d+_\d+$")
_PROTEIN_SUFFIX_RE = re.compile(r"-p(\d+)$")


@app.command()
def main(
    pipeline_output_file: Path,
    interproscan_output_file: Path,
    output_file: Path,
    pipeline_column: str = typer.Option(
        "uniprot_id", help="Column name in pipeline output to match against InterProScan"
    ),
) -> None:
    """Map pipeline IDs to their InterProScan protein_accession via the shared transcript stem."""
    df_pipeline = pl.read_csv(pipeline_output_file, separator="\t", quote_char=None, columns=[pipeline_column])
    df_interpro = pl.read_csv(
        interproscan_output_file,
        separator="\t",
        quote_char=None,
        has_header=False,
        new_columns=["protein_accession"],
        columns=[0],  # only read the first column by index
    )

    matches = match_transcript_stems(
        transcripts=df_pipeline[pipeline_column].to_list(),
        protein_accessions=df_interpro["protein_accession"].drop_nulls().to_list(),
    )

    if not matches:
        print("No matches found. Check input files and column names.")
        raise ValueError("No matches found.")

    unmatched = sum(1 for v in matches.values() if v is None)
    if unmatched:
        print(f"{unmatched} of {len(matches)} pipeline IDs have no matching InterProScan accession.")

    with open(output_file, "w") as f:
        json.dump(matches, f, indent=2)


def transcript_stem(pipeline_id: str) -> str:
    """Strip the "transcript=" prefix and "_sample_X_NN" chunk suffix from a pipeline ID."""
    stem = pipeline_id.removeprefix("transcript=")
    return _SAMPLE_SUFFIX_RE.sub("", stem)


def build_stem_index(protein_accessions: list[str]) -> dict[str, str]:
    """Index InterProScan protein_accessions by transcript stem.

    Keeps the lowest "-pK" isoform when a stem has more than one accession
    (every accession observed in practice is "-p1", but this stays correct if
    a stem ever has multiple isoforms).
    """
    by_stem: dict[str, list[tuple[int, str]]] = {}
    for accession in protein_accessions:
        match = _PROTEIN_SUFFIX_RE.search(accession)
        stem = accession[: match.start()] if match else accession
        isoform = int(match.group(1)) if match else 0
        by_stem.setdefault(stem, []).append((isoform, accession))

    return {stem: min(candidates)[1] for stem, candidates in by_stem.items()}


def match_transcript_stems(transcripts: list[str], protein_accessions: list[str]) -> dict[str, str | None]:
    """Map each pipeline transcript ID to the InterProScan accession sharing its stem.

    Returns None for a transcript when no InterProScan accession shares its stem,
    rather than guessing a similarly-named but unrelated accession.
    """
    stem_index = build_stem_index(protein_accessions)
    return {t: stem_index.get(transcript_stem(t)) for t in transcripts}


if __name__ == "__main__":
    app()
