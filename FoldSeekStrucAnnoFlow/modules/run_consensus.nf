#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process run_consensus {

    input:
    
    tuple val(chunk_id), path('output/chopping_chainsaw.txt'), path('output/chopping_merizo.txt'), path('output/chopping_unidoc.txt')


    output:
    path 'output/consensus.tsv', emit: consensus


    script:
    """
    set -x
    source /app/ted-tools/ted_consensus_1.0/ted_consensus/bin/activate
    which python3

    python3 /app/ted-tools/ted_consensus_1.0/scripts/get_consensus.py \
    -c output/chopping_merizo.txt \
    output/chopping_chainsaw.txt \
    output/chopping_unidoc.txt \
    -o output/consensus.tsv > output/consensus.log 2>&1

   if test -f output/consensus.tsv; then
        python3 /app/ted-tools/ted_consensus_1.0/scripts/filter_domains_consensus.py \
        "output/consensus.tsv" \
        -o "output/consensus.tsv.tmp" 

        if [ \$? == 0 ]; then
            mv "output/consensus.tsv.tmp" "output/consensus.tsv"
        fi
    else
        echo "Expected to find output file at output/consensus.tsv but it does not exist. Exiting with error."
        exit 1
    fi

    """
    stub:
    """
    echo "Stub process for run_consensus"
    rsync -av /launchDir/fixtures/debug/run_consensus/ ./
    """
}
