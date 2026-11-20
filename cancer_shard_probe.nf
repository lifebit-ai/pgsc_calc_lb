#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

process CANCER_SHARD_PROBE {
    tag "${shard_label}"

    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    cpus 4
    memory 4.GB
    time 4.h
    maxForks 3

    publishDir "${params.outdir}/cancer-shard-probe", mode: 'copy'

    input:
    tuple val(shard_label), val(expected_contig), path(vcf, stageAs: 'input.vcf.gz'), path(index, stageAs: 'input.vcf.gz.tbi')

    output:
    path "${shard_label}.localization-receipt.tsv", emit: receipt

    script:
    """
    cancer_shard_probe.py \
        --label '${shard_label}' \
        --expected-contig '${expected_contig}' \
        --hold-seconds '${params.hold_seconds}' \
        --vcf input.vcf.gz \
        --index input.vcf.gz.tbi \
        --output '${shard_label}.localization-receipt.tsv'
    """
}

workflow {
    required_params = [
        input_vcf_chr01: params.input_vcf_chr01,
        input_index_chr01: params.input_index_chr01,
        input_vcf_chr20: params.input_vcf_chr20,
        input_index_chr20: params.input_index_chr20,
        input_vcf_chr22: params.input_vcf_chr22,
        input_index_chr22: params.input_index_chr22
    ]
    missing_params = required_params.findAll { !it.value }.collect { "--${it.key}" }
    if (missing_params) {
        error "Please provide required Azure inputs: ${missing_params.join(', ')}"
    }
    if (!(params.hold_seconds.toString() ==~ /^[0-9]+$/)) {
        error "--hold_seconds must be a non-negative integer"
    }
    if ((params.hold_seconds as int) > 1800) {
        error "--hold_seconds must not exceed 1800"
    }

    input_ch = Channel.of(
        tuple(
            'chr01',
            'chr1',
            file(params.input_vcf_chr01, checkIfExists: true),
            file(params.input_index_chr01, checkIfExists: true)
        ),
        tuple(
            'chr20',
            'chr20',
            file(params.input_vcf_chr20, checkIfExists: true),
            file(params.input_index_chr20, checkIfExists: true)
        ),
        tuple(
            'chr22',
            'chr22',
            file(params.input_vcf_chr22, checkIfExists: true),
            file(params.input_index_chr22, checkIfExists: true)
        )
    )

    CANCER_SHARD_PROBE(input_ch)
}
