#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Adapted from domain_annotation_pipeline/modules/run_domain_quality.nf

process run_domain_quality {

    input:
    tuple val(id), path("chopped_pdbs/*")

    output:
    tuple val(id), path("${id}_domain_quality.csv")

    script:
    """
    ${params.domain_quality_script_setup}
    ${params.domain_quality_script} -d chopped_pdbs/ -o ${id}_domain_quality.csv
    perl -i.bak -pe 's/\\r\\n/\\n/g' ${id}_domain_quality.csv
    """
}
