# GCP Enterprise Infrastructure & Bazel RBE Setup Guide for Angular Workflows

> **Reference Baseline**: Upstream `angular/angular` at commit `58e1d9a23c` (prior to `sajuptpm` dual-mode workflow modifications).  
> **Covered Services**: Google Cloud RBE, Google Cloud Storage (GCS), Google BigQuery, and Workload Identity Federation (WIF).

---

## 1. Where These 4 Services Are Used in Upstream Angular Workflows

| Service | Used in Upstream Workflow(s) (`58e1d9a23c`) | Exact Jobs / Configuration Details |
| :--- | :--- | :--- |
| **Google Cloud RBE**<br>(`remotebuildexecution.googleapis.com`) | • [`.github/workflows/ci.yml`](file:///c:/projects/angular/.github/workflows/ci.yml) (`CI (push)`)<br>• [`.github/workflows/pr.yml`](file:///c:/projects/angular/.github/workflows/pr.yml) (`Pull Request`)<br>• [`.github/workflows/adev-preview-build.yml`](file:///c:/projects/angular/.github/workflows/adev-preview-build.yml)<br>• [`.github/workflows/benchmark-compare.yml`](file:///c:/projects/angular/.github/workflows/benchmark-compare.yml) | Invoked via `angular/dev-infra/github-actions/bazel/configure-remote`:<br>• **`ci.yml`**: 8 jobs (`devtools`, `test`, `integration-tests`, `adev`, `vscode-ng-language-service`, `publish-snapshots`, `zone-js`, `adev-deploy`), with `secrets.RBE_TRUSTED_BUILDS_USER` passed in 6 of them.<br>• **`pr.yml`**: 6 jobs (`devtools`, `test`, `integration-tests`, `adev`, `vscode-ng-language-service`, `zone-js`); `test` also uploads `/tmp/rbe-grpc.log`.<br>• **`adev-preview-build.yml`**: `adev-build` job.<br>• **`benchmark-compare.yml`**: `benchmark-compare` job.<br>• Configured in [`.bazelrc`](file:///c:/projects/angular/.bazelrc#L126-L135): `projects/internal-200822/instances/primary_instance` (`--jobs=200`). |
| **Google Cloud Storage (GCS)** | • [`.github/workflows/ci.yml`](file:///c:/projects/angular/.github/workflows/ci.yml)<br>• [`.github/workflows/pr.yml`](file:///c:/projects/angular/.github/workflows/pr.yml)<br>• *(Referenced in `master_list` under `perf.yml`)* | • Explicitly configured in [`.bazelrc`](file:///c:/projects/angular/.bazelrc#L138):<br>  `build:remote-cache --remote_cache=https://storage.googleapis.com/angular-team-cache`<br>  Used by Bazel remote-cache setup steps (`Setup Bazel Remote Caching` in `test` and `integration-tests` in `ci.yml` and `pr.yml`).<br>• In `perf.yml`, telemetry storage/upload happens inside the external `@angular/ng-dev` package (`pnpm ng-dev perf workflows`), whose compiled source is not checked into this repo. |
| **Workload Identity Federation (WIF)** | • [`.github/workflows/perf.yml`](file:///c:/projects/angular/.github/workflows/perf.yml) (`Performance Tracking`) | • Job `workflow` uses `google-github-actions/auth@v3` (`id-token: write`) to authenticate GitHub OIDC tokens to:<br>  - `project_id: 'internal-200822'`<br>  - `workload_identity_provider: 'projects/823469418460/locations/global/workloadIdentityPools/measurables-tracking/providers/angular'`<br>  - `service_account: 'measures-uploader@internal-200822.iam.gserviceaccount.com'` |
| **Google BigQuery** | • *(Listed in `master_list` under `perf.yml`, **not** directly referenced in `.github/workflows/*.yml`)* | **Codebase Reality Check**: BigQuery does not appear anywhere in `.github/workflows/*.yml`, and `@google-cloud/bigquery` is not in [`pnpm-lock.yaml`](file:///c:/projects/angular/pnpm-lock.yaml). The only direct mention in the repo is an illustrative example in [`packages/benchpress/README.md`](file:///c:/projects/angular/packages/benchpress/README.md#L286). Meanwhile, `@angular/ng-dev` (invoked by `perf.yml`) declares `@google-cloud/spanner@8.0.0` in [`pnpm-lock.yaml`](file:///c:/projects/angular/pnpm-lock.yaml#L11866). *(Any BigQuery ingestion used by Google lives either inside external/private `dev-infra` code or downstream analytics pipelines inside `internal-200822`.)* |

---

## 2. Why Google Cloud RBE Is Not a Buyable Service

**Google Cloud RBE (`remotebuildexecution.googleapis.com`) is NOT a commercially buyable, self-service GCP product.**

- Google Cloud's hosted RBE remained an internal/early-preview service used primarily by Google projects (such as `internal-200822` for Angular and AOSP builds) and was never launched as a generally available (GA) self-service offering in the GCP Console or Marketplace.
- Although `roles/remotebuildexecution.*` IAM references exist in GCP documentation, an external enterprise **cannot purchase or enable** `remotebuildexecution.googleapis.com` in a standard GCP project.

---

## 3. What to Purchase & Which Subscriptions to Choose in Your Enterprise

GCP services (**Cloud Storage**, **BigQuery**, **WIF**) do **not** use fixed seat-based "SaaS subscriptions." You provision **one standard Google Cloud Platform (GCP) Billing Account** (Pay-As-You-Go or Enterprise Agreement) and select the appropriate billing tier/storage class per service:

### A. Workload Identity Federation (WIF)
- **What to purchase**: **Nothing ($0.00)**.
- **Details**: WIF is a free built-in feature of Google Cloud IAM. Enable the `iam.googleapis.com`, `sts.googleapis.com`, and `iamcredentials.googleapis.com` APIs inside your GCP project.

### B. Google Cloud Storage (GCS)
- **Tier / Class to Choose**: **Standard Storage Class** (Regional bucket in the same region as your CI/compute, e.g., `us-central1`).
  - *Avoid Nearline, Coldline, or Archive*: Bazel build caches have constant small reads/writes and short retention; colder storage classes penalize early deletion (30–365 day minimum durations) and charge per-GB retrieval fees.
- **Pricing Model**: Standard **Pay-As-You-Go** billing (includes an **Always Free tier** of **5 GB-month** US regional storage, 5,000 Class A ops, and 50,000 Class B ops/month).
  - Beyond free tier: ~$0.020/GB-month (US regional Standard), ~$0.005 per 1k Class A writes, ~$0.004 per 10k Class B reads, and ~$0.12/GB internet egress to external GitHub-hosted runners (**$0 egress** if CI/RBE workers run in the same GCP region).
- **Cost Control**: Configure an **Object Lifecycle Rule** to automatically delete cache objects older than 7–14 days.

### C. Google BigQuery *(Only if You Want SQL Analytics for `perf.yml`)*
- **Pricing Model to Choose**: **On-Demand Pricing (Pay-As-You-Go)** attached to a **paid GCP Billing Account**.
  - **Do NOT purchase BigQuery Editions** (`Standard` ~$0.04/slot-hour, `Enterprise`, or `Enterprise Plus`): Editions reserve dedicated slot capacity for continuous heavy enterprise BI and would drastically overcharge for small CI telemetry workloads.
  - **Do NOT rely on the unpaid "BigQuery Sandbox"**: Sandbox tables automatically expire after **60 days** and disallow streaming inserts.
- **Pricing / Free Allowance under On-Demand**:
  - **Always Free Tier**: **1 TiB of query data scanned/month free** + **10 GiB of storage/month free**.
  - Beyond free tier: **$6.25 per TiB scanned**, active storage ~$0.02/GiB/month, streaming inserts $0.05/GiB (or **$0** if using batch `bq load` jobs).
- **Note on `perf.yml`**: Because upstream `pnpm ng-dev perf workflows` targets Google's private `internal-200822` backend (and depends on `@google-cloud/spanner@8.0.0`), an enterprise using BigQuery should replace the upload step with a lightweight script writing benchmark JSON into your own BigQuery table via `bq load` or `@google-cloud/bigquery` (staying inside the $0/month Always Free Tier), or simply archive metrics as GitHub Actions Artifacts ($0, zero GCP required).

---

## 4. How to Set Up Bazel RBE in Your Enterprise

Because Bazel communicates over the open-source **Remote Execution API (REAPI v2)** protocol, you can replace `remotebuildexecution.googleapis.com` using any of three enterprise architectures:

| Option | What to Buy / Provision | Cost Model | Best For |
| :--- | :--- | :--- | :--- |
| **Option 1: Commercial Managed Bazel RBE**<br>*(Turnkey SaaS or Self-Hosted in your GCP VPC)* | Subscribe to a Bazel RBE vendor:<br>• **[BuildBuddy](https://www.buildbuddy.io/)** (Cloud or Enterprise Self-Hosted)<br>• **[EngFlow](https://www.engflow.com/)** (Managed or GCP Self-Hosted)<br>• **[Aspect Build](https://www.aspect.build/)** | Commercial usage-based / enterprise contract (BuildBuddy also offers a small free tier) | **Fastest enterprise setup** with managed RBE workers, Build Event UI, and vendor SLA without maintaining RBE infrastructure from scratch. |
| **Option 2: Self-Hosted Open-Source RBE on GCP (GKE)**<br>*(100% Inside Your GCP Project)* | Purchase standard GCP compute & storage:<br>• **Google Kubernetes Engine (GKE)**<br>• **Compute Engine Linux VMs** (`c2`/`c3`/`n2` worker pool)<br>• **GCS Standard Bucket** (cold CAS) + **SSD/Redis** (hot CAS)<br>Deploy **[Buildbarn](https://github.com/buildbarn)** (Apache-2.0) or **Buildfarm / NativeLink** | Standard GCP infrastructure cost only (**$0 software license fee**); zero GCS egress when workers & GCS share a region | **Enterprises prohibiting third-party SaaS** where all source code and build artifacts must stay strictly inside your private GCP VPC. |
| **Option 3: Remote Cache Only (`GCS + WIF`) + Larger Runners**<br>*(No RBE Cluster Needed)* | • **GCP Billing Account + GCS Standard Bucket** (`--config=remote-cache`) + **WIF**<br>• **GitHub Hosted Runners** (`ubuntu-latest` or paid `ubuntu-latest-8core` at $0.032/min) or self-hosted GCE runners | ~$5–$30/mo for GCS + GitHub runner cost ($0 on public repos for `ubuntu-latest`; $0.032/min for 8-core) | **Simplest architecture** — eliminates operating a Bazel RBE worker cluster while preserving shared build caching via GCS + WIF. |

---

## 5. Recommended Enterprise Blueprint (GCP + GitHub Actions)

1. **Create 1 GCP Project with a standard Pay-As-You-Go Billing Account**:
   - Enable APIs: `iam.googleapis.com`, `sts.googleapis.com`, `iamcredentials.googleapis.com`, `storage.googleapis.com`, and (if keeping `perf.yml` SQL analytics) `bigquery.googleapis.com` (On-Demand).
2. **Create a GCS Bucket (`Standard` class, single region, 14-day lifecycle expiry)** for Bazel remote caching (`--remote_cache=https://storage.googleapis.com/<your-enterprise-bazel-cache>`).
3. **Configure Workload Identity Federation (WIF)** ($0):
   - Create a Workload Identity Pool & GitHub OIDC provider restricted to your organization (`assertion.repository_owner == '<your-org>'`).
   - Grant the mapped Service Account `roles/storage.objectUser` on your cache bucket (and `roles/bigquery.dataEditor` + `roles/bigquery.jobUser` if using BigQuery).
   - Use `google-github-actions/auth@v3` in your workflows — it sets `GOOGLE_APPLICATION_CREDENTIALS`, which works directly with Bazel's `--google_default_credentials` flag already in [`.bazelrc`](file:///c:/projects/angular/.bazelrc#L141).
4. **Choose Execution Compute**:
   - Either deploy **BuildBuddy / EngFlow** or self-host **Buildbarn on GKE** and point `--remote_executor` and `--remote_cache` in [`.bazelrc`](file:///c:/projects/angular/.bazelrc#L128-L129) to your endpoint, **or** skip RBE workers and use **GCS Remote Cache + GitHub Runners** (or self-hosted GCE runners in the same GCP region).

---

## 6. Using BuildBuddy Instead of Google Cloud RBE: Do You Still Need BigQuery, GCS, or WIF?

**Short Answer:** If you use **BuildBuddy Cloud (Managed SaaS)**, you **do NOT need any of the three** (**no BigQuery, no Google Cloud Storage, and no Workload Identity Federation**) — unless you separately choose to keep `perf.yml` pushing framework bundle-size metrics into your own GCP project.

The exact requirement depends on whether you choose **BuildBuddy Cloud (SaaS)** or **BuildBuddy Enterprise (Self-Hosted inside your own GCP VPC)**:

| GCP Service | If Using **BuildBuddy Cloud (SaaS)** | If Using **BuildBuddy Enterprise (Self-Hosted on GCP)** | Why? |
| :--- | :---: | :---: | :--- |
| **Google Cloud Storage (GCS)** | **No** | **Yes** *(or AWS S3 / disk)* | • **Cloud**: BuildBuddy manages all CAS/Action Cache and build artifact storage internally.<br>• **Self-Hosted**: BuildBuddy stores invocation history and larger cache blocks in an object store configured in `config.yaml` (`storage.gcs.bucket`), paired with local SSDs (Pebble) for hot cache. |
| **Workload Identity Federation (WIF)** | **No** | **No** *(in GitHub Actions)* | • BuildBuddy authenticates Bazel CI requests via an **API key header** (`x-buildbuddy-api-key`) stored as a standard GitHub secret (or mTLS/OIDC), not GCP STS tokens.<br>• *(Inside GKE, self-hosted BuildBuddy pods can use standard GKE IAM / node identity to read/write the GCS bucket — no GitHub OIDC WIF needed in workflows.)* |
| **Google BigQuery** | **No** | **No** | • BuildBuddy does not use BigQuery. It includes a built-in **Build Event UI (BES), timing profiles, cache analytics, and API** out of the box.<br>• As verified in [`perf.yml`](file:///c:/projects/angular/.github/workflows/perf.yml) and [`pnpm-lock.yaml`](file:///c:/projects/angular/pnpm-lock.yaml), BigQuery is not directly invoked by upstream `.github/workflows/*.yml` anyway. |

### Nuance Regarding `perf.yml`
BuildBuddy replaces **Google Cloud RBE + Bazel Remote Cache** (`ci.yml`, `pr.yml`, `adev-preview-build.yml`, and `benchmark-compare.yml`). It does **not** replace the custom GCP upload inside [`perf.yml`](file:///c:/projects/angular/.github/workflows/perf.yml) (`pnpm ng-dev perf workflows`), which uses WIF (`google-github-actions/auth@v3`) to upload Angular bundle-size/benchmark metrics to Google's private `internal-200822` project:

1. **Recommended ($0 GCP cost, zero GCP accounts needed):** Replace the GCP upload in `perf.yml` with **GitHub Actions Artifacts + `$GITHUB_STEP_SUMMARY`** (or query build timings from BuildBuddy's UI/API). Then **BigQuery, GCS, and WIF are 100% unnecessary**.
2. **Only if your enterprise specifically mandates a custom BigQuery SQL dashboard** for `perf.yml` metrics: Keep **WIF ($0)** + **BigQuery On-Demand (Always Free tier)** solely for that one telemetry job — still completely separate from BuildBuddy.

### Summary of `.bazelrc` Changes with BuildBuddy
Instead of Angular's upstream GCP RBE/GCS configuration in [`.bazelrc`](file:///c:/projects/angular/.bazelrc#L126-L141) (`remotebuildexecution.googleapis.com` and `--google_default_credentials`), your enterprise simply configures:
- `--remote_executor=grpcs://<your-buildbuddy-endpoint>`
- `--remote_cache=grpcs://<your-buildbuddy-endpoint>`
- `--bes_backend=grpcs://<your-buildbuddy-endpoint>`
- `--remote_header=x-buildbuddy-api-key=<SECRET>` and `--bes_header=x-buildbuddy-api-key=<SECRET>`

With **BuildBuddy Cloud**, that single vendor subscription eliminates **Google Cloud RBE, Google Cloud Storage, Workload Identity Federation, and BigQuery** completely.
