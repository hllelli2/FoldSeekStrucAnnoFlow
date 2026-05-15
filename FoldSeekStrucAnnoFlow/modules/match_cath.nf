#!/usr/bin/env nextflow
nextflow.enable.dsl=2


process match_CATH {
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path(foldseek_results)

    output:
    path("final_results.tsv")

    script:

    """
    python3 "${baseDir}/bin/match_cath.py"  ./${foldseek_results}
    """
    }