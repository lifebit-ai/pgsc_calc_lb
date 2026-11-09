#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

params.outdir = params.outdir ?: 'results'

process PRODUCE_FILE {
    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    publishDir "${params.outdir}/producer", mode: 'copy'

    output:
    path 'message.txt', emit: message
    path 'producer-context.txt', emit: context

    script:
    """
    echo "Hello from producer" > message.txt

    {
        echo "process=PRODUCE_FILE"
        echo -n "hostname="
        cat /etc/hostname
        echo -n "working_directory="
        pwd
        echo -n "message_sha256="
        sha256sum message.txt | cut -d ' ' -f 1
    } > producer-context.txt
    """
}

process CONSUME_FILE {
    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    publishDir "${params.outdir}/consumer", mode: 'copy'

    input:
    path message

    output:
    path 'final.txt', emit: result
    path 'consumer-context.txt', emit: context

    script:
    """
    grep -Fxq "Hello from producer" ${message}
    cat ${message} > final.txt
    echo "Processed by consumer" >> final.txt

    {
        echo "process=CONSUME_FILE"
        echo -n "hostname="
        cat /etc/hostname
        echo -n "working_directory="
        pwd
        echo "input_name=${message}"
        echo -n "input_sha256="
        sha256sum ${message} | cut -d ' ' -f 1
        echo -n "final_sha256="
        sha256sum final.txt | cut -d ' ' -f 1
    } > consumer-context.txt
    """
}

workflow {
    PRODUCE_FILE()
    CONSUME_FILE(PRODUCE_FILE.out.message)
}
