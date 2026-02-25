from pathlib import Path

EXPECTED_OUTPUT = """
query_id	target_id	evalue	tmscore	type	qcov	tcov
AF-G1S737-F1-model_v6_01	AF-P19026-F1-model_v6	1.107e-06	0.7416	H	0.846	0.446
AF-G1S737-F1-model_v6_copy_02	AF-P24941-2-F1-model_v6	2.915e-29	0.9928	H	1.0	0.636
AF-G1S737-F1-model_v6_cif_01	AF-P19026-F1-model_v6	1.107e-06	0.7416	H	0.846	0.446
AF-G1S737-F1-model_v6_02	AF-P24941-2-F1-model_v6	2.915e-29	0.9928	H	1.0	0.636
AF-G1S737-F1-model_v6_copy_01	AF-P19026-F1-model_v6	1.107e-06	0.7416	H	0.846	0.446
AF-G1S737-F1-model_v6_cif_02	AF-P24941-2-F1-model_v6	2.915e-29	0.9928	H	1.0	0.636

"""


def test_format_foldseek_output(test_data_dir: Path, tmp_dir: Path) -> None:
    # start by getting the pathway to the test data, which is in the same directory as this test file
    input_file = test_data_dir / "foldseek_output.m8"
    output_file = tmp_dir / "formatted_foldseek_output.tsv"
    # now we can call the function to format the foldseek output, which is in the bin directory
    from FoldSeekStrucAnnoFlow.bin.filter_foldseek_results import main as format_foldseek

    assert input_file.exists(), f"Input file {input_file} does not exist"
    format_foldseek(input_file=input_file, output_file=output_file)

    assert output_file.exists(), f"Output file {output_file} was not created"

    # Read in output file and expected output file, and compare them
    with open(output_file, "r") as f:
        output_lines = f.readlines()
        output_lines = [line.strip() for line in output_lines if line.strip()]

    expected_lines = EXPECTED_OUTPUT.strip().split("\n")
    expected_lines = [line.strip() for line in expected_lines if line.strip()]
    assert output_lines == expected_lines, (
        f"Output lines do not match expected lines. Got:\n{output_lines}\nExpected:\n{expected_lines}"
    )
