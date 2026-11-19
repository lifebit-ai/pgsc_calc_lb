# Container Registry Connectivity Test - 2026-11-18

## Purpose

Determine which public container registries are reachable from an interactive
session in the IHLAD TRE, and distinguish registry/firewall failures from image
name, short-name resolution, rate-limit, architecture, and runtime failures.

Do not add registry credentials, use private images, enable debug logging, or
copy bearer tokens into this note.

## Test Environment

| Field | Observation |
| --- | --- |
| Session type | VSCode interactive session |
| Cloud | Azure |
| Runtime | Podman 4.9.3 |
| Architecture | amd64 |
| Podman graph root | `/home/vscode/.local/share/containers/storage` |
| Graph-root backing volume | `/mnt/libraries`, 50 GB total |
| Available graph-root disk | 47 GB before pulls; 7% used |

The Podman image store was empty before testing. All three test images reported
`not_cached`, so each pull will exercise registry manifest and layer access.

## Safety Rules

- Use fully qualified image names for registry tests.
- Record whether an image was already cached before pulling.
- Do not run `podman system prune`.
- Do not remove images that predated this test.
- Do not use `--log-level=debug` unless standard output is insufficient; debug
  output may contain registry authentication details.
- Pulled images consume interactive-session storage.

## Test Images

| Registry | Image | Why selected |
| --- | --- | --- |
| GHCR | `ghcr.io/pgscatalog/pyyaml:6.0` | Known to work in DoH Azure Batch and required by the current workflow |
| Docker Hub | `docker.io/library/ubuntu:22.04` | Exact public image family that failed in Azure Batch |
| Quay | `quay.io/lifebitaiorg/samtools` | Public image used in Lifebit's official Podman documentation |

The Docker Hub shorthand `ubuntu:22.04` is a separate short-name-resolution
test, not the primary registry test.

## Baseline Commands

```bash
podman --version
podman info --format 'arch={{.Host.Arch}} graphRoot={{.Store.GraphRoot}}'
podman image list

for image in \
    ghcr.io/pgscatalog/pyyaml:6.0 \
    docker.io/library/ubuntu:22.04 \
    quay.io/lifebitaiorg/samtools
do
    if podman image exists "$image"; then
        printf 'cached\t%s\n' "$image"
    else
        printf 'not_cached\t%s\n' "$image"
    fi
done
```

After identifying the graph root, check its backing filesystem capacity with
`df -h <graph-root>`.

## Pull and Runtime Tests

Run one at a time.

### GHCR control

```bash
time podman pull ghcr.io/pgscatalog/pyyaml:6.0
podman image inspect ghcr.io/pgscatalog/pyyaml:6.0 \
    --format 'digest={{.Digest}} arch={{.Architecture}} size={{.Size}}'
podman run --rm ghcr.io/pgscatalog/pyyaml:6.0 \
    bash -c 'python --version && echo GHCR_RUN_OK'
```

### Docker Hub

```bash
time podman pull docker.io/library/ubuntu:22.04
podman image inspect docker.io/library/ubuntu:22.04 \
    --format 'digest={{.Digest}} arch={{.Architecture}} size={{.Size}}'
podman run --rm docker.io/library/ubuntu:22.04 \
    bash -c 'cat /etc/os-release | grep PRETTY_NAME; echo DOCKERHUB_RUN_OK'
```

### Quay

```bash
time podman pull quay.io/lifebitaiorg/samtools
podman image inspect quay.io/lifebitaiorg/samtools \
    --format 'digest={{.Digest}} arch={{.Architecture}} size={{.Size}}'
podman run --rm quay.io/lifebitaiorg/samtools \
    samtools --version
```

### Optional Docker Hub short-name test

Only after the fully qualified Docker Hub test:

```bash
podman pull ubuntu:22.04
```

A short-name failure with a successful fully qualified pull is a Podman registry
search-policy issue, not a firewall failure.

## Results

| Registry/image | Cached before | Pull | Manifest/digest | Run | Elapsed | Error classification |
| --- | --- | --- | --- | --- | --- | --- |
| GHCR/pyyaml | No | Success; signatures, seven blobs, config and manifest copied | Pull returned image ID beginning `fdcc8188`; user reported subsequent checks looked good | Reported success | 5.548 s | None |
| Docker Hub/Ubuntu | No | Success; signatures, one blob, config and manifest copied | amd64; 80,869,588 bytes; reported digest begins `sha256:8abcafcf` | Success: Ubuntu 22.04.5 LTS and `DOCKERHUB_RUN_OK` | 3.092 s | Harmless rootless IPv6 sysctl warning during run |
| Quay/Lifebit samtools | No | Success | `sha256:272999639cdf356e8427e1cd6c4f1dc4fd20b0e8242fb859e3d8758b3b03d38`; amd64; 568,398,789 bytes | Success: samtools 1.10 / htslib 1.10.2 | Not captured | Non-fatal IPv6 sysctl warning and parse message |
| Docker Hub short name | Qualified image already cached | Success | Resolved to Docker Hub image | Not rerun | Not recorded | None |
| Docker Hub Alpine short name | Not recorded | Success; layer, config and manifest copied | Podman explicitly resolved alias to `docker.io/library/alpine:3.20`; pull returned image ID beginning `bf8527eb` | Run pending | 2.348 s | None |

### GHCR pull observation

The uncached pull of `ghcr.io/pgscatalog/pyyaml:6.0` completed successfully in
5.548 seconds. Podman retrieved signatures, all seven layers, image config, and
the manifest. This confirms GHCR registry and layer-host access from the
interactive session. The user reported the subsequent inspection/runtime checks
looked good; exact output was not captured in this note.

### Docker Hub observation

The uncached, fully qualified pull of `docker.io/library/ubuntu:22.04`
completed in 3.092 seconds. Podman retrieved signatures, the image layer,
configuration, and manifest. Inspection reported amd64 and 80,869,588 bytes.
The screen-captured digest contained an OCR-ambiguous character, so only the
verified prefix is retained here.

The container ran successfully and reported Ubuntu 22.04.5 LTS followed by
`DOCKERHUB_RUN_OK`. Podman emitted a warning that it could not set an IPv6
`accept_dad` sysctl on a read-only procfs; this did not prevent execution.

This confirms Docker Hub registry, layer-host, image, and runtime access from
the interactive session. It does not by itself prove identical firewall access
from Azure Batch workers.

The shorthand pull `podman pull ubuntu:22.04` also succeeded. This confirms the
interactive session's Podman configuration can resolve the unqualified image
name. Together with the fully qualified pull and successful run, the earlier
Azure Batch rejection is more likely to involve Batch-specific image-reference
validation, Batch network policy, or the old Nextflow Azure executor than an
interactive-session Podman or general Docker Hub failure.

An independent short-name pull of uncached `alpine:3.20` completed in 2.348
seconds. Podman reported:

```text
Resolved "alpine" as an alias
(/etc/containers/registries.conf.d/shortnames.conf)
Trying to pull docker.io/library/alpine:3.20
```

This proves short-name behavior in the interactive session comes from Podman's
configured alias table, not a generic image-name feature shared with Azure
Batch. Nextflow's Azure Batch executor does not apply the interactive session's
Podman `shortnames.conf`.

### Quay observation

The uncached pull of `quay.io/lifebitaiorg/samtools` succeeded. Inspection
reported digest
`sha256:272999639cdf356e8427e1cd6c4f1dc4fd20b0e8242fb859e3d8758b3b03d38`,
amd64, and 568,398,789 bytes.

The container executed `samtools --version` and reported samtools 1.10 with
htslib 1.10.2. It also emitted the same non-fatal rootless IPv6 sysctl warning
and a parse message before the version output. Because the requested binary ran,
these messages are image/runtime behavior, not a Quay registry-access failure.

### Interactive-session conclusion

All tested public registries are reachable from the interactive session:

- GHCR: pull and execution succeeded.
- Docker Hub: fully qualified pull, shorthand resolution, and execution
  succeeded.
- Quay: pull, inspection, and execution succeeded.

The local image store now contains approximately 81 MB of Ubuntu, 143 MB of
PGSCatalog pyyaml, and 568 MB of Lifebit samtools images, approximately 792 MB
as displayed by Podman. This test does not prove that Azure Batch workers use
the same network route or image-reference validation.

### Azure Batch acceptance

An isolated workflow at Git revision
`bff3ba6a280844a39b372199786ed36580758a68` used:

```nextflow
container 'docker.io/library/ubuntu:22.04'
```

The Azure Batch analysis completed successfully. The otherwise equivalent
earlier workflow using `ubuntu:22.04` failed before command execution with
`One or more container images specified are invalid`.

This isolates the failure to unqualified image-reference handling in the DoH
Nextflow/Azure Batch path. Docker Hub registry access, layer access, image
architecture, and container execution all work. Use fully qualified container
references for this deployment.

### Nextflow 22.11.1-edge source confirmation

Inspection of the exact upstream source for Nextflow `v22.11.1-edge` confirms
that the Azure executor does not qualify or otherwise rewrite the process image
name. `AzBatchTaskHandler` submits the process task to `AzBatchService`, where
`createTask()` reads `task.getContainer()` and passes the resulting string
directly to Azure's `TaskContainerSettings.withImageName(container)`.

The corresponding upstream unit test uses `ubuntu:latest` and asserts that
Azure's task container setting remains exactly `ubuntu:latest`. The executor's
default registry server of `docker.io` configures pool registry credentials; it
is not prepended to the process image name. No Podman, `shortnames.conf`, or
`registries.conf` handling exists in the `nf-azure` source at this revision.

Therefore the supported post-mortem wording is:

- Interactive Podman resolved short names through its local alias
  configuration.
- Nextflow `22.11.1-edge` passed the configured process image name unchanged to
  Azure Batch.
- Azure Batch rejected the unqualified reference and accepted the fully
  qualified reference in the observed runs.
- There is no evidence that the Batch worker literally lacked a
  `shortnames.conf` file; that claim is unnecessary and should not be made.

Upstream source evidence:

- [`AzBatchTaskHandler.groovy`](https://github.com/nextflow-io/nextflow/blob/4fc071ff773fee7c0d3d3b52e6ab92f9e4e362dd/plugins/nf-azure/src/main/nextflow/cloud/azure/batch/AzBatchTaskHandler.groovy#L78-L93)
- [`AzBatchService.groovy`](https://github.com/nextflow-io/nextflow/blob/4fc071ff773fee7c0d3d3b52e6ab92f9e4e362dd/plugins/nf-azure/src/main/nextflow/cloud/azure/batch/AzBatchService.groovy#L368-L406)
- [`AzBatchServiceTest.groovy`](https://github.com/nextflow-io/nextflow/blob/4fc071ff773fee7c0d3d3b52e6ab92f9e4e362dd/plugins/nf-azure/src/test/nextflow/cloud/azure/batch/AzBatchServiceTest.groovy#L460-L490)
- [Nextflow issue 2354](https://github.com/nextflow-io/nextflow/issues/2354),
  explaining why Nextflow cannot safely assume and prepend one default registry

## Failure Classification

| Symptom | Likely layer |
| --- | --- |
| DNS lookup failure | DNS/firewall configuration |
| Connection timeout/refused | Network/firewall route |
| TLS or unknown authority | Organization CA/certificate configuration |
| HTTP 401 while probing `/v2/` | Registry is reachable; authentication challenge is normal for public pulls |
| HTTP 403 | Firewall/policy or registry authorization |
| HTTP 429 | Registry rate limit, especially Docker Hub |
| Manifest unknown/not found | Wrong image/tag, not necessarily firewall |
| No matching manifest | CPU architecture mismatch |
| Blob/layer download failure after manifest succeeds | CDN/layer host blocked or interrupted |
| Pull succeeds but run fails | Image entrypoint/runtime/content issue, not registry access |
| Short name fails, qualified name succeeds | Podman short-name registry policy |

## If a Pull Fails

Capture only standard error text first. Then test registry reachability:

```bash
getent hosts ghcr.io
getent hosts registry-1.docker.io
getent hosts auth.docker.io
getent hosts production.cloudflare.docker.com
getent hosts quay.io

curl -sS -o /dev/null -w 'ghcr status=%{http_code}\n' https://ghcr.io/v2/
curl -sS -o /dev/null -w 'docker status=%{http_code}\n' https://registry-1.docker.io/v2/
curl -sS -o /dev/null -w 'quay status=%{http_code}\n' https://quay.io/v2/
```

Do not paste tokens, authorization headers, private registry URLs, or verbose
debug logs into Git.

## Cleanup

List images and sizes after testing:

```bash
podman image list
```

Remove only images confirmed as newly pulled and no longer needed:

```bash
podman image rm <fully-qualified-image>
```

Keep `ghcr.io/pgscatalog/pyyaml:6.0` if it will be reused for workflow or
interactive validation.

## Documentation Source

- [Install tools and plugins in a VSCode session](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1713799629/Install+tools+and+plugins+in+VSCode)
