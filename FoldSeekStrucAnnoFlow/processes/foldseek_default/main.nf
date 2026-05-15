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
    ch_target_db_split = ch_target_db.map { db ->
        def f = file(db)
        [f.parent, f.name]  
}
        ch_target_db_split.view { "split: " + it }

        // ch_target_db_split = ch_target_db.map { db ->
        //     [file(db).parent, file(db).name]
        // }

        query_db_target_db_ch = foldseek_db_ch.combine(ch_target_db_split)

        fs_search_ch = run_foldseek(query_db_target_db_ch)

        fs_m8_ch = foldseek_run_convertalis(fs_search_ch)


        fs_m8_ch.view { f -> "fs_m8_ch: " + f }

        ch_parser_script = channel.value(file(params.general_parser_script))

        fs_parser_ch = foldseek_default_process_results(
            fs_m8_ch,  // no .combine() needed - target_db_name already in tuple
            ch_parser_script
        )

        fs_parser_ch.view { f -> "fs_parser_ch: " + f }  // add this


        foldseek_ch = fs_parser_ch.collectFile(
            keepHeader: true,
            skip: 1,
            storeDir: params.results_dir,
            name: "foldseek_parsed_results_non-cath.tsv"
        ) { f -> f[1] }

        foldseek_ch.view { f -> "foldseek_ch: " + f }
    

    emit:
        foldseek_ch
}