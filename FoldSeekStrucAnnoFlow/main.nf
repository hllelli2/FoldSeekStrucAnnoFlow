#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { MERIZO_RUN } from './modules/merizo/main.nf'


// basic worfklow that finds all pdb files in the input directory and runs Merizo on them
workflow MERIZO_WORKFLOW {
    input_dir = file(params.input_dir)
    repo_dir = params.merizo_repo
    work_dir = params.work_dir
    extra_args = params.merizo_extra_args
    pdb_files = Channel.fromPath("${input_dir}/*.pdb")
    merizo_results = MERIZO_RUN(pdb_files, repo_dir, work_dir, extra_args)
    merizo_results.view()
}