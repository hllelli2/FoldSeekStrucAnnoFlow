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
    internal_dir=\$(unzip -Z1 "${pdb_zip}" | head -n1 | sed 's|/.*||' | tr -d '\n')

    # Check if internal_dir is actually a directory inside the zip
    if unzip -Z1 "${pdb_zip}" | grep -q "^\${internal_dir}/"; then
        prefix="\${internal_dir}/"
    else
        prefix=""
    fi

    while read -r line; do
        [[ -z "\${line// }" ]] && continue

        echo "Extracting structure for ID: \${line}"
        unzip -j "${pdb_zip}" "\${prefix}\${line}.*" || true


    done < ${id_file}
    """
}
