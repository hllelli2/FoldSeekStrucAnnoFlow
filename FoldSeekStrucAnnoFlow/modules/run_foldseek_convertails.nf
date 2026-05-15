#!/usr/bin/env nextflow

nextflow.enable.dsl=2


// This is adapted from the domain-annotation-pipeline foldseek module

process foldseek_run_convertalis {
    publishDir "results/convertalis", mode: 'copy', pattern: "*.m8"

    
    input:
    tuple val(id), path(query_db_dir), path(target_db_dir), val(target_db_name), path(result_db_dir)


    output:
tuple val(id), path(query_db_dir), path(target_db_dir), val(target_db_name), path(result_db_dir), path("foldseek_output.m8"), emit: m8_output

    script:
    """
    ${params.foldseek_exec} convertalis \\
        ${query_db_dir}/query_db \\
        ${target_db_dir}/${target_db_name} \\
        ${result_db_dir}/foldseek_output_db \\
        foldseek_output.m8 \\
        --format-output "query,target,fident,evalue,qlen,tlen,qtmscore,ttmscore,qcov,tcov"
    
    """
}
