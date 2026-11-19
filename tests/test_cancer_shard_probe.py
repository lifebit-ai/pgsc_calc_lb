import gzip
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "bin" / "cancer_shard_probe.py"


class CancerShardProbeTest(unittest.TestCase):
    def make_inputs(self, root):
        vcf = root / "synthetic.vcf.gz"
        index = root / "synthetic.vcf.gz.tbi"
        with gzip.open(vcf, "wb") as handle:
            handle.write(b"##fileformat=VCFv4.2\n")
            handle.write(b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE_A\n")
            handle.write(b"chr20\t10\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n")
            handle.write(b"chr20\t20\t.\tC\tT\t.\tPASS\t.\tGT\t1/1\n")
        with gzip.open(index, "wb") as handle:
            handle.write(b"TBI\x01synthetic-index\n")
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
                    "hostname",
                    "working_directory",
                    "vcf_name",
                    "vcf_resolved_path",
                    "vcf_file_kind",
                    "vcf_size_bytes",
                    "vcf_device",
                    "vcf_inode",
                    "index_name",
                    "index_resolved_path",
                    "index_file_kind",
                    "index_size_bytes",
                    "index_sha256",
                    "filesystem_type",
                    "filesystem_mount_target",
                    "variant_count",
                    "variant_key_sha256",
                    "python_version",
                    "az_batch_pool_id",
                    "az_batch_node_id",
                    "az_batch_task_id",
                },
            )
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
            vcf.write_bytes(b"not-gzip")
            with gzip.open(index, "wb") as handle:
                handle.write(b"TBI\x01synthetic-index\n")
            output = root / "receipt.tsv"

            result = self.run_probe("chr20", vcf, index, output)

            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())

    def test_rejects_non_tbi_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vcf, index = self.make_inputs(root)
            with gzip.open(index, "wb") as handle:
                handle.write(b"not-a-tbi-index")

            result = self.run_probe("chr20", vcf, index, root / "receipt.tsv")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Index is not a tabix TBI file", result.stderr)

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
