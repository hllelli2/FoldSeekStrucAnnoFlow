#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// Of the FoldSeek hits with no Gene3D/Pfam coverage, splits proteins into "no
// InterProScan hit in any analysis" vs "has some other InterProScan hit (e.g.
// PANTHER), just not Gene3D/Pfam". Needs match_columns built against the *raw*
// (unfiltered) InterProScan output - the Gene3D/Pfam-filtered one used elsewhere in
// this pipeline can't tell those two cases apart. See bin/split_no_interpro_coverage.py.
process split_no_interpro_coverage {
    publishDir "${params.post_processing_results_dir}", mode: 'copy'

    input:
    path(foldseek_non_cath_file)
    path(interproscan_raw_file)
    path(match_columns_file)
    val(source_dbs)

    output:
    path("no_interpro_hit.csv"), emit: no_interpro_hit
    path("no_pfam_gene3d_hit.csv"), emit: no_pfam_gene3d_hit

    script:
    """
    python3 "${projectDir}/bin/split_no_interpro_coverage.py" \\
        ${foldseek_non_cath_file} \\
        ${interproscan_raw_file} \\
        ${match_columns_file} \\
        no_interpro_hit.csv \\
        no_pfam_gene3d_hit.csv \\
        --source-dbs '${source_dbs}'
    """
}
