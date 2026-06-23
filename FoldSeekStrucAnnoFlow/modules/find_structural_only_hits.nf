#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Flags FoldSeek hits from structural-only databases (PDB, AFDB) whose protein
// has no Gene3D and/or no Pfam hit in InterProScan - i.e. cases where the
// structural search found something sequence-based domain databases missed.
// See bin/find_structural_only_hits.py.
process find_structural_only_hits {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(foldseek_non_cath_file)
    path(interproscan_output_file)
    path(match_columns_file)
    val(source_dbs)

    output:
    path("structural_only_hits.tsv"), emit: hits
    path("structural_only_hits.log"), emit: log

    script:
    """
    python3 "${projectDir}/bin/find_structural_only_hits.py" \\
        ${foldseek_non_cath_file} \\
        ${interproscan_output_file} \\
        ${match_columns_file} \\
        structural_only_hits.tsv \\
        --source-dbs '${source_dbs}' \\
        | tee structural_only_hits.log
    """
}
