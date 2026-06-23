#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Checks FoldSeek Pfam hits (foldseek_parsed_results_non-cath.tsv, db == PfamSDB)
// against InterProScan Pfam hits for the same proteins. See bin/interpro_comparison.py.
process compare_pfam_annotations {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(pipeline_output_file)
    path(interproscan_output_file)
    path(match_columns_file)

    output:
    path("pfam_interpro_comparison.tsv"), emit: comparison

    script:
    """
    python3 "${projectDir}/bin/interpro_comparison.py" pfam \\
        ${pipeline_output_file} \\
        ${interproscan_output_file} \\
        ${match_columns_file} \\
        pfam_interpro_comparison.tsv
    """
}
