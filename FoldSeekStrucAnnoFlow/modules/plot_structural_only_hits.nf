#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Plots InterProScan coverage of FoldSeek hits from structural-only databases
// (e.g. PDB/AFDB): overall Gene3D/Pfam coverage breakdown, and gap rate per
// source db. See bin/plot_structural_only_hits.py.
process plot_structural_only_hits {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(structural_only_hits_file)

    output:
    path("structural_only_hits_summary.png"), emit: plot

    script:
    """
    python3 "${projectDir}/bin/plot_structural_only_hits.py" \\
        ${structural_only_hits_file} \\
        structural_only_hits_summary.png
    """
}
