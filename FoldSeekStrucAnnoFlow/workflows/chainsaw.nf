#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { CHAINSAW_RUN } from '../modules/chainsaw/main.nf'


workflow CHAINSAW_WORKFLOW {
    take:
        input_dir

    main:

        repo_dir = params.chainsaw_repo
        work_dir = params.work_dir
        extra_args = params.chainsaw_extra_args
        cpu_flag = params.cpu
        gpu_flag = params.gpu
        // add logic that it can't be both cpu and gpu true??
        if (cpu_flag && gpu_flag) {
            error "Both CPU and GPU flags cannot be true at the same time."
        }

        // view the type of input_dir

        pdb_files = input_dir.map { file -> file.listFiles().findAll {f -> f.name.endsWith('.pdb') } }.flatten()
        pdb_files.view {f -> "Found PDB file: ${f}" }
        (chainsaw_results, versions) = CHAINSAW_RUN(pdb_files, repo_dir, work_dir, extra_args, cpu_flag, gpu_flag)
        chainsaw_results.view {f -> "Chainsaw output files: ${f}" }

    emit:
        chainsaw_results
        versions
        
}


