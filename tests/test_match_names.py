from FoldSeekStrucAnnoFlow.bin.match_names import build_stem_index, match_transcript_stems, transcript_stem


def test_transcript_stem_strips_prefix_and_sample_suffix() -> None:
    assert transcript_stem("transcript=B9J08_005046-t37_1_sample_0_01") == "B9J08_005046-t37_1"
    assert transcript_stem("transcript=B9J08_005046-t37_1_sample_0_02") == "B9J08_005046-t37_1"
    # Tolerates IDs that are already bare (no prefix / no chunk suffix).
    assert transcript_stem("B9J08_005046-t37_1") == "B9J08_005046-t37_1"


def test_build_stem_index_keeps_lowest_isoform() -> None:
    index = build_stem_index(["GENE-tA_1-p2", "GENE-tA_1-p1", "OTHER-tB_1-p1"])
    assert index == {"GENE-tA_1": "GENE-tA_1-p1", "OTHER-tB_1": "OTHER-tB_1-p1"}


def test_match_transcript_stems_does_not_confuse_similarly_named_genes() -> None:
    # Regression test: CNN00765 and CNB04765 only differ by a couple of digits
    # and a chromosome letter. The old longest-common-substring matcher matched
    # CNN00765 to CNB04765's accession by coincidence; the real fix is that
    # CNN00765 has no InterProScan accession at all here, so it must map to None
    # rather than borrowing CNB04765's.
    transcripts = [
        "transcript=CNN00765-t26_1_sample_0_01",
        "transcript=CNB04765-t26_1_sample_0_01",
    ]
    protein_accessions = ["CNB04765-t26_1-p1"]

    matches = match_transcript_stems(transcripts, protein_accessions)

    assert matches["transcript=CNB04765-t26_1_sample_0_01"] == "CNB04765-t26_1-p1"
    assert matches["transcript=CNN00765-t26_1_sample_0_01"] is None


def test_match_transcript_stems_propagates_same_accession_across_domain_chunks() -> None:
    # Two domain chunks chopped from the same transcript both map to the one
    # protein accession for that transcript.
    transcripts = [
        "transcript=CNB04290-t26_1_sample_0_01",
        "transcript=CNB04290-t26_1_sample_0_02",
    ]
    protein_accessions = ["CNB04290-t26_1-p1"]

    matches = match_transcript_stems(transcripts, protein_accessions)

    assert matches["transcript=CNB04290-t26_1_sample_0_01"] == "CNB04290-t26_1-p1"
    assert matches["transcript=CNB04290-t26_1_sample_0_02"] == "CNB04290-t26_1-p1"
