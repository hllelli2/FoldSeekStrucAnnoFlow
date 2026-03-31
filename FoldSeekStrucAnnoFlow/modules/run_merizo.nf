#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process run_merizo {

    input:
    tuple val(chunk_id), path(pdbs)

    output:    
    tuple val(chunk_id), path('output/chopping_merizo.txt'), emit: merizo
    tuple val(chunk_id), path('output/chopping_merizo.log'), emit: merizo_log
    tuple val(chunk_id), path('output/targets.txt'), emit: targets
    

    script:
    """
    set -x
    export OMP_NUM_THREADS=${task.cpus}
    export MKL_NUM_THREADS=${task.cpus}
    OFFSET_RESI=0
    # Activate the ted_consensus python environment
    source /app/ted-tools/ted_consensus_1.0/ted_consensus/bin/activate

    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    uname -a
    pwd
    mkdir output
    ls -lrta
    ls -l /dev/nvidia* || true
    nvidia-smi -L || true
    env | sort
    target_list="output/targets.txt"
    mkdir -p pdb
    mv *.pdb pdb/
    readlink -f "pdb/"*.pdb > \${target_list}
    
    python3 /app/ted-tools/ted_consensus_1.0/programs/merizo/predict_afdb.py \
    -l "\${target_list}" --out output/chopping_merizo.txt > output/chopping_merizo.log 2>&1

    # Filter choppings to remove small segments and single-residue domains
    if test -f output/chopping_merizo.txt; then
        python3 /app/ted-tools/ted_consensus_1.0/scripts/filter_domains.py \
        "output/chopping_merizo.txt" \
        -o "output/chopping_merizo.txt.tmp" \
        --offset_resi "\${OFFSET_RESI}" \

        if [ \$? == 0 ]; then
            mv "output/chopping_merizo.txt.tmp" "output/chopping_merizo.txt"
        fi
    else
        echo "Expected to find output file at output/chopping_merizo.txt but it does not exist. Exiting with error."
        exit 1
    fi

    """

    stub:
    """
    echo "Stub process for run_merizo"
    rsync -av /launchDir/fixtures/debug/run_merizo/ ./
    """
}