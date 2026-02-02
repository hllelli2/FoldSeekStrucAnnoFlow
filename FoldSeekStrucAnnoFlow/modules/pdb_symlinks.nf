#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process collect_pdb_symlinks {

    input:
    path(pdb_files)
    output:
    path("${dirName}/*.pdb")

    script:
    dirName = "all_pdbs_for_chopping" 
    """
    mkdir ${dirName}

    for pdb in ${pdb_files}; do
        ln -s "\$pdb" "${dirName}/\$(basename \$pdb)"
    done
    """
}