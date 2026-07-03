# Adapted from https://github.com/UCLOrengoGroup/domain-annotation-pipeline/blob/main/docker/script/create_stride_summary.py

"""
Script to summarize secondary structure information from one or more STRIDE files
into a tab-separated CSV file with headers.

Usage:
    transform_consensus.py -o <output_summary_file.csv> <stride_file1> [<stride_file2> ...]

Raises:
    FileNotFoundError: If any STRIDE file does not exist.
    ValueError: If a STRIDE file is improperly formatted.
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import TypedDict


class StrideSummary(TypedDict):
    id: str | None
    chain_id: str | None
    num_helix_strand_turn: int
    num_helix: int
    num_strand: int
    num_helix_strand: int
    num_turn: int


def parse_stride_file(file_path: str) -> StrideSummary:
    """
    Parses a STRIDE file and extracts secondary structure information.

    Args:
        file_path (str): Path to the STRIDE file.

    Returns:
        dict: A dictionary containing summarized secondary structure information.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"STRIDE file '{file_path}' does not exist.")

    summary: StrideSummary = {
        "id": None,
        "chain_id": None,
        "num_helix_strand_turn": 0,
        "num_helix": 0,
        "num_strand": 0,
        "num_helix_strand": 0,
        "num_turn": 0,
    }

    found_chn = False
    try:
        with open(file_path, "r", encoding="latin-1") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CHN"):
                    found_chn = True
                    parts = line.split()
                    summary["id"] = Path(file_path).with_suffix(".pdb").name
                    summary["chain_id"] = parts[2]
                elif line.startswith("LOC"):
                    structure_type = line.split()[1]
                    if "HELIX" in structure_type.upper():
                        summary["num_helix"] += 1
                    elif "STRAND" in structure_type.upper():
                        summary["num_strand"] += 1
                    elif "TURN" in structure_type.upper():
                        summary["num_turn"] += 1

            summary["num_helix_strand_turn"] = summary["num_helix"] + summary["num_strand"] + summary["num_turn"]
            summary["num_helix_strand"] = summary["num_helix"] + summary["num_strand"]
    except Exception as e:
        raise ValueError(f"Error parsing STRIDE file '{file_path}': {e}")

    if not found_chn:
        raise ValueError(f"No CHN record found in STRIDE file '{file_path}' (degenerate/empty structure?)")

    return summary


def write_summary_to_tsv(summaries: list[StrideSummary], output_file: str) -> None:
    """
    Writes the summarized secondary structure information to a tab-separated CSV file.

    Args:
        summaries (list): A list of dictionaries containing summarized secondary structure information.
        output_file (str): Path to the output TSV file.

    Raises:
        IOError: If there is an issue writing to the file.
    """
    try:
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "chain_id",
                    "num_helix_strand_turn",
                    "num_helix",
                    "num_strand",
                    "num_helix_strand",
                    "num_turn",
                ],
                delimiter="\t",
            )
            writer.writeheader()
            writer.writerows(summaries)
    except IOError as e:
        raise IOError(f"Error writing to TSV file '{output_file}': {e}")


def main(output_file: str, stride_dir: str, stride_suffix: str = ".stride") -> None:
    """
    Main function to parse multiple STRIDE files and write the summary to a TSV file.

    Args:
        output_file (str): Path to the output TSV file.
        stride_files (list): List of paths to STRIDE files.
    """
    summaries = []
    error_count = 0

    stride_filenames = [f for f in os.listdir(stride_dir) if f.endswith(stride_suffix)]

    for stride_file in stride_filenames:
        stride_path = os.path.join(stride_dir, stride_file)
        print(f"Processing STRIDE file: {stride_file}")
        try:
            summary = parse_stride_file(stride_path)
        except (FileNotFoundError, ValueError) as e:
            print(f"WARNING: skipping '{stride_file}': {e}", file=sys.stderr)
            error_count += 1
            continue
        summaries.append(summary)

    write_summary_to_tsv(summaries, output_file)
    print(f"Summary written: {len(summaries)} of {len(stride_filenames)} STRIDE files summarized to '{output_file}'.")
    if error_count > 0:
        print(f"WARNING: {error_count} STRIDE file(s) skipped due to parse errors", file=sys.stderr)

    print("Done")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Summarize secondary structure information from STRIDE files into a tab-separated CSV file."
    )

    argparser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Path to the output summary file (tab-separated CSV).",
    )

    argparser.add_argument(
        "-d",
        "--stride_dir",
        type=str,
        default=".",
        help="Directory of STRIDE files to parse.",
    )

    argparser.add_argument(
        "--suffix",
        type=str,
        default=".stride",
        help="Suffix to use when searching for STRIDE files.",
    )

    args = argparser.parse_args()
    output_file = args.output
    stride_dir = args.stride_dir
    stride_suffix = args.suffix

    if not stride_dir:
        print("No STRIDE directory provided.")
        sys.exit(1)

    if not output_file:
        print("No output file specified. Please provide an output file path.")
        sys.exit(1)

    main(output_file, stride_dir, stride_suffix)
