#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process foldseek_create_db {
    
    publishDir "results/database_dir_${id}", mode: 'copy'

    
    input:
    tuple val(id), path(pdb_files)

    output:
    tuple val(id), path("database_dir"), emit: query_db_dir

    script:
    """
    mkdir -p database_dir
    ${params.foldseek_exec} createdb \\
        . \\
        database_dir/query_db
    """
    }