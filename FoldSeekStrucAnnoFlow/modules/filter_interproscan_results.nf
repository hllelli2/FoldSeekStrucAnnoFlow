#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Filters a raw InterProScan TSV down to the analyses we trust for comparison
// (Gene3D + Pfam by default), dropping unrelated databases (PANTHER, SUPERFAMILY,
// CDD, ...) and disorder/feature predictors (MobiDBLite, Coils, ...).
// See bin/filter_interproscan_results.py.
process filter_interproscan_results {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(interproscan_output_file)
    val(keep_analyses)

    output:
    path("interproscan_filtered.tsv"), emit: filtered

    script:
    """
    python3 "${projectDir}/bin/filter_interproscan_results.py" \\
        ${interproscan_output_file} \\
        interproscan_filtered.tsv \\
        --keep-analyses '${keep_analyses}'
    """
}
