#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { run_foldseek } from '../../modules/run_foldseek.nf'
include { foldseek_create_db } from '../../modules/create_db.nf'
include { foldseek_run_convertalis } from '../../modules/run_foldseek_convertails.nf'
include { foldseek_default_process_results } from '../../modules/filter_foldseek_results.nf'


workflow foldseek_default {
    
    take:
        ch_target_db
        foldseek_db_ch

    main:

        query_db_target_db_ch = foldseek_db_ch.combine(
            ch_target_db
        )

        // Here move all of this to a seperate process

        query_db_target_db_ch.view { f -> "query_db_target_db_ch: " + f }

        
        fs_search_ch = run_foldseek(
        query_db_target_db_ch
        ) 

        fs_search_ch = fs_search_ch.combine(ch_target_db)

        fs_search_ch.view { f -> "fs_search_ch: " + f }


        fs_m8_ch = foldseek_run_convertalis(fs_search_ch)

        ch_parser_script = channel.value(file(params.general_parser_script))


        fs_parser_ch = foldseek_default_process_results(fs_m8_ch, ch_parser_script)
        foldseek_ch = fs_parser_ch.collectFile( 
        name: "foldseek_parsed_results_default.tsv",
        keepHeader: true,
        skip: 1,
        storeDir: params.results_dir,
        sort: { f -> f[0] }
        ) { f -> f[1] }
    



    emit:
        foldseek_ch
}