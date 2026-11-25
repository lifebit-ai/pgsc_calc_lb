import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChromosomeShardSchemaTest(unittest.TestCase):
    def test_schema_index_points_to_probe_schema(self):
        schema_index = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))

        self.assertEqual(
            schema_index,
            {
                "schemas": [
                    {
                        "name": "Chromosome scale-out probe",
                        "filePath": "nextflow_schema.json",
                    }
                ]
            },
        )

    def test_schema_groups_required_inputs_and_execution_defaults(self):
        schema = json.loads((ROOT / "nextflow_schema.json").read_text(encoding="utf-8"))
        inputs = schema["definitions"]["input_options"]
        execution = schema["definitions"]["execution_options"]["properties"]

        self.assertIn("/chromosome_probe_01/", schema["$id"])

        self.assertEqual(
            inputs["required"],
            [
                "input_vcf_chr01",
                "input_index_chr01",
                "input_vcf_chr20",
                "input_index_chr20",
                "input_vcf_chr22",
                "input_index_chr22",
            ],
        )
        for name in inputs["required"]:
            self.assertEqual(inputs["properties"][name]["type"], "string")
            self.assertEqual(inputs["properties"][name]["format"], "file-path")
            self.assertTrue(inputs["properties"][name]["exists"])
        self.assertEqual(execution["hold_seconds"]["default"], 1200)
        self.assertEqual(execution["hold_seconds"]["maximum"], 1800)
        self.assertEqual(execution["outdir"]["default"], "results")
        self.assertEqual(
            schema["allOf"],
            [
                {"$ref": "#/definitions/input_options"},
                {"$ref": "#/definitions/execution_options"},
            ],
        )

    def test_probe_defaults_are_defined_only_in_nextflow_config(self):
        config = (ROOT / "nextflow.config").read_text(encoding="utf-8")
        workflow = (ROOT / "chromosome_shard_probe.nf").read_text(encoding="utf-8")
        expected_defaults = {
            "input_vcf_chr01": "null",
            "input_index_chr01": "null",
            "input_vcf_chr20": "null",
            "input_index_chr20": "null",
            "input_vcf_chr22": "null",
            "input_index_chr22": "null",
            "hold_seconds": "1200",
            "outdir": '"$launchDir/results"',
        }

        for name, value in expected_defaults.items():
            self.assertRegex(config, rf"(?m)^\s*{name}\s*=\s*{re.escape(value)}\s*$")
            self.assertNotRegex(workflow, rf"(?m)^\s*params\.{name}\s*=")

    def test_params_file_template_matches_public_parameters(self):
        template = (
            ROOT / "assets/examples/chromosome_shard_probe.params.example.yaml"
        ).read_text(encoding="utf-8")
        values = dict(
            line.split(": ", 1)
            for line in template.splitlines()
            if line and not line.startswith("#")
        )
        base = "az://<account>/<container>/<blob-key>"

        self.assertEqual(
            values,
            {
                "input_vcf_chr01": f'"{base}/chr01/<vcf-file>.vcf.gz"',
                "input_index_chr01": f'"{base}/chr01/<vcf-file>.vcf.gz.tbi"',
                "input_vcf_chr20": f'"{base}/chr20/<vcf-file>.vcf.gz"',
                "input_index_chr20": f'"{base}/chr20/<vcf-file>.vcf.gz.tbi"',
                "input_vcf_chr22": f'"{base}/chr22/<vcf-file>.vcf.gz"',
                "input_index_chr22": f'"{base}/chr22/<vcf-file>.vcf.gz.tbi"',
                "hold_seconds": "1200",
                "outdir": '"chromosome-shard-scaleout-<unique-run-name>"',
            },
        )


if __name__ == "__main__":
    unittest.main()
