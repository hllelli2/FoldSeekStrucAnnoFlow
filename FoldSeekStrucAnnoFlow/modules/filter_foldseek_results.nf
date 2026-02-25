

process foldseek_default_process_results { 
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    tuple val(id), path(m8_file)
    path(parser_script)
    

    output:
    tuple val(id), path("foldseek_parsed_results_default.tsv"), emit: foldseek_parsed_results

    script:
    """
    python3 ${parser_script} -i ${m8_file} -o foldseek_parsed_results_default.tsv
    """
}