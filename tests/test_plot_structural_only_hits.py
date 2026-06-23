import polars as pl

from FoldSeekStrucAnnoFlow.bin.plot_structural_only_hits import gap_proteins_by_db, overall_coverage_counts

ROWS = [
    # query_id, db, protein_accession, has_gene3d, has_pfam, no_interpro_domain_hit
    ("q-a", "pdb", "P-A", True, False, False),  # Gene3D only
    ("q-a", "afdb50", "P-A", True, False, False),  # same protein, second hit - must not double count
    ("q-b", "afdb50", "P-B", False, True, False),  # Pfam only
    ("q-c", "pdb", "P-C", True, True, False),  # both
    ("q-d", "pdb", "P-D", False, False, True),  # gap, hit by both pdb and afdb50
    ("q-d", "afdb50", "P-D", False, False, True),
    ("q-e", "afdb_swissprot", None, False, False, True),  # gap, unmapped, hit by afdb_swissprot only
]


def make_df() -> pl.DataFrame:
    return pl.DataFrame(
        ROWS,
        schema=["query_id", "db", "protein_accession", "has_gene3d", "has_pfam", "no_interpro_domain_hit"],
        orient="row",
    )


def test_overall_coverage_counts_dedupes_per_protein_and_handles_unmapped() -> None:
    counts = overall_coverage_counts(make_df())

    assert counts == {
        "Gene3D only": 1,
        "Pfam only": 1,
        "Both": 1,
        "No coverage (gap)": 2,
    }


def test_gap_proteins_by_db_counts_overlap_across_dbs() -> None:
    counts_by_db, total_gap_proteins = gap_proteins_by_db(make_df())

    assert total_gap_proteins == 2  # P-D and the unmapped q-e protein
    assert counts_by_db == {
        "afdb50": 1,  # P-D
        "afdb_swissprot": 1,  # unmapped q-e
        "pdb": 1,  # P-D
    }
