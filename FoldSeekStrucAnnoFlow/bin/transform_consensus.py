# Adapted from https://github.com/UCLOrengoGroup/domain-annotation-pipeline/blob/main/docker/script/transform_consensus.py
#

import argparse
import os
import sys

import pandas as pd  # type: ignore[import-untyped]

DEFAULT_STRIDE_SUMMARY_SUFFIX = ".stride.summary"

parser = argparse.ArgumentParser(
    description="Transforms the consensus data.",
)

parser.add_argument(
    "--input_file",
    "-i",
    type=str,
    required=True,
    help="Path to the input file containing consensus data",
)
parser.add_argument(
    "--output_file",
    "-o",
    type=str,
    required=True,
    help="Path to the output file for transformed data",
)
parser.add_argument(
    "--md5_file",
    "-m",
    type=str,
    required=True,
    help="Path to the MD5 file for PDB files",
)
parser.add_argument(
    "--stride_dir",
    "-s",
    type=str,
    required=True,
    help="Path to STRIDE summary file directory",
)

parser.add_argument(
    "--stride_summary_suffix",
    type=str,
    default=DEFAULT_STRIDE_SUMMARY_SUFFIX,
    help="Suffix for STRIDE summary files (default: .stride.summary)",
)


def read_md5_file(md5_file: str) -> dict[str, str]:
    df = pd.read_csv(md5_file, sep="\t")
    md5_lookup = dict(zip(df["pdb_file"], df["md5"]))
    return md5_lookup


def calculate_nres(domain: str) -> int:
    fragments = domain.split("_")
    total = 0
    for frag in fragments:
        start, end = map(int, frag.split("-"))
        total += end - start + 1
    return total


def read_stride_summary(file_path: str) -> dict[str, dict[str, str]]:
    """
    Reads a STRIDE summary file (TSV) and returns a dictionary of dictionaries indexed by 'id'.
    """
    stride_data_by_id = dict()
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Stride file '{file_path}' does not exist.")

    expected_keys = [
        "id",
        "chain_id",
        "num_helix_strand_turn",
        "num_helix",
        "num_strand",
        "num_helix_strand",
        "num_turn",
    ]

    with open(file_path, "r") as f:
        header = f.readline().strip().split("\t")
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != len(header):
                raise ValueError(f"Invalid format in stride file: {file_path}")
            stride_data = {}
            for key, value in zip(header, parts):
                if key not in expected_keys:
                    raise ValueError(f"Unexpected key '{key}' in stride file: {file_path}")
                stride_data[key] = value
            stride_id = stride_data["id"]
            stride_data_by_id[stride_id] = stride_data

    if not stride_data_by_id:
        raise ValueError(f"No data found in stride file: {file_path}")

    return stride_data_by_id


def transform_consensus(
    input_file: str,
    output_file: str,
    md5_file: str,
    stride_dir: str,
    stride_summary_suffix: str = DEFAULT_STRIDE_SUMMARY_SUFFIX,
) -> None:
    headers = [
        "target_id",
        "MD5",
        "nres",
        "high",
        "med",
        "low",
        "high_dom",
        "med_dom",
        "low_dom",
    ]
    df = pd.read_csv(input_file, sep="\t", names=headers)

    md5_lookup = read_md5_file(md5_file)

    # Read all stride summary files and combine their data
    all_stride_data_by_id = {}
    stride_files = [os.path.join(stride_dir, f) for f in os.listdir(stride_dir) if f.endswith(stride_summary_suffix)]
    for stride_file in stride_files:
        _stride_data = read_stride_summary(stride_file)
        all_stride_data_by_id.update(_stride_data)

    output_rows = []
    stride_keys = [
        "num_helix_strand_turn",
        "num_helix",
        "num_strand",
        "num_helix_strand",
        "num_turn",
    ]
    stride_missing_count = 0
    md5_missing_count = 0

    for idx, row in df.iterrows():
        uniprot_id = row["target_id"]
        domain_count = 1

        all_domains = []

        for level in ["high", "med"]:
            dom_str = row[f"{level}_dom"]
            if isinstance(dom_str, str) and dom_str.lower() != "na":
                domains = dom_str.split(",")
                for domain in domains:
                    all_domains.append((domain, level))  # Store as tuple: (domain, level)

        # Sort all domains by their lowest start residue
        all_domains = sorted(all_domains, key=lambda d: min(int(frag.split("-")[0]) for frag in d[0].split("_")))
        for domain, level in all_domains:
            domain_id = f"{uniprot_id}_{domain_count:02d}"
            pdb_filename = f"{domain_id}.pdb"

            nres = calculate_nres(domain)
            num_segments = domain.count("_") + 1

            if pdb_filename not in md5_lookup:
                print(f"WARNING: MD5 not found for domain '{pdb_filename}', skipping row", file=sys.stderr)
                md5_missing_count += 1
                domain_count += 1
                continue

            if pdb_filename not in all_stride_data_by_id:
                print(
                    f"WARNING: Stride summary data not found for ID '{pdb_filename}', filling SSE columns with NA",
                    file=sys.stderr,
                )
                stride_missing_count += 1
                stride_data = {}
            else:
                stride_data = all_stride_data_by_id[pdb_filename]

            md5 = md5_lookup[pdb_filename]

            row_data = [domain_id, md5, level, domain, nres, num_segments]
            for key in stride_keys:
                row_data.append(stride_data.get(key, "NA"))

            output_rows.append(row_data)
            domain_count += 1

    print(f"Transformed {len(output_rows)} domain rows from {len(df)} consensus entries")
    if stride_missing_count > 0:
        print(
            f"WARNING: {stride_missing_count} domain(s) had no STRIDE summary data (SSE columns set to NA)",
            file=sys.stderr,
        )
    if md5_missing_count > 0:
        print(f"WARNING: {md5_missing_count} domain(s) had no MD5 entry and were skipped", file=sys.stderr)

    if not output_rows and len(df) > 0:
        raise ValueError(
            "No domain rows were produced from a non-empty consensus input — "
            "check --stride_dir and --md5_file for systemic errors."
        )

    column_names = [
        "uniprot_id",
        "md5_domain",
        "consensus_level",
        "chopping",
        "nres_domain",
        "num_segments",
    ] + stride_keys

    output_df = pd.DataFrame(output_rows, columns=column_names)
    output_df.to_csv(output_file, sep="\t", index=False)


# CLI use
if __name__ == "__main__":
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    md5_file = args.md5_file
    stride_dir = args.stride_dir
    stride_summary_suffix = args.stride_summary_suffix

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    if not os.path.exists(md5_file):
        raise FileNotFoundError(f"MD5 file '{md5_file}' does not exist.")

    if not os.path.exists(stride_dir):
        raise ValueError("Stride directory does not exist or is invalid.")

    transform_consensus(input_file, output_file, md5_file, stride_dir, stride_summary_suffix)
