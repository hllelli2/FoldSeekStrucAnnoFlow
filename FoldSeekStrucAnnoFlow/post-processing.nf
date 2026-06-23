#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * Post-processing / validation workflow
 *
 * Cross-checks the structure-based FoldSeek domain/family calls produced by
 * main.nf against independent sequence-based InterProScan annotations for the
 * same proteins:
 *   - CATH labels (final_domain_annotations.tsv) vs InterProScan Gene3D hits
 *   - Pfam hits (foldseek_parsed_results_non-cath.tsv, db == PfamSDB) vs InterProScan Pfam hits
 *   - general ID-mapping / hit coverage diagnostics across all non-CATH FoldSeek hits
 *
 * Run after main.nf has produced results for the same --project_name, e.g.:
 *   nextflow run post-processing.nf \
 *       --project_name <same as main.nf run> \
 *       --interproscan_output_file /path/to/interproscan_output.tsv
 */

// ===============================================
// PARAMETERS
// ===============================================

params.results_dir = "${workflow.launchDir}/results/${params.project_name}"
// Each run gets its own dedicated subfolder (Nextflow's auto-generated run name,
// e.g. "happy_einstein") so re-running never overwrites a previous run's tables/plots.
params.post_processing_results_dir = "${params.results_dir}/post_processing/${workflow.runName}"

params.final_domain_annotations_file = params.final_domain_annotations_file ?: "${params.results_dir}/final_domain_annotations.tsv"
params.foldseek_non_cath_file = params.foldseek_non_cath_file ?: "${params.results_dir}/foldseek_parsed_results_non-cath.tsv"
params.interproscan_keep_analyses = params.interproscan_keep_analyses ?: 'Gene3D,Pfam'
params.structural_source_dbs = params.structural_source_dbs ?: 'pdb,afdb50,afdb_swissprot'

// ===============================================
// MODULE IMPORTS
// ===============================================

include { filter_interproscan_results } from './modules/filter_interproscan_results.nf'
include { match_pipeline_names as match_names_cath } from './modules/match_pipeline_names.nf'
include { match_pipeline_names as match_names_pfam } from './modules/match_pipeline_names.nf'
include { compare_cath_annotations } from './modules/compare_cath_annotations.nf'
include { compare_pfam_annotations } from './modules/compare_pfam_annotations.nf'
include { diagnose_interpro_coverage } from './modules/diagnose_interpro_coverage.nf'
include { find_structural_only_hits } from './modules/find_structural_only_hits.nf'
include { plot_interpro_comparison } from './modules/plot_interpro_comparison.nf'
include { plot_structural_only_hits } from './modules/plot_structural_only_hits.nf'

// ===============================================
// HELPER FUNCTIONS
// ===============================================

def validateParameters() {
    if (!params.project_name) {
        error("Project name must be specified in the parameters.")
    }

    if (!params.interproscan_output_file || !file(params.interproscan_output_file).exists()) {
        error("InterProScan output file not found: ${params.interproscan_output_file}")
    }

    if (!file(params.final_domain_annotations_file).exists()) {
        error("Final domain annotations file not found: ${params.final_domain_annotations_file}. Has main.nf been run for project '${params.project_name}'?")
    }

    if (!file(params.foldseek_non_cath_file).exists()) {
        error("Non-CATH FoldSeek results file not found: ${params.foldseek_non_cath_file}. Has main.nf been run for project '${params.project_name}'?")
    }

    file(params.post_processing_results_dir).mkdirs()

    log.info(
        """
    ==============================================
    Post-processing: InterProScan validation
    ==============================================
    Project name                : ${params.project_name}
    Results dir                 : ${params.results_dir}
    Final domain annotations    : ${params.final_domain_annotations_file}
    Non-CATH FoldSeek results   : ${params.foldseek_non_cath_file}
    InterProScan output         : ${params.interproscan_output_file}
    InterProScan analyses kept  : ${params.interproscan_keep_analyses}
    Structural-only source dbs  : ${params.structural_source_dbs}
    Output dir                  : ${params.post_processing_results_dir}
    ==============================================
    """.stripIndent()
    )
}

// ===============================================
// MAIN WORKFLOW
// ===============================================

workflow {

    validateParameters()

    ch_final_domain_annotations = channel.value(file(params.final_domain_annotations_file))
    ch_foldseek_non_cath = channel.value(file(params.foldseek_non_cath_file))
    ch_interproscan_raw = channel.value(file(params.interproscan_output_file))

    // =========================================
    // PHASE 0: Filter InterProScan to the analyses we trust
    // =========================================
    // Raw InterProScan output also contains PANTHER/SUPERFAMILY/CDD/... and
    // disorder/feature predictors (MobiDBLite, Coils, ...) that we don't compare
    // against. Filtering them out up front keeps every downstream step (ID
    // mapping, joins, diagnostics) working on just the Gene3D + Pfam rows.

    ch_interproscan = filter_interproscan_results(
        ch_interproscan_raw,
        params.interproscan_keep_analyses,
    )

    // =========================================
    // PHASE 1: Map pipeline IDs -> InterProScan protein_accession
    // =========================================
    // Run separately per source file since each uses a different ID column
    // (uniprot_id in the per-domain final results vs query_id in the raw
    // FoldSeek hits), even though both reference the same underlying proteins.

    cath_match_columns_ch = match_names_cath(
        ch_final_domain_annotations,
        ch_interproscan,
        'uniprot_id',
        'cath',
    )

    pfam_match_columns_ch = match_names_pfam(
        ch_foldseek_non_cath,
        ch_interproscan,
        'query_id',
        'pfam',
    )

    // =========================================
    // PHASE 2: Compare structural calls to InterProScan
    // =========================================

    cath_comparison_ch = compare_cath_annotations(
        ch_final_domain_annotations,
        ch_interproscan,
        cath_match_columns_ch,
    )

    pfam_comparison_ch = compare_pfam_annotations(
        ch_foldseek_non_cath,
        ch_interproscan,
        pfam_match_columns_ch,
    )

    diagnose_interpro_coverage(
        ch_foldseek_non_cath,
        ch_interproscan,
        pfam_match_columns_ch,
        'query_id',
    )

    // =========================================
    // PHASE 3: Find structural-only hits (PDB/AFDB hit, no Gene3D/Pfam coverage)
    // =========================================
    // Reuses the query_id -> protein_accession mapping already built for the
    // Pfam comparison, since it comes from the same foldseek_non_cath file.

    structural_only_hits_ch = find_structural_only_hits(
        ch_foldseek_non_cath,
        ch_interproscan,
        pfam_match_columns_ch,
        params.structural_source_dbs,
    )

    // =========================================
    // PHASE 4: Plot the comparison summaries
    // =========================================

    plot_interpro_comparison(
        cath_comparison_ch,
        pfam_comparison_ch,
    )

    plot_structural_only_hits(structural_only_hits_ch.hits)

    cath_comparison_ch.view { f -> "CATH vs InterProScan comparison written to: " + f }
    pfam_comparison_ch.view { f -> "Pfam vs InterProScan comparison written to: " + f }
}
