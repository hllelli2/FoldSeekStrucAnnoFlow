#!/usr/bin/env nextflow
nextflow.enable.dsl=2


// adapted from domain-annotation-pipeline/modules/extract_pdbs_from_zip.nf

process extract_structures_from_zip {

    input:
    tuple val(id), path(id_file)
    path pdb_zip

    output:
    tuple val(id), path("*.{pdb,cif,mmcif}")

    script:
    
    """
    ${params.extract_structure_script} ${pdb_zip} ${id_file} 
    """

    stub:
    """
    echo "Stub for extract_structures_from_zip with ID: ${id}"
    touch ${id}_structure.pdb
    touch ${id}_structure.cif
    touch ${id}_structure.mmcif
    """
    }



