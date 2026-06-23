#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Checks FoldSeek CATH labels (final_domain_annotations.tsv) against InterProScan
// Gene3D hits for the same proteins. See bin/interpro_comparison.py.
process compare_cath_annotations {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(pipeline_output_file)
    path(interproscan_output_file)
    path(match_columns_file)

    output:
    path("cath_interpro_comparison.tsv"), emit: comparison

    script:
    """
    python3 "${projectDir}/bin/interpro_comparison.py" cath \\
        ${pipeline_output_file} \\
        ${interproscan_output_file} \\
        ${match_columns_file} \\
        cath_interpro_comparison.tsv
    """
}
