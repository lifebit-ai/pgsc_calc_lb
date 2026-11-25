#!/usr/bin/env python3

import argparse
import gzip
import hashlib
import platform
import re
import stat
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_HOLD_SECONDS = 1800
MAX_TBI_ITEMS = 10_000_000
MAX_TBI_NAME_BYTES = 16 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_vcf(path, expected_contig):
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
            if fields[0] != expected_contig.encode("ascii"):
                observed = fields[0].decode("ascii", errors="replace")
                raise ValueError(
                    f"Unexpected VCF contig at line {line_number}: "
                    f"expected {expected_contig}, observed {observed}"
                )
            digest.update(b"\t".join((fields[0], fields[1], fields[3], fields[4])))
            digest.update(b"\n")
            variant_count += 1
    if not found_fileformat or not found_header:
        raise ValueError("VCF fileformat or #CHROM header is missing")
    if variant_count == 0:
        raise ValueError("VCF contains no variant records")
    return variant_count, digest.hexdigest()


def validate_bgzf(path, description):
    with path.open("rb") as handle:
        block_count = 0
        while True:
            header = handle.read(12)
            if not header:
                break
            if len(header) != 12 or header[:4] != b"\x1f\x8b\x08\x04":
                raise ValueError(f"{description} is not BGZF-compressed")
            extra_size = struct.unpack("<H", header[10:12])[0]
            extra = handle.read(extra_size)
            if len(extra) != extra_size:
                raise ValueError(f"{description} has a truncated BGZF header")

            block_size = None
            offset = 0
            while offset + 4 <= len(extra):
                subfield_id = extra[offset : offset + 2]
                subfield_size = struct.unpack("<H", extra[offset + 2 : offset + 4])[0]
                offset += 4
                if offset + subfield_size > len(extra):
                    raise ValueError(f"{description} has an invalid BGZF header")
                if subfield_id == b"BC" and subfield_size == 2:
                    block_size = struct.unpack("<H", extra[offset : offset + 2])[0] + 1
                offset += subfield_size

            minimum_size = 12 + extra_size + 8
            if block_size is None or not minimum_size <= block_size <= 65536:
                raise ValueError(f"{description} has an invalid BGZF block size")
            remaining = block_size - 12 - extra_size
            if len(handle.read(remaining)) != remaining:
                raise ValueError(f"{description} has a truncated BGZF block")
            block_count += 1

        if block_count == 0:
            raise ValueError(f"{description} is not BGZF-compressed")


def read_exact(handle, size, description):
    value = handle.read(size)
    if len(value) != size:
        raise ValueError(f"Truncated tabix TBI {description}")
    return value


def discard_exact(handle, size, description):
    remaining = size
    while remaining:
        chunk = handle.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError(f"Truncated tabix TBI {description}")
        remaining -= len(chunk)


def read_count(handle, description):
    count = struct.unpack("<i", read_exact(handle, 4, description))[0]
    if count < 0 or count > MAX_TBI_ITEMS:
        raise ValueError(f"Invalid tabix TBI {description}")
    return count


def validate_tbi(path, expected_contig):
    with gzip.open(path, "rb") as handle:
        magic = read_exact(handle, 4, "header")
        if magic != b"TBI\x01":
            raise ValueError("Index is not a tabix TBI file")
        header = magic + read_exact(handle, 32, "header")
        _, n_ref, preset, col_seq, col_beg, col_end, meta, skip, names_size = struct.unpack(
            "<4s8i", header
        )
        if n_ref < 1 or n_ref > MAX_TBI_ITEMS:
            raise ValueError("Invalid tabix TBI reference count")
        if names_size < 1 or names_size > MAX_TBI_NAME_BYTES:
            raise ValueError("Invalid tabix TBI header")
        if preset != 2 or (col_seq, col_beg, col_end, meta, skip) != (
            1,
            2,
            0,
            ord("#"),
            0,
        ):
            raise ValueError("Tabix TBI is not configured for VCF input")

        names_blob = read_exact(handle, names_size, "contig names")
        if not names_blob.endswith(b"\0"):
            raise ValueError("Invalid tabix TBI contig names")
        names = names_blob[:-1].split(b"\0")
        if len(names) != n_ref:
            raise ValueError("Tabix TBI reference count does not match contig names")
        contigs = {name.decode("utf-8") for name in names}
        if expected_contig not in contigs:
            raise ValueError(f"Tabix TBI does not contain expected contig {expected_contig}")

        for _ in range(n_ref):
            for _ in range(read_count(handle, "bin count")):
                read_exact(handle, 4, "bin identifier")
                discard_exact(handle, read_count(handle, "chunk count") * 16, "chunks")
            discard_exact(handle, read_count(handle, "linear index count") * 8, "linear index")

        trailer = handle.read()
        if len(trailer) not in (0, 8):
            raise ValueError("Invalid tabix TBI trailer")


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
        description="Create a metadata-only receipt for a staged chromosome VCF shard"
    )
    parser.add_argument("--label", required=True)
    parser.add_argument("--expected-contig", required=True)
    parser.add_argument("--hold-seconds", type=int, default=0)
    parser.add_argument("--vcf", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    started = datetime.now(timezone.utc)

    if not LABEL_PATTERN.fullmatch(args.label):
        raise ValueError("Label may contain only letters, numbers, dot, underscore, and hyphen")
    if not LABEL_PATTERN.fullmatch(args.expected_contig):
        raise ValueError("Expected contig may contain only letters, numbers, dot, underscore, and hyphen")
    if args.hold_seconds < 0:
        raise ValueError("Hold seconds must be non-negative")
    if args.hold_seconds > MAX_HOLD_SECONDS:
        raise ValueError(f"Hold seconds must not exceed {MAX_HOLD_SECONDS}")
    if not args.vcf.name.endswith(".vcf.gz"):
        raise ValueError("VCF input must end with .vcf.gz")
    if args.index.name != args.vcf.name + ".tbi":
        raise ValueError(f"Index must be named {args.vcf.name}.tbi")
    if not args.vcf.is_file() or args.vcf.stat().st_size == 0:
        raise ValueError("VCF input is missing or empty")
    if not args.index.is_file() or args.index.stat().st_size == 0:
        raise ValueError("Index input is missing or empty")

    validate_bgzf(args.vcf, "VCF input")
    validate_bgzf(args.index, "Tabix index")
    vcf_stat = args.vcf.stat()
    index_stat = args.index.stat()
    if args.hold_seconds:
        time.sleep(args.hold_seconds)
    variant_count, variant_key_sha256 = inspect_vcf(args.vcf, args.expected_contig)
    validate_tbi(args.index, args.expected_contig)
    completed = datetime.now(timezone.utc)

    rows = [
        ("label", args.label),
        ("expected_contig", args.expected_contig),
        ("hold_seconds", args.hold_seconds),
        ("process", "CHROMOSOME_SHARD_PROBE"),
        ("started_utc", started.isoformat()),
        ("completed_utc", completed.isoformat()),
        ("elapsed_seconds", f"{(completed - started).total_seconds():.3f}"),
        ("vcf_name", args.vcf.name),
        ("vcf_file_kind", file_kind(args.vcf)),
        ("vcf_size_bytes", vcf_stat.st_size),
        ("index_name", args.index.name),
        ("index_file_kind", file_kind(args.index)),
        ("index_size_bytes", index_stat.st_size),
        ("index_sha256", sha256_file(args.index)),
        ("variant_count", variant_count),
        ("variant_key_sha256", variant_key_sha256),
        ("python_version", platform.python_version()),
    ]
    write_receipt(args.output, rows)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
