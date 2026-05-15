#!/usr/bin/env nextflow


nextflow.enable.dsl=2

include { run_foldseek } from '../../modules/run_foldseek.nf'
include { foldseek_create_db } from '../../modules/create_db.nf'
include { foldseek_run_convertalis } from '../../modules/run_foldseek_convertails.nf'
include { foldseek_process_results } from '../../external/domain-annotation-pipeline/foldseek/modules/foldseek_process_results.nf'
workflow foldseek_cath {
    take:
        ch_target_db
        foldseek_db_ch
        ch_lookup_file

    main:
        ch_target_db_split = ch_target_db.map { db ->
            def f = file(db)
            [f.parent, f.name]
        }

        ch_target_db_split.view { "split: " + it }

        query_db_target_db_ch = foldseek_db_ch.combine(ch_target_db_split)

        fs_search_ch = run_foldseek(query_db_target_db_ch)

        fs_m8_ch = foldseek_run_convertalis(fs_search_ch)

        ch_parser_script = channel.value(file(params.parser_script))

        fs_m8_remapped_ch = fs_m8_ch.map { id, query_db_dir, target_db_dir, target_db_name, result_db_dir, m8_file ->
            [id, m8_file]
        }

        fs_parsed_ch = foldseek_process_results(fs_m8_remapped_ch, ch_lookup_file, ch_parser_script)

        // fs_parsed_ch = foldseek_process_results(fs_m8_ch, ch_lookup_file, ch_parser_script)

        foldseek_ch = fs_parsed_ch.collectFile( 
            name: 'foldseek_parsed_results.tsv',
            keepHeader: true,
            skip: 1,
            storeDir: params.results_dir,
            sort: { f -> f[0] }
        ) { f -> f[1] }
 
    emit:
        foldseek_ch
}