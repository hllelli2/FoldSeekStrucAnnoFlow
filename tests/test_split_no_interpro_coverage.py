import polars as pl

from FoldSeekStrucAnnoFlow.bin.split_no_interpro_coverage import split_no_coverage_hits

FOLDSEEK_ROWS = [
    ("q-a", "t-a", "pdb"),  # protein A: Gene3D hit -> covered
    ("q-b", "t-b", "afdb50"),  # protein B: Pfam hit -> covered
    ("q-c", "t-c", "pdb"),  # protein C: PANTHER hit only -> has IPS, but no Gene3D/Pfam
    ("q-e", "t-e", "afdb_swissprot"),  # unmapped -> no InterProScan hit in any analysis
    ("q-f", "t-f", "PfamSDB"),  # not a source db -> filtered out entirely
]

MATCH_COLUMNS = {
    "q-a": "P-A",
    "q-b": "P-B",
    "q-c": "P-C",
    "q-e": None,  # match_names.py always emits a key per transcript, null when unmapped
    "q-f": "P-F",  # mapped, but P-F has no rows at all in the raw InterProScan output
}

INTERPRO_RAW_ROWS = [
    ("P-A", "Gene3D", "G3DSA:1.1.1.1"),
    ("P-B", "Pfam", "PF00001"),
    ("P-C", "PANTHER", "PTHR12345"),
]


def make_foldseek_df() -> pl.DataFrame:
    return pl.DataFrame(FOLDSEEK_ROWS, schema=["query_id", "target_id", "db"], orient="row")


def make_interpro_raw_df() -> pl.DataFrame:
    return pl.DataFrame(
        INTERPRO_RAW_ROWS, schema=["protein_accession", "analysis", "signature_accession"], orient="row"
    )


def test_split_no_coverage_hits_separates_no_ips_from_no_pfam_gene3d() -> None:
    no_interpro_hit, no_pfam_gene3d = split_no_coverage_hits(make_foldseek_df(), make_interpro_raw_df(), MATCH_COLUMNS)

    assert no_interpro_hit["query_id"].to_list() == ["q-e"]
    assert no_pfam_gene3d["query_id"].to_list() == ["q-c"]


def test_split_no_coverage_hits_checks_raw_interpro_not_just_mapping() -> None:
    # q-f is mapped to P-F (non-null protein_accession), but P-F has no rows at all in
    # the raw InterProScan output, so it must land in "no IPS hit at all", not be
    # mistaken for "covered" just because it had a successful ID mapping.
    no_interpro_hit, no_pfam_gene3d = split_no_coverage_hits(
        make_foldseek_df(), make_interpro_raw_df(), MATCH_COLUMNS, source_dbs="PfamSDB"
    )

    assert no_interpro_hit["query_id"].to_list() == ["q-f"]
    assert no_pfam_gene3d.shape[0] == 0
