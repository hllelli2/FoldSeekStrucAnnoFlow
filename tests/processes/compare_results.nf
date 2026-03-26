#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process compare_consensus_files {
    input:
    path consensus1
    path consensus2

    output:
    path "comparison_result.txt"

    script:
    """
    diff <(sort "${consensus1}") <(sort "${consensus2}") > comparison_result.txt || echo "Files differ" >> comparison_result.txt
    if [ \$? -ne 0 ]; then
        echo "Files differ" >> comparison_result.txt
        exit 1
    fi
    """
}


