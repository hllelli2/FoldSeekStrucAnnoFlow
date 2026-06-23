from pathlib import Path

from FoldSeekStrucAnnoFlow.bin.plot_interpro_comparison import any_match_counts


def test_any_match_counts_dedupes_per_protein_and_fills_missing_categories(tmp_dir: Path) -> None:
    comparison_file = tmp_dir / "comparison.tsv"
    comparison_file.write_text(
        "protein_accession\tany_match\n"
        "P1\ttrue\n"
        "P1\ttrue\n"  # same protein repeated (e.g. multiple domain rows) - must only count once
        "P2\tfalse\n"
        "P3\t\n"  # no comparable InterProScan data -> null
    )

    counts = any_match_counts(comparison_file)

    assert counts == {"true": 1, "false": 1, "no_data": 1}
