#!/usr/bin/env python3

import argparse
import gzip
import hashlib
import os
import platform
import re
import socket
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
AZURE_ENV_KEYS = ("AZ_BATCH_POOL_ID", "AZ_BATCH_NODE_ID", "AZ_BATCH_TASK_ID")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mount_details(path):
    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.exists():
        return "unavailable", "unavailable"

    target = str(path.resolve())
    best_mount = ""
    best_type = "unavailable"
    for line in mountinfo.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        mount_point = fields[4].replace("\\040", " ").replace("\\011", "\t")
        if target == mount_point or target.startswith(mount_point.rstrip("/") + "/"):
            if len(mount_point) > len(best_mount):
                best_mount = mount_point
                best_type = fields[separator + 1]
    return best_type, best_mount or "unavailable"


def inspect_vcf(path):
    digest = hashlib.sha256()
    variant_count = 0
    found_fileformat = False
    found_header = False
    with gzip.open(path, "rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.startswith(b"##fileformat=VCF"):
                found_fileformat = True
                continue
            if line.startswith(b"#CHROM\t"):
                found_header = True
                continue
            if line.startswith(b"#"):
                continue
            if not found_fileformat or not found_header:
                raise ValueError("VCF records must follow fileformat and #CHROM headers")
            fields = line.rstrip(b"\r\n").split(b"\t", 8)
            if len(fields) < 8:
                raise ValueError(f"Malformed VCF record at line {line_number}")
            try:
                position = int(fields[1])
            except ValueError as error:
                raise ValueError(f"Invalid VCF position at line {line_number}") from error
            if position < 1:
                raise ValueError(f"Invalid VCF position at line {line_number}")
            digest.update(b"\t".join((fields[0], fields[1], fields[3], fields[4])))
            digest.update(b"\n")
            variant_count += 1
    if not found_fileformat or not found_header:
        raise ValueError("VCF fileformat or #CHROM header is missing")
    if variant_count == 0:
        raise ValueError("VCF contains no variant records")
    return variant_count, digest.hexdigest()


def validate_tbi(path):
    with gzip.open(path, "rb") as handle:
        if handle.read(4) != b"TBI\x01":
            raise ValueError("Index is not a tabix TBI file")


def file_kind(path):
    if path.is_symlink():
        return "symlink"
    return "regular" if stat.S_ISREG(path.stat().st_mode) else "other"


def write_receipt(output, rows):
    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("key\tvalue\n")
        for key, value in rows:
            text = str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")
            handle.write(f"{key}\t{text}\n")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a metadata-only receipt for a staged cancer VCF shard"
    )
    parser.add_argument("--label", required=True)
    parser.add_argument("--vcf", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    started = datetime.now(timezone.utc)

    if not LABEL_PATTERN.fullmatch(args.label):
        raise ValueError("Label may contain only letters, numbers, dot, underscore, and hyphen")
    if not args.vcf.name.endswith(".vcf.gz"):
        raise ValueError("VCF input must end with .vcf.gz")
    if args.index.name != args.vcf.name + ".tbi":
        raise ValueError(f"Index must be named {args.vcf.name}.tbi")
    if not args.vcf.is_file() or args.vcf.stat().st_size == 0:
        raise ValueError("VCF input is missing or empty")
    if not args.index.is_file() or args.index.stat().st_size == 0:
        raise ValueError("Index input is missing or empty")

    vcf_stat = args.vcf.stat()
    index_stat = args.index.stat()
    filesystem_type, mount_target = mount_details(args.vcf)
    variant_count, variant_key_sha256 = inspect_vcf(args.vcf)
    validate_tbi(args.index)
    completed = datetime.now(timezone.utc)

    rows = [
        ("label", args.label),
        ("process", "CANCER_SHARD_PROBE"),
        ("started_utc", started.isoformat()),
        ("completed_utc", completed.isoformat()),
        ("elapsed_seconds", f"{(completed - started).total_seconds():.3f}"),
        ("hostname", socket.gethostname()),
        ("working_directory", Path.cwd().resolve()),
        ("vcf_name", args.vcf.name),
        ("vcf_resolved_path", args.vcf.resolve()),
        ("vcf_file_kind", file_kind(args.vcf)),
        ("vcf_size_bytes", vcf_stat.st_size),
        ("vcf_device", vcf_stat.st_dev),
        ("vcf_inode", vcf_stat.st_ino),
        ("index_name", args.index.name),
        ("index_resolved_path", args.index.resolve()),
        ("index_file_kind", file_kind(args.index)),
        ("index_size_bytes", index_stat.st_size),
        ("index_sha256", sha256_file(args.index)),
        ("filesystem_type", filesystem_type),
        ("filesystem_mount_target", mount_target),
        ("variant_count", variant_count),
        ("variant_key_sha256", variant_key_sha256),
        ("python_version", platform.python_version()),
    ]
    rows.extend((key.lower(), os.environ.get(key, "not_set")) for key in AZURE_ENV_KEYS)
    write_receipt(args.output, rows)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
