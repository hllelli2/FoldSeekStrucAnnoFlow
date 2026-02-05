#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// This is adapted from the domain-annotation-pipeline foldseek module

process run_foldseek {
    publishDir "results", mode: 'copy'

    input:
    tuple val(id), path(query_db_dir)
    path(target_db)


    output:
    tuple val(id), path(query_db_dir), path("result_db_dir"), emit: search_results

    script:
    """
    GPU_FLAG=""
    if [ "${params.USE_GPU}" = true ]; then
        GPU_FLAG="--gpu 0"
    fi


    mkdir -p tmp_foldseek
    mkdir -p result_db_dir
    ${params.foldseek_exec} search \\
        ${query_db_dir}/query_db \\
        ${params.foldseek_databases_dir}/${target_db} \\
        result_db_dir/foldseek_output_db \\
        tmp_foldseek \\
        --cov-mode 5 \\
        --alignment-type 2 \\
        -e ${params.T_EVALUE_THRESHOLD} \\
        -s 10 \\
        -c ${params.H_COVERAGE_THRESHOLD} \\
        -a \\
        \${GPU_FLAG} 
    
    rm -rf tmp_foldseek
    
    """
}