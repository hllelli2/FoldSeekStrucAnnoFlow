#!/usr/bin/Nextflow

nextflow.enable.dsl=2

process dummy_taxonomy_file {
    input:
        val filename

    output:
        file "${filename}" 

    script:
    """
    echo -e "accession\tproteome_id\ttax_common_name\ttax_scientific_name\ttax_lineage" > ${filename}
    """
}
