import polars as pl

from FoldSeekStrucAnnoFlow.bin.find_structural_only_hits import find_structural_only_hits

FOLDSEEK_ROWS = [
    ("q-a", "t-a", "pdb"),  # protein A: pdb hit, has a Gene3D hit -> covered
    ("q-b", "t-b", "afdb50"),  # protein B: afdb50 hit, has a Pfam hit -> covered
    ("q-c", "t-c", "pdb"),  # protein C: pdb hit, no Gene3D/Pfam at all -> gap
    ("q-d", "t-d", "PfamSDB"),  # protein D: only a PfamSDB hit -> filtered out (not a source db)
    ("q-e", "t-e", "afdb_swissprot"),  # protein E: match_names.py found no mapping for this one -> gap
]

MATCH_COLUMNS = {
    "q-a": "P-A",
    "q-b": "P-B",
    "q-c": "P-C",
    "q-d": "P-D",
    "q-e": None,  # match_names.py always emits a key per transcript, null when unmapped
}

INTERPRO_ROWS = [
    ("P-A", "Gene3D", "G3DSA:1.1.1.1"),
    ("P-B", "Pfam", "PF00001"),
]


def make_foldseek_df() -> pl.DataFrame:
    return pl.DataFrame(FOLDSEEK_ROWS, schema=["query_id", "target_id", "db"], orient="row")


def make_interpro_df() -> pl.DataFrame:
    return pl.DataFrame(INTERPRO_ROWS, schema=["protein_accession", "analysis", "signature_accession"], orient="row")


def test_find_structural_only_hits_flags_proteins_with_no_interpro_coverage() -> None:
    df = find_structural_only_hits(make_foldseek_df(), make_interpro_df(), MATCH_COLUMNS)

    by_query = {row["query_id"]: row for row in df.to_dicts()}

    assert "q-d" not in by_query  # PfamSDB isn't a structural source db, filtered out entirely

    assert by_query["q-a"]["has_gene3d"] is True
    assert by_query["q-a"]["no_interpro_domain_hit"] is False

    assert by_query["q-b"]["has_pfam"] is True
    assert by_query["q-b"]["no_interpro_domain_hit"] is False

    assert by_query["q-c"]["has_gene3d"] is False
    assert by_query["q-c"]["has_pfam"] is False
    assert by_query["q-c"]["no_interpro_domain_hit"] is True

    # unmapped query (null in match_columns) can't be confirmed in InterProScan either
    assert by_query["q-e"]["protein_accession"] is None
    assert by_query["q-e"]["no_interpro_domain_hit"] is True


def test_find_structural_only_hits_respects_custom_source_dbs() -> None:
    df = find_structural_only_hits(make_foldseek_df(), make_interpro_df(), MATCH_COLUMNS, source_dbs="PfamSDB")

    assert df["query_id"].to_list() == ["q-d"]
