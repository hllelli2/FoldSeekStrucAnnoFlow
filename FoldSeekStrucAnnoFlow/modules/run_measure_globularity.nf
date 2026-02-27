#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// Adapted from domain_annotation_pipeline/modules/run_measure_globularity.nf

process run_measure_globularity {
    

    input:
    tuple val(id), path("pdb/*") //pdb_dir

    output:
    tuple val(id), path("${id}_domain_globularity.tsv") 

    // added an intermediate tmp file and dos2unix to recognise end of lines correctly.
    script:
    """
    ${params.globularity_script} --pdb_dir ./pdb --domain_globularity ${id}_domain_globularity_tmp.tsv
    dos2unix ${id}_domain_globularity_tmp.tsv > ${id}_domain_globularity.tsv || tr -d '\\r' < ${id}_domain_globularity_tmp.tsv > ${id}_domain_globularity.tsv
    """
    
}