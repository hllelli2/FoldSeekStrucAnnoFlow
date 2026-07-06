#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process run_chainsaw {

    input:
    tuple val(chunk_id), path(pdbs)

    output:    
    tuple val(chunk_id), path('output/chopping_chainsaw.txt'), emit: chainsaw
    tuple val(chunk_id), path('output/chopping_chainsaw.log'), emit: chainsaw_log

    script:
    """
    set -x
    export OMP_NUM_THREADS=${task.cpus}
    export MKL_NUM_THREADS=${task.cpus}
    OFFSET_RESI=1
    source /app/ted-tools/ted_consensus_1.0/ted_consensus/bin/activate
    which python3
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    uname -a
    pwd
    mkdir -p output
    mkdir -p pdb
    mv *.pdb pdb/
    ls -lrta
    ls -l /dev/nvidia* || true
    nvidia-smi -L || true
    env | sort

    python3 /app/ted-tools/ted_consensus_1.0/programs/chainsaw/get_predictions.py \
    --structure_directory pdb \
    -o output/chopping_chainsaw.txt --append > output/chopping_chainsaw.log 2>&1

    if test -f output/chopping_chainsaw.txt; then
        python3 /app/ted-tools/ted_consensus_1.0/scripts/filter_domains.py \
        "output/chopping_chainsaw.txt" \
        -o "output/chopping_chainsaw.txt.tmp" \
        --offset_resi "\${OFFSET_RESI}"

        if [ \$? == 0 ]; then
            mv "output/chopping_chainsaw.txt.tmp" "output/chopping_chainsaw.txt"
        fi
    else
        echo "Expected to find output file at output/chopping_chainsaw.txt but it does not exist. Exiting with error."
        exit 1
    fi
    """

    stub:
    """
    echo "Stub process for run_chainsaw"
    rsync -av /launchDir/fixtures/debug/run_chainsaw/ ./
    """
}