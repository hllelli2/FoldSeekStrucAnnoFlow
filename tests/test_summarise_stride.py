import pytest

from FoldSeekStrucAnnoFlow.bin.summarise_stride import parse_stride_file


def _write_stride(path, extra_lines=()):
    """Write a minimal valid stride file with optional extra lines."""
    lines = [
        "CHN  test.pdb A\n",
        "LOC  AlphaHelix    MET     1  A   LYS    10 A\n",
        "LOC  AlphaHelix    GLY    15  A   ALA    20 A\n",
        "LOC  Strand         VAL    25  A   ILE    30 A\n",
        "LOC  TurnI          SER    35  A   ASP    38 A\n",
    ]
    path.write_bytes(b"".join(line.encode() for line in lines) + b"".join(extra_lines))


def test_parse_stride_file_counts_secondary_structure(tmp_path):
    stride = tmp_path / "test.stride"
    _write_stride(stride)

    result = parse_stride_file(str(stride))

    assert result["num_helix"] == 2
    assert result["num_strand"] == 1
    assert result["num_turn"] == 1
    assert result["num_helix_strand"] == 3
    assert result["num_helix_strand_turn"] == 4
    assert result["chain_id"] == "A"


def test_parse_stride_file_handles_non_utf8_bytes(tmp_path):
    """stride can emit non-UTF-8 bytes (e.g. 0xed) in atom/residue fields.
    parse_stride_file must not raise UnicodeDecodeError on such files."""
    stride = tmp_path / "non_utf8.stride"
    # \xed is an invalid UTF-8 continuation byte; embed it in a non-structural line
    _write_stride(stride, extra_lines=[b"REM  broken\xed bytes here\n"])

    result = parse_stride_file(str(stride))

    assert result["num_helix"] == 2
    assert result["num_strand"] == 1
    assert result["chain_id"] == "A"


def test_parse_stride_file_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_stride_file("/nonexistent/path/missing.stride")
