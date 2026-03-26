#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { run_chainsaw } from '../../modules/run_chainsaw.nf'
include { run_merizo } from '../../modules/run_merizo.nf'
include { run_unidoc } from '../../modules/run_unidoc.nf'
include { run_consensus } from '../../modules/run_consensus.nf'

workflow run_ted_segmentation {

   
    take:
    heavy_chunk_ch
        

    main:

        run_chainsaw_ch = run_chainsaw(heavy_chunk_ch)
        run_merizo_ch = run_merizo(heavy_chunk_ch)
        unidoc_input_ch = heavy_chunk_ch
            .join(run_merizo_ch.merizo)
            .join(run_merizo_ch.targets)
            .map { chunk_id, pdbs, merizo_chopping, targets -> tuple(chunk_id, pdbs, merizo_chopping, targets) }


        run_unidoc_ch = run_unidoc(unidoc_input_ch)

        consensus_input_ch = run_chainsaw_ch.chainsaw
            .join(run_merizo_ch.merizo)
            .join(run_unidoc_ch.unidoc)
            .map { chunk_id, chainsaw_chopping, merizo_chopping, unidoc_chopping -> tuple(chunk_id, chainsaw_chopping, merizo_chopping, unidoc_chopping) }
    

        consensus_ch = run_consensus(consensus_input_ch)
    emit:
        consensus_ch

}

