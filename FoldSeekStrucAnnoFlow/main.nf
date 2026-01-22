#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { MERIZO_WORKFLOW } from './workflows/merizo.nf'
include { CHAINSAW_WORKFLOW } from './workflows/chainsaw.nf'

// basic worfklow that finds all pdb files in the input directory and runs Merizo on them

workflow {
    input_dir = channel.fromPath(params.input_dir, type: 'dir')
    merizo_results = MERIZO_WORKFLOW(input_dir)
    chainsaw_results = CHAINSAW_WORKFLOW(input_dir)

}


