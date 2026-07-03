import subprocess
import sys
from pathlib import Path

import pandas as pd

from FoldSeekStrucAnnoFlow.bin.transform_consensus import transform_consensus

TRANSFORM_CONSENSUS_SCRIPT = (
    Path(__file__).resolve().parents[1] / "FoldSeekStrucAnnoFlow" / "bin" / "transform_consensus.py"
)

STRIDE_HEADER = "id\tchain_id\tnum_helix_strand_turn\tnum_helix\tnum_strand\tnum_helix_strand\tnum_turn\n"


def _write_consensus_row(path, target_id, high_dom="NA", med_dom="NA", low_dom="NA"):
    # headers: target_id, MD5, nres, high, med, low, high_dom, med_dom, low_dom
    path.write_text(f"{target_id}\tignored_md5\t150\t1\t1\t0\t{high_dom}\t{med_dom}\t{low_dom}\n")


def test_transform_consensus_na_fills_missing_stride(tmp_path):
    consensus_file = tmp_path / "consensus.tsv"
    _write_consensus_row(consensus_file, "test_target", high_dom="1-50")

    md5_file = tmp_path / "md5.tsv"
    md5_file.write_text("pdb_file\tmd5\ntest_target_01.pdb\tabc123\n")

    stride_dir = tmp_path / "stride"
    stride_dir.mkdir()
    (stride_dir / "batch1.stride.summary").write_text(STRIDE_HEADER + "other_target_01.pdb\tA\t5\t2\t1\t3\t2\n")

    output_file = tmp_path / "out.tsv"
    transform_consensus(str(consensus_file), str(output_file), str(md5_file), str(stride_dir))

    result = pd.read_csv(output_file, sep="\t", keep_default_na=False)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["uniprot_id"] == "test_target_01"
    assert row["md5_domain"] == "abc123"
    for key in ["num_helix_strand_turn", "num_helix", "num_strand", "num_helix_strand", "num_turn"]:
        assert row[key] == "NA"


def test_transform_consensus_skips_missing_md5_and_keeps_numbering(tmp_path):
    consensus_file = tmp_path / "consensus.tsv"
    # high_dom -> domain _01 (skipped, no md5), med_dom -> domain _02 (kept)
    _write_consensus_row(consensus_file, "test_target", high_dom="1-50", med_dom="60-100")

    md5_file = tmp_path / "md5.tsv"
    md5_file.write_text("pdb_file\tmd5\ntest_target_02.pdb\tdef456\n")

    stride_dir = tmp_path / "stride"
    stride_dir.mkdir()
    (stride_dir / "batch1.stride.summary").write_text(
        STRIDE_HEADER + "test_target_01.pdb\tA\t9\t9\t0\t9\t0\n" + "test_target_02.pdb\tA\t7\t3\t2\t5\t2\n"
    )

    output_file = tmp_path / "out.tsv"
    transform_consensus(str(consensus_file), str(output_file), str(md5_file), str(stride_dir))

    result = pd.read_csv(output_file, sep="\t", keep_default_na=False)
    assert len(result) == 1
    row = result.iloc[0]
    # domain _01 was skipped (no md5), but _02 keeps its own number, not renumbered to _01
    assert row["uniprot_id"] == "test_target_02"
    assert row["md5_domain"] == "def456"
    assert str(row["num_helix"]) == "3"
    assert str(row["num_strand"]) == "2"


def _run_cli(args, tmp_path):
    return subprocess.run(
        [sys.executable, str(TRANSFORM_CONSENSUS_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )


def test_transform_consensus_still_raises_on_missing_input_file(tmp_path):
    md5_file = tmp_path / "md5.tsv"
    md5_file.write_text("pdb_file\tmd5\n")
    stride_dir = tmp_path / "stride"
    stride_dir.mkdir()

    result = _run_cli(["-i", "missing.tsv", "-o", "out.tsv", "-m", str(md5_file), "-s", str(stride_dir)], tmp_path)
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_transform_consensus_still_raises_on_missing_md5_file(tmp_path):
    input_file = tmp_path / "consensus.tsv"
    _write_consensus_row(input_file, "test_target")
    stride_dir = tmp_path / "stride"
    stride_dir.mkdir()

    result = _run_cli(
        ["-i", str(input_file), "-o", "out.tsv", "-m", "missing_md5.tsv", "-s", str(stride_dir)], tmp_path
    )
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_transform_consensus_still_raises_on_missing_stride_dir(tmp_path):
    input_file = tmp_path / "consensus.tsv"
    _write_consensus_row(input_file, "test_target")
    md5_file = tmp_path / "md5.tsv"
    md5_file.write_text("pdb_file\tmd5\n")

    result = _run_cli(
        ["-i", str(input_file), "-o", "out.tsv", "-m", str(md5_file), "-s", "missing_stride_dir"], tmp_path
    )
    assert result.returncode != 0
    assert "does not exist or is invalid" in result.stderr
