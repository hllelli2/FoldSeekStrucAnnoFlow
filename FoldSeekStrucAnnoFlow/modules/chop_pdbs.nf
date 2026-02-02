process chop_pdb_from_dir {
    // label 'sge_low'
    // set the container in the config file 
    publishDir "${params.results_dir}/chopped_pdbs" , mode: 'copy'

    input:
    tuple val(id), path(consensus_chunk)
    path pdb_files

    output:
    tuple val(id), path('chopped_pdbs/*.pdb')
    
    script:
    """
    mkdir -p chopped_pdbs
    
    
    pdb_files_dir=\$(dirname ${pdb_files})
    ${params.chop_pdb_script} --consensus ${consensus_chunk} --pdb-dir . --output chopped_pdbs
    """
}

