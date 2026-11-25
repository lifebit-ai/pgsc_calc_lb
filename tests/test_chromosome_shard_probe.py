import gzip
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "bin" / "chromosome_shard_probe.py"


class ChromosomeShardProbeTest(unittest.TestCase):
    def write_bgzf(self, path, payload):
        compressor = zlib.compressobj(level=6, wbits=-15)
        compressed = compressor.compress(payload) + compressor.flush()
        block_size = 18 + len(compressed) + 8
        self.assertLessEqual(block_size, 65536)
        header = struct.pack("<BBBBIBBH", 31, 139, 8, 4, 0, 0, 255, 6)
        extra = b"BC" + struct.pack("<HH", 2, block_size - 1)
        footer = struct.pack("<II", zlib.crc32(payload), len(payload))
        path.write_bytes(header + extra + compressed + footer)

    def make_inputs(self, root, contig="chr20", index_contig=None, index_preset=2):
        vcf = root / "synthetic.vcf.gz"
        index = root / "synthetic.vcf.gz.tbi"
        vcf_payload = (
            b"##fileformat=VCFv4.2\n"
            b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE_A\n"
            + f"{contig}\t10\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n".encode()
            + f"{contig}\t20\t.\tC\tT\t.\tPASS\t.\tGT\t1/1\n".encode()
        )
        self.write_bgzf(vcf, vcf_payload)
        index_name = (index_contig or contig).encode() + b"\0"
        index_payload = (
            struct.pack(
                "<4s8i",
                b"TBI\x01",
                1,
                index_preset,
                1,
                2,
                0,
                ord("#"),
                0,
                len(index_name),
            )
            + index_name
            + struct.pack("<ii", 0, 0)
        )
        self.write_bgzf(index, index_payload)
        return vcf, index

    def run_probe(
        self, label, vcf, index, output, expected_contig="chr20", hold_seconds=0
    ):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--label",
                label,
                "--expected-contig",
                expected_contig,
                "--hold-seconds",
                str(hold_seconds),
                "--vcf",
                str(vcf),
                "--index",
                str(index),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_writes_metadata_only_receipt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            output = root / "receipt.tsv"

            result = self.run_probe("chr20", vcf, index, output)

            self.assertEqual(result.returncode, 0, result.stderr)
            rows = dict(
                line.split("\t", 1)
                for line in output.read_text(encoding="utf-8").splitlines()[1:]
            )
            expected_digest = hashlib.sha256(
                b"chr20\t10\tA\tG\nchr20\t20\tC\tT\n"
            ).hexdigest()
            self.assertEqual(rows["variant_count"], "2")
            self.assertEqual(rows["hold_seconds"], "0")
            self.assertEqual(rows["variant_key_sha256"], expected_digest)
            self.assertEqual(rows["index_sha256"], hashlib.sha256(index.read_bytes()).hexdigest())
            receipt = output.read_text(encoding="utf-8")
            self.assertEqual(
                set(rows),
                {
                    "label",
                    "expected_contig",
                    "hold_seconds",
                    "process",
                    "started_utc",
                    "completed_utc",
                    "elapsed_seconds",
                    "vcf_name",
                    "vcf_file_kind",
                    "vcf_size_bytes",
                    "index_name",
                    "index_file_kind",
                    "index_size_bytes",
                    "index_sha256",
                    "variant_count",
                    "variant_key_sha256",
                    "python_version",
                },
            )
            self.assertEqual(rows["process"], "CHROMOSOME_SHARD_PROBE")
            self.assertNotIn("SAMPLE_A", receipt)
            self.assertNotIn("0/1", receipt)
            self.assertNotIn("1/1", receipt)

    def test_rejects_mismatched_index_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            wrong_index = root / "wrong.tbi"
            index.rename(wrong_index)

            result = self.run_probe("chr20", vcf, wrong_index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Index must be named synthetic.vcf.gz.tbi", result.stderr)

    def test_rejects_corrupt_gzip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf = root / "synthetic.vcf.gz"
            index = root / "synthetic.vcf.gz.tbi"
            _, valid_index = self.make_inputs(root)
            self.assertEqual(index, valid_index)
            vcf.write_bytes(b"not-gzip")
            output = root / "receipt.tsv"

            result = self.run_probe("chr20", vcf, index, output)

            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())

    def test_rejects_non_tbi_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            self.write_bgzf(index, b"not-a-tbi-index")

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Index is not a tabix TBI file", result.stderr)

    def test_rejects_non_vcf_tabix_preset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root, index_preset=1)

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Tabix TBI is not configured for VCF input", result.stderr)

    def test_rejects_ordinary_gzip_vcf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            with gzip.open(vcf, "wb") as handle:
                handle.write(b"##fileformat=VCFv4.2\n")

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("VCF input is not BGZF-compressed", result.stderr)

    def test_rejects_invalid_bgzf_block_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            payload = bytearray(vcf.read_bytes())
            payload[16:18] = struct.pack("<H", 1)
            vcf.write_bytes(payload)

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("VCF input has an invalid BGZF block size", result.stderr)

    def test_rejects_vcf_preset_with_extra_flags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root, index_preset=0x10002)

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Tabix TBI is not configured for VCF input", result.stderr)

    def test_rejects_index_for_unexpected_contig(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root, index_contig="chr22")

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Tabix TBI does not contain expected contig chr20", result.stderr)

    def test_rejects_truncated_tbi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            self.write_bgzf(
                index,
                struct.pack("<4s8i", b"TBI\x01", 1, 2, 1, 2, 0, 35, 0, 6),
            )

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Truncated tabix TBI contig names", result.stderr)

    def test_rejects_unsafe_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)

            result = self.run_probe("chr20'; touch leaked; echo '", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Label may contain only", result.stderr)
            self.assertFalse((root / "leaked").exists())

    def test_rejects_unexpected_contig(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)

            result = self.run_probe(
                "chr22", vcf, index, root / "receipt.tsv", expected_contig="chr22"
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("expected chr22, observed chr20", result.stderr)

    def test_rejects_hold_above_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)

            result = self.run_probe(
                "chr20", vcf, index, root / "receipt.tsv", hold_seconds=1801
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Hold seconds must not exceed 1800", result.stderr)


if __name__ == "__main__":
    unittest.main()
