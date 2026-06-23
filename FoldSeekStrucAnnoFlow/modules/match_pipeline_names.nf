#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Maps pipeline IDs (e.g. "transcript=...") to InterProScan protein_accession
// values via fuzzy longest-common-substring matching. See bin/match_names.py.
process match_pipeline_names {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(pipeline_output_file)
    path(interproscan_output_file)
    val(pipeline_column)
    val(label)

    output:
    path("match_columns_${label}.json"), emit: match_columns

    script:
    """
    python3 "${projectDir}/bin/match_names.py" \\
        ${pipeline_output_file} \\
        ${interproscan_output_file} \\
        match_columns_${label}.json \\
        --pipeline-column ${pipeline_column}
    """
}
