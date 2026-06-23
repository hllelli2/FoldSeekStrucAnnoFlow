import polars as pl

from FoldSeekStrucAnnoFlow.bin.interpro_comparison import (
    build_cath_comparison,
    build_pfam_comparison,
    compute_match_summary,
)


def test_compute_match_summary_propagates_and_nulls_out_uncomparable_groups() -> None:
    df = pl.DataFrame(
        {
            "g": ["a", "a", "b", "b", "c", "c"],
            "m": [None, True, None, False, None, None],
        },
        schema={"g": pl.Utf8, "m": pl.Boolean},
    )

    summary = compute_match_summary(df, match_col="m", group_col="g").sort("g")

    assert summary.to_dicts() == [
        {"g": "a", "any_match": True},
        {"g": "b", "any_match": False},
        {"g": "c", "any_match": None},
    ]


def test_build_cath_comparison_propagates_match_to_sibling_domain() -> None:
    # d1 and d2 are two domains chopped from the same protein (P1).
    df_pipeline = pl.DataFrame(
        {
            "uniprot_id": ["d1", "d2", "d3"],
            "cath_label": ["1.10.10.10", "2.20.20.20", "9.9.9.9"],
        }
    )
    df_interpro = pl.DataFrame(
        {
            "protein_accession": ["P1", "P1"],
            "analysis": ["Gene3D", "Gene3D"],
            "signature_accession": ["G3DSA:1.10.10.10", "G3DSA:5.50.50.50"],
        }
    )
    match_columns = {"d1": "P1", "d2": "P1", "d3": "P2"}  # d3's protein (P2) has no InterProScan hits at all

    df_output = build_cath_comparison(df_pipeline, df_interpro, match_columns)

    # Exactly one any_match column should exist (regression test for the any_match/any_match_right bug).
    assert df_output.columns.count("any_match") == 1

    by_domain = dict(zip(df_output["uniprot_id"], df_output["any_match"]))
    # d2 has no matching InterPro hit on its own rows, but its sibling domain d1 (same protein) does.
    assert by_domain["d1"] is True
    assert by_domain["d2"] is True
    # d3's protein has no comparable InterProScan data at all, so its match status is unknown.
    assert by_domain["d3"] is None


def test_build_pfam_comparison_filters_to_pfamsdb_and_matches_target_suffix() -> None:
    df_pipeline = pl.DataFrame(
        {
            "query_id": ["q1", "q1", "q2"],
            "target_id": ["X_31_193_PF00001", "Y_1_10_PF00002", "Z_1_10_PF00099"],
            "db": ["PfamSDB", "afdb50", "PfamSDB"],
        }
    )
    df_interpro = pl.DataFrame(
        {
            "protein_accession": ["A1", "A2"],
            "analysis": ["Pfam", "Pfam"],
            "signature_accession": ["PF00001", "PF00003"],
        }
    )
    match_columns = {"q1": "A1", "q2": "A2"}

    df_output = build_pfam_comparison(df_pipeline, df_interpro, match_columns)

    assert df_output.columns.count("any_match") == 1
    # The afdb50 row for q1 should have been filtered out before the InterProScan join.
    assert df_output.shape[0] == 2

    by_query = dict(zip(df_output["query_id"], df_output["any_match"]))
    assert by_query["q1"] is True  # PF00001 == PF00001
    assert by_query["q2"] is False  # PF00099 != PF00003
