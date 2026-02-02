#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process deepfri_predict {
    publishDir "results", mode: 'copy'

    input:
    tuple val(id), path(pdb_files)

    output:
    tuple val(id), path("deepfri_output_dir"), emit: deepfri_results
    // >> python predict.py -pdb ./examples/pdb_files/1S3P-A.pdb -ont mf -v

    script:
    """
    mkdir -p deepfri_output_dir
    ${params.deepfri_predict_script} \\
        -pdb \\
        -ont mf \\
        --pdb_dir . \\
2        --saliency \\
        --use_backprop
    """
}