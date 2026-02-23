#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { run_foldseek } from '../../modules/run_foldseek.nf'
include { foldseek_create_db } from '../../modules/create_db.nf'
include { foldseek_run_convertalis } from '../../modules/run_foldseek_convertails.nf'


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

        fs_m8_ch.view { f -> "fs_m8_ch: " + f }

        // I only what the next 

    emit:
        fs_m8_ch

}