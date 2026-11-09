#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

params.input_file = null
params.outdir = params.outdir ?: 'results'

process STAGE_INPUT {
    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    publishDir "${params.outdir}/input", mode: 'copy'

    input:
    path source_file

    output:
    path 'received.txt', emit: received
    path 'input-context.txt', emit: context

    script:
    """
    cp ${source_file} received.txt

    {
        echo "process=STAGE_INPUT"
        echo -n "hostname="
        cat /etc/hostname
        echo -n "working_directory="
        pwd
        echo "source_name=${source_file}"
        echo -n "source_size_bytes="
        wc -c < ${source_file}
        echo -n "source_sha256="
        sha256sum ${source_file} | cut -d ' ' -f 1
        echo -n "received_size_bytes="
        wc -c < received.txt
        echo -n "received_sha256="
        sha256sum received.txt | cut -d ' ' -f 1
    } > input-context.txt
    """
}

workflow {
    if (!params.input_file) {
        error "Please provide --input_file using the Lifebit file selector"
    }

    input_ch = Channel.fromPath(params.input_file, checkIfExists: true)
    STAGE_INPUT(input_ch)
}
