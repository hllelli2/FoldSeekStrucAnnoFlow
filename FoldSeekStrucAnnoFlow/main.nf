#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * Structure annotation workflow - Main Workflow
 * 
 * Uses parts of the workflow from domain-annotation-pipeline from  https://github.com/UCLOrengoGroup/domain-annotation-pipeline/

 * Main workflow file adapted from https://github.com/UCLOrengoGroup/domain-annotation-pipeline/blob/main/workflows/annotate.nf
 * 
 */


// ===============================================
// PARAMETERS
// ===============================================
// Output directory
params.results_dir = "${workflow.launchDir}/results/${params.project_name}"
params.publish_mode = 'copy'


// ===============================================
// MODULE IMPORTS
// ===============================================

include { input_structure_zip_to_ids } from './modules/pdbs_to_ids.nf'
include { extract_structures_from_zip } from './modules/extract_pdbs_from_zip.nf'
include { convert_cifs_to_pdb } from './modules/cif_to_pdb.nf'
include { collect_pdb_symlinks } from './modules/pdb_symlinks.nf'
include { chop_pdb_from_dir } from './modules/chop_pdbs.nf'
include { foldseek_create_db } from './modules/foldseek_create_db.nf'


// ===============================================
// DOMAIN ANNO... MODULE IMPORTS
// ===============================================



include { filter_pdb } from './external/domain-annotation-pipeline/modules/filter_pdb.nf'

// Domain prediction modules
include { run_ted_segmentation } from './external/domain-annotation-pipeline/modules/run_ted_segmentation.nf'
// Filtering and consensus modules
include { run_filter_domains } from './external/domain-annotation-pipeline/modules/run_filter_domains.nf'
include { run_filter_domains_reformatted as run_filter_domains_reformatted_unidoc } from './external/domain-annotation-pipeline/modules/run_filter_domains_reformatted.nf'
include { run_filter_domains_reformatted as run_filter_domains_reformatted_merizo } from './external/domain-annotation-pipeline/modules/run_filter_domains_reformatted.nf'
include { convert_merizo_results } from './external/domain-annotation-pipeline/modules/convert_merizo_results.nf'
include { convert_unidoc_results } from './external/domain-annotation-pipeline/modules/convert_unidoc_results.nf'
include { run_get_consensus } from './external/domain-annotation-pipeline/modules/run_get_consensus.nf'
include { run_filter_consensus } from './external/domain-annotation-pipeline/modules/run_filter_consensus.nf'

// Post-processing modules
include { chop_pdb } from './external/domain-annotation-pipeline/modules/chop_pdb.nf'
include { chop_pdb_from_zip } from './external/domain-annotation-pipeline/modules/chop_pdb_from_zip.nf'
include { create_md5 } from './external/domain-annotation-pipeline/modules/create_domain_md5.nf'
include { run_stride } from './external/domain-annotation-pipeline/modules/run_stride.nf'
include { summarise_stride } from './external/domain-annotation-pipeline/modules/summarise_stride.nf'
include { transform_consensus } from './external/domain-annotation-pipeline/modules/transform.nf'

// Analysis modules
include { run_domain_quality } from './external/domain-annotation-pipeline/modules/run_domain_quality.nf'
include { run_measure_globularity } from './external/domain-annotation-pipeline/modules/run_measure_globularity.nf'
include { run_plddt } from './external/domain-annotation-pipeline/modules/run_plddt.nf'
include { join_plddt_md5 } from './external/domain-annotation-pipeline/modules/join_plddt_md5.nf'

// Final collection modules
include { collect_results } from './external/domain-annotation-pipeline/modules/collect_results_combine_chopping.nf'
include { collect_results_final } from './external/domain-annotation-pipeline/modules/collect_results_add_metadata.nf'
include { run_AF_domain_id } from './external/domain-annotation-pipeline/modules/run_create_AF_domain_id.nf'

// Foldseek modules
// Here I'll add my own FOLDSEEK modules with the right parameters 

// ===============================================
// HELPER FUNCTIONS
// ===============================================

def validateParameters() {

    if (!params.project_name) {
        error("Project name must be specified in the parameters.")
    }

    if (!params.chunk_size || params.chunk_size <= 0) {
        error("Chunk size must be a positive integer.")
    }

    if (params.debug && !params.max_entries) {
        params.max_entries = 10
    }
    // TODO: Remove this as want to run this purely from pdb or cif files

    if (!params.uniprot_csv_file || !params.pdb_zip_file) {
        error("Both UniProt CSV file and PDB ZIP file must be specified.")
    }

    // Ensure results directory exists
    if (!file(params.results_dir).exists()) {
        file(params.results_dir).mkdirs()
    }

    // Validate required parameters
   
    if (!params.pdb_zip_file || !file(params.pdb_zip_file).exists()) {
        error("PDB ZIP file not found: ${params.pdb_zip_file}")
    }
    // Foldseek asset existence check


    // Foldseek-specific validation
    // if (!params.parser_script || !file(params.parser_script).exists()) {
        // error("Foldseek parser_script not found: ${params.parser_script}")
    // }

    // This is cool, I like this alot but it'll get messy when expanding so might be able to have a python script to do this
    log.info(
        """
    ==============================================
    Domain Annotation Pipeline
    ==============================================
    Project name        : ${params.project_name}
    UniProt CSV file    : ${params.uniprot_csv_file}
    PDB ZIP file        : ${params.pdb_zip_file}
    Main chunk size     : ${params.chunk_size}
    Light chunk size    : ${params.light_chunk_size}
    Heavy chunk size    : ${params.heavy_chunk_size}
    Min chain residues  : ${params.min_chain_residues}
    Max entries (debug) : ${params.max_entries ?: 'N/A'}
    Results dir         : ${params.results_dir}
    Debug mode          : ${params.debug}
    ----------------------------------------------
    Foldseek Configuration Information
    ----------------------------------------------
    Foldseek target Database Directory : ${params.foldseek_databases_dir}
    
    
    
    ==============================================
    """.stripIndent()
    )
}

// ===============================================
// MAIN WORKFLOW
// ===============================================


// Need to remove any reference to downloaidng any assests. I'll add downloades to the external/ folder and reference them locally instead.
workflow {
    
    validateParameters()
    
    // =========================================
    // PHASE 0: Setup Foldseek Assets
    // =========================================
    
    
    // Manual mode - specifies custom CATH database file locations
    // Usage: set --auto_fetch_foldseek_assets to false and --target_db /path/to/db --lookup_file /path/to/lookup
    
    // Keeping this as it checks if a database exists. 

    // TODO: Look at where in the config file these are kept. I'll be using my own config file
    // ch_target_db = Channel.value(file(params.target_db))
    // ch_lookup_file = Channel.value(file(params.lookup_file))

    file("${params.results_dir}/consensus_chunks").mkdirs()

    // =========================================
    // PHASE 1: Data Preparation
    // =========================================


    all_model_ids = input_structure_zip_to_ids(file(params.pdb_zip_file))
    

     // Apply debug limit if enabled
    if (params.debug && params.max_entries) {
        all_model_ids = all_model_ids.take(params.max_entries)
    }

    chunked_ids_ch = all_model_ids.collectFile(
            name: 'all_model_ids.txt',
            newLine: true,
            storeDir: "${params.results_dir}/intermediate",
        )
        .splitText(by: params.chunk_size, file: true)
        .toList()
        .flatMap { List chunk_files ->
            // Emit a tuple (id, path) where id is the chunk index and path is the chunk file
            chunk_files.withIndex().collect { cf, idx ->
                [ idx, cf ]
            }
        }

    // Extract PDB and CIF files from zip based on chunked ids
    unfiltered_pdb_ch = extract_structures_from_zip(chunked_ids_ch, file(params.pdb_zip_file))


    // extract all cif files from unfiltered_pdb_ch to be converted to pdb files
    cif_files_ch = unfiltered_pdb_ch
        .flatMap { tuple ->
            def id = tuple[0]
            def paths = tuple[1]
            paths = paths instanceof List ? paths : [paths]
            def cif_files = paths.findAll { it.name.endsWith('.cif') || it.name.endsWith('.mmcif') }
            return cif_files.collect { cif_file -> [ id, cif_file ] }
        }

    pdb_files_ch = unfiltered_pdb_ch
        .flatMap { tuple ->
            def id = tuple[0]
            def paths = tuple[1]
            paths = paths instanceof List ? paths : [paths]
            def pdb_files = paths.findAll { it.name.endsWith('.pdb') }
            return pdb_files.collect { pdb_file -> [ id, pdb_file ] }
        }

    
    converted_pdb_ch = convert_cifs_to_pdb(cif_files_ch
        .map { id, cif_file -> 
            [ id, cif_file ] 
        }
        .groupTuple()
    )

    all_pdb_ch = converted_pdb_ch.concat(pdb_files_ch).groupTuple()
    

    // changing this to filter the pdbs and cifs together. Will convert them to cifs just after taking them out the zip
    filtered_pdb_ch = filter_pdb(all_pdb_ch, params.min_chain_residues)

    // From this point, I;m going to uncover the workflow bit by bit to ensure it works with PDB or CIF files directly


//     // TODO: currently the rest of the workflow uses channel without chunk index
//     //       we should feed, this through to all subsequent steps for better
//     //       tracking / debugging / caching
    ids_ch = chunked_ids_ch.map { it -> it[1] }
    filtered_pdb_ch = filtered_pdb_ch.map { it -> it[1] }

//     // =========================================
//     // PHASE 2: Domain Prediction
//     // =========================================

//     // deterministic chunking: collect & sort, then chunk
//     // required for caching, but waits for all PDBs first
    heavy_chunk_ch = filtered_pdb_ch
        .flatten()
        .toSortedList { it.toString() }   // sort PDB paths deterministically
        .flatMap { List allFiles ->
            def chunks = []
            int step = params.heavy_chunk_size as int

            (0..<allFiles.size()).step(step).each { i ->
                int end = Math.min(i + step, allFiles.size())
                chunks << allFiles.subList(i, end)
            }

            return chunks
        }



    segmentation_ch = run_ted_segmentation(heavy_chunk_ch)
    // Multi-channel output cannot be applied to operator view for which argument is already provided

    // =========================================
    // PHASE 3: Results Collection & Filtering
    // =========================================

//     // collect the result for the chainsaw output
    collected_chainsaw_ch = segmentation_ch.chainsaw.collectFile(
        name: 'domain_assignments.chainsaw.tsv',
        storeDir: params.results_dir,
    )
    collected_merizo_ch = segmentation_ch.merizo.collectFile(
        name: 'domain_assignments.merizo.tsv',
        storeDir: params.results_dir,
    )
    collected_unidoc_ch = segmentation_ch.unidoc.collectFile(
        name: 'domain_assignments.unidoc.tsv',
        storeDir: params.results_dir,
    )
    collected_consensus_ch = segmentation_ch.consensus.collectFile(
        name: 'domain_assignments.consensus.tsv',
        storeDir: params.results_dir,
    )

    // =========================================
    // PHASE 4: Post-Consensus Processing
    // =========================================

    // Split consensus file into chunks for parallel processing using native Nextflow
    consensus_chunks_ch = collected_consensus_ch
        .splitText(
            by: params.light_chunk_size, 
            file: "${params.results_dir}/consensus_chunks/consensus_chunks"
        )
        .toList()
        .flatMap { List chunk_files ->
            // Emit a tuple (id, path) where id is the chunk index and path is the chunk file
            chunk_files.withIndex().collect { cf, idx ->
                [ idx, cf ]
            }
        }


    chopped_pdb_ch = chop_pdb_from_dir(
        consensus_chunks_ch,
        heavy_chunk_ch
    )


    // IT WORKED!!!! I've got all the hopeed pdbs without needed to change too much


//     // Generate MD5 hashes for domains added a new file and script_ch
    md5_chunks_ch = create_md5(chopped_pdb_ch)
    collected_md5_ch = md5_chunks_ch
        .collectFile(
            name: "all_md5.tsv",
            keepHeader: true, // This was added to remove mid-file headers but there was a problem with end of lines
            skip: 1,          // see the create_md5 process for details.
            storeDir: params.results_dir,
            sort: { it -> it[0] } // sort by chunk id
        ) { it -> it[1] } // use file name to collect


    // =========================================
    // PHASE 5: Structure Analysis
    // =========================================

    // Run STRIDE analysis
    stride_results_ch = run_stride(chopped_pdb_ch)    
    stride_summaries_ch = summarise_stride(stride_results_ch)
    collected_stride_summaries_ch = stride_summaries_ch.collectFile(
        name: "all_stride_summaries.tsv",
        keepHeader: true,
        skip: 1,
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect
    

    // Now breaks here
    
    // Run globularity analysis
    globularity_ch = run_measure_globularity(chopped_pdb_ch)
    // globularity_ch.view { "globularity_ch: " + it }
    // no flatten as only a single file per chunk
    collected_globularity_ch = globularity_ch.collectFile(
        name: "all_domain_globularity.tsv",
        keepHeader: true,
        skip: 1,
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

//     // chopped_pdb_ch.view { "chopped_pdb_ch: " + it }1
    domain_quality_ch = run_domain_quality(chopped_pdb_ch)

    collected_domain_quality_ch = domain_quality_ch.collectFile(
        name: "all_domain_quality.csv",
        keepHeader: true,
        skip: 1,
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

    // Run pLDDT analysis
    plddt_ch = run_plddt(chopped_pdb_ch)
    // plddt_ch.view { "plddt_ch: " + it }
    // no flatten as only a single file per chunk
    collected_plddt_ch = plddt_ch.collectFile(
        name: "all_plddt.tsv",
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

    collected_plddt_with_md5_ch = join_plddt_md5(collected_plddt_ch, collected_md5_ch)


    // =========================================
    // PHASE 6: Run foldseek
    // =========================================

    // Create the query DB from the chopped pdbs channel

    // It doesn't even use the chopped pdb so I'm not
    foldseek_create_db(chopped_pdb_ch) 

    // Define the target (CATH) database channel
    // This needs to be changed to make is malleable for the local database location
    ch_target_db = channel.fromPath(params.target_db)

    
    // Run foldseek search on the output of process create_foldseek_db and the CATH database
    // fs_search_ch = foldseek_run_foldseek(foldseek_create_db.out.query_db_dir, ch_target_db)
    
    // Convert results with fs convertalis, pass query_db, CATH_db and output db from run_foldseek
    // fs_m8_ch = foldseek_run_convertalis(fs_search_ch, ch_target_db)

    // Parse output - first create a channel from the location of the python and look_up scripts
    // ch_parser_script = Channel.value(file(params.parser_script))
    //ch_parser_script = Channel.fromPath(params.parser_script, checkIfExists: true)
    
    // Now pass the convertalis .m8 and python script as intputs to the parsing process
    // fs_parsed_ch = foldseek_process_results(fs_m8_ch, ch_lookup_file, ch_parser_script)
    
    // Finally combine results together with a similar collectFile statement as used above
    // foldseek_ch = fs_parsed_ch.collectFile( 
    //     name: 'foldseek_parsed_results.tsv',
    //     keepHeader: true,
    //     skip: 1,
    //     storeDir: params.results_dir,
    //     sort: { it -> it[0] }
    // ) { it -> it[1] }

    // create a dummy foldseek channel for now to allow workflow to run
    foldseek_ch = Channel.empty()
    // =========================================
    // PHASE 7: Final Assembly
    // =========================================

    // Transform consensus with structure data
    transformed_consensus_ch = transform_consensus(
        collected_consensus_ch,
        collected_md5_ch,
        collected_stride_summaries_ch,
    )

    // Generate AF domain IDs
    // af_domain_ids_ch = run_AF_domain_id(transformed_consensus_ch)

    // Collect intermediate results
    intermediate_results_ch = collect_results(
        collected_chainsaw_ch,
        collected_merizo_ch,
        collected_unidoc_ch,
        
    )

    // Generate final comprehensive results
    collect_results_script_ch = channel.fromPath(
        "${workflow.projectDir}/../docker/script/combine_results_final.py", 
        checkIfExists: true
    )
    collect_results_script_ch.view { "collect_results_script_ch: " + it }
    
    collected_taxonomy_ch = channel.empty() // Temporary empty channel as not downloading from UniProt
    final_results_ch = collect_results_final(
        collect_results_script_ch,
        transformed_consensus_ch,
        collected_globularity_ch,
        collected_plddt_with_md5_ch,
        collected_domain_quality_ch,
        collected_taxonomy_ch,
        foldseek_ch,
    )

//     // =========================================
//     // PHASE 8: Output Generation
//     // =========================================

//     // Ensure final outputs are saved
//     final_results_ch
//         .map { file ->
//             def output_path = "${params.results_dir}/final_domain_annotations.tsv"
//             file.copyTo(output_path)
//             log.info("Final results written to: ${output_path}")
//             return output_path
//         }
//         .view { "Final output: ${it}" }

//     // Create completion marker
//     final_results_ch
//         .map {
//             def completion_file = file("${params.results_dir}/WORKFLOW_COMPLETED")
//             completion_file.text = """
//             Workflow completed successfully at: ${new Date()}
//             Total processing time: ${workflow.duration}
//             """.stripIndent()
//             return "Workflow completed successfully"
//         }
//         .view()
}

