import pytest

from FoldSeekStrucAnnoFlow.bin.summarise_stride import main, parse_stride_file


def _write_stride(path, extra_lines=(), include_chn=True):
    """Write a minimal valid stride file with optional extra lines."""
    lines = []
    if include_chn:
        lines.append("CHN  test.pdb A\n")
    lines += [
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


def test_parse_stride_file_id_derived_from_filename(tmp_path):
    stride = tmp_path / "A0A2R8YEH3_01.stride"
    _write_stride(stride)

    result = parse_stride_file(str(stride))

    assert result["id"] == "A0A2R8YEH3_01.pdb"


def test_parse_stride_file_raises_on_missing_chn(tmp_path):
    stride = tmp_path / "no_chn.stride"
    _write_stride(stride, include_chn=False)

    with pytest.raises(ValueError):
        parse_stride_file(str(stride))


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


def test_main_skips_bad_file_among_good_ones(tmp_path):
    _write_stride(tmp_path / "good_one.stride")
    _write_stride(tmp_path / "good_two.stride")
    _write_stride(tmp_path / "bad.stride", include_chn=False)

    output_file = tmp_path / "summary.tsv"
    main(str(output_file), str(tmp_path), ".stride")

    content = output_file.read_text()
    # header + 2 good rows, bad.stride skipped rather than raising
    assert len(content.strip().splitlines()) == 3
