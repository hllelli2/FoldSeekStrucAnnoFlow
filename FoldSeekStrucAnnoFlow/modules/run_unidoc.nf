#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process run_unidoc {

    input:
    tuple val(chunk_id), path(pdbs), path(merizo_chopping), path(targets)

    output:    
    tuple val(chunk_id), path('output/chopping_unidoc.txt'), emit: unidoc
    tuple val(chunk_id), path('output/chopping_unidoc.log'), emit: unidoc_log

    script:
    """
    OFFSET_RESI=0
    
    ${params.run_unidoc_script_setup}
    set -x
    which python3
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    uname -a
    pwd
    mkdir -p output
    ls -lrta
    ls -l /dev/nvidia* || true
    nvidia-smi -L || true
    env | sort
    
    python3 /tmp/unidoc_temp/Run_UniDoc_from_scratch_structure_afdb.py \
    -l ${targets} --out output/chopping_unidoc.txt \
    --inherit_chopping ${merizo_chopping} \
        > output/chopping_unidoc.log 2>&1

    if test -f output/chopping_unidoc.txt; then
        python3 /app/ted-tools/ted_consensus_1.0/scripts/filter_domains.py \
        "output/chopping_unidoc.txt" \
        -o "output/chopping_unidoc.txt.tmp" \
        --offset_resi "\${OFFSET_RESI}"

        if [ \$? == 0 ]; then
            mv "output/chopping_unidoc.txt.tmp" "output/chopping_unidoc.txt"
        fi
    else
        echo "Expected to find output file at output/chopping_unidoc.txt but it does not exist. Exiting with error."
        exit 1
    fi
    """

    stub:
    """
    echo "Stub process for run_unidoc"
    rsync -av /launchDir/fixtures/debug/run_unidoc/ ./

    """
}