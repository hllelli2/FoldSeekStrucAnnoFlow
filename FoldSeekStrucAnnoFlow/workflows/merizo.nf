#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { MERIZO_RUN } from '../modules/merizo/main.nf'


workflow MERIZO_WORKFLOW {
    take:
        input_dir

    main:

        repo_dir = params.merizo_repo
        work_dir = params.work_dir
        extra_args = params.merizo_extra_args
        cpu_flag = params.cpu
        gpu_flag = params.gpu
        // add logic that it can't be both cpu and gpu true??
        if (cpu_flag && gpu_flag) {
            error "Both CPU and GPU flags cannot be true at the same time."
        }

        // view the type of input_dir

        pdb_files = input_dir.map { file -> file.listFiles().findAll {f -> f.name.endsWith('.pdb') } }.flatten()
        pdb_files.view {f -> "Found PDB file: ${f}" }
        (merizo_results, versions) = MERIZO_RUN(pdb_files, repo_dir, work_dir, extra_args, cpu_flag, gpu_flag)
        merizo_results.view {f -> "Merizo output files: ${f}" }

    emit:
        merizo_results
        versions
        
}


