#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Adapted from domain_annotation_pipeline/modules/run_stride.nf
// A STRIDE failure on one *.pdb in a batch used to be silently `continue`d past with
// no trace once params.debug was off, and the whole batch's output was a non-optional
// glob that hard-failed if every file in it failed. Now failures are always recorded
// to stride_failures.tsv and a partial/empty batch doesn't fail the task.

process run_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    tuple val(id), path('*')

    output:
    tuple val(id), path('*.stride', optional: true), path('stride_failures.tsv')

    script:
    """
    : > stride_failures.tsv
    for f in *.pdb; do
        if stride \$f > \${f%.pdb}.stride 2> \${f%.pdb}.stride.err; then
            :
        else
            status=\$?
            echo "WARNING: STRIDE failed on \$f (exit \$status), see \${f%.pdb}.stride.err"
            errmsg=\$(tail -n1 \${f%.pdb}.stride.err 2>/dev/null)
            printf '%s|%s|%s\\n' "\$f" "\$status" "\$errmsg" >> stride_failures.tsv
        fi
    done
    """
}
