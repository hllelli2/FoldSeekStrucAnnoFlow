#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Plots CATH and Pfam vs InterProScan any_match summaries side by side.
// See bin/plot_interpro_comparison.py.
process plot_interpro_comparison {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(cath_comparison_file)
    path(pfam_comparison_file)

    output:
    path("interpro_match_summary.png"), emit: plot

    script:
    """
    python3 "${projectDir}/bin/plot_interpro_comparison.py" \\
        ${cath_comparison_file} \\
        ${pfam_comparison_file} \\
        interpro_match_summary.png
    """
}
