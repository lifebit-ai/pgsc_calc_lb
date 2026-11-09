#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

params.outdir = params.outdir ?: 'results'

process HELLO {
    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    publishDir params.outdir, mode: 'copy'

    output:
    path 'hello.txt'

    script:
    """
    echo "Hello from Lifebit" > hello.txt
    """
}

workflow {
    HELLO()
}
