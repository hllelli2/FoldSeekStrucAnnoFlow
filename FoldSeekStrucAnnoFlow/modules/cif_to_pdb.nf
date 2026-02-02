#!/usr/bin/env nextflow
nextflow.enable.dsl=2


process convert_cifs_to_pdb {

    input:
    tuple val(id), path(cif_files)

    output:
    tuple val(id), path("*.pdb")

    script:

    """

    python3 "${baseDir}/bin/cif_to_pdb.py" ${cif_files} ./
    """
    }

// ToDo: Add Stub

