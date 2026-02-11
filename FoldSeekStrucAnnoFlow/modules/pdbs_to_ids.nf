#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process input_structure_zip_to_ids {
    publishDir "${params.results_dir}", mode: 'copy'

    input:
    path zip_file
    output:
    path ids_output
 
 
    script:
    ids_output = "ids.txt"
    """
    ${params.zip_to_ids_script} ${zip_file} ${ids_output}
 
    """ 
// TODO: add a stub
stub:
"""
    echo "Stub for input_structure_zip_to_ids"
    touch ids.txt

    """
}