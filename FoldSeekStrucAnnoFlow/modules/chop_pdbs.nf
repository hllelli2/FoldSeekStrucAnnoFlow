process chop_pdb_from_dir {
    // label 'sge_low'
    // set the container in the config file 
    publishDir "${params.results_dir}/chopped_pdbs" , mode: 'copy'

    input:
    tuple val(id), path(consensus_chunk)
    tuple val(id2), path(consensus_chunk_files)
    output:
    tuple val(id), path('chopped_pdbs/*.pdb')
    
    script:
    """
    mkdir -p chopped_pdbs
    
    
    #pdb_files_dir=\$(dirname ${consensus_chunk_files}) cp \${pdb_files_dir}/*.pdb ./
    ${params.chop_pdb_script} --consensus ${consensus_chunk_files} --pdb-dir . --output chopped_pdbs
    """
}

