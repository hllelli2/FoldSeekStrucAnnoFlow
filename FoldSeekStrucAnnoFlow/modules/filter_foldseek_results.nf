#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process foldseek_default_process_results { 
    publishDir "${params.results_dir}", mode: 'copy'

    input:
    tuple val(id), path(query_db_dir), path(target_db_dir), val(target_db_name), path(result_db_dir), path(m8_file)
    path(parser_script)

    output:
    tuple val(target_db_name), path("foldseek_parsed_results_${target_db_name}.tsv"), emit: foldseek_parsed_results

    script:
    """
    python3 ${parser_script} -i ${m8_file} -o tmp.tsv
    awk 'NR==1 {print \$0"\tdb"} NR>1 {print \$0"\t${target_db_name}"}' tmp.tsv > foldseek_parsed_results_${target_db_name}.tsv
    """
}