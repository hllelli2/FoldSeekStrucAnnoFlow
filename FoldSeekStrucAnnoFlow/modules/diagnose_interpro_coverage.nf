#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Joins FoldSeek results against the full InterProScan output and reports
// ID-mapping / hit coverage diagnostics. See bin/interpro_comparison.py.
process diagnose_interpro_coverage {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(pipeline_output_file)
    path(interproscan_output_file)
    path(match_columns_file)
    val(pipeline_column)

    output:
    path("interpro_diagnostics.tsv"), emit: diagnostics
    path("interpro_diagnostics.log"), emit: log

    script:
    """
    python3 "${projectDir}/bin/interpro_comparison.py" diagnose \\
        ${pipeline_output_file} \\
        ${interproscan_output_file} \\
        ${match_columns_file} \\
        interpro_diagnostics.tsv \\
        --pipeline-column ${pipeline_column} \\
        | tee interpro_diagnostics.log
    """
}
