# Google Cloud Monitoring Audit for Angular Workflows

> **Evaluated Service**: Google Cloud Monitoring (`https://cloud.google.com/monitoring`)  
> **Reference Baseline**: Upstream `angular/angular` at commit `58e1d9a23c` and current `HEAD`  
> **Verdict**: **Not used in Angular workflows ($0.00 purchase needed)**

---

## 1. Where Google Cloud Monitoring Is Used in Angular

**Nowhere in the Angular codebase or `.github/workflows/*.yml`.**

An exhaustive search across the entire repository (at both upstream commit `58e1d9a23c` and `HEAD`) confirms **zero references** to `cloud.google.com/monitoring`, `monitoring.googleapis.com`, `@google-cloud/monitoring`, or `stackdriver`.

* The only `"monitoring"` dependency in [`pnpm-lock.yaml`](file:///c:/projects/angular/pnpm-lock.yaml#L1472) is `@algolia/monitoring@1.59.0` (an internal sub-dependency of `algoliasearch`, unrelated to Google Cloud Monitoring).

### Why Did It Appear in Earlier Notes / Spreadsheets?
* In [`workflow-fixes/angular_pipeline_result.xlsx`](file:///c:/projects/angular/workflow-fixes/angular_pipeline_result.xlsx) (`angular` sheet, Row 12 for [`perf.yml`](file:///c:/projects/angular/.github/workflows/perf.yml)), an earlier summary cell informally grouped `"GCP BigQuery / Cloud Storage / Cloud Monitoring (internal-200822)"`, and [`workflow-fixes/data1.xlsx`](file:///c:/projects/angular/workflow-fixes/data1.xlsx) (`master_list` Row 434) used the generic phrase `"performance monitoring"`.
* In reality, [`perf.yml`](file:///c:/projects/angular/.github/workflows/perf.yml) tracks framework performance benchmarks via `pnpm ng-dev perf workflows` (where [`pnpm-lock.yaml`](file:///c:/projects/angular/pnpm-lock.yaml#L11866) shows `@angular/ng-dev` depends on `@google-cloud/spanner@8.0.0`, **not** Cloud Monitoring).

---

## 2. What Should You Buy for Your Enterprise?

| Scenario | Purchase / Subscription Required | Pricing / Free Tier Details |
| :--- | :--- | :--- |
| **Running Angular CI/CD Workflows & Releases** *(with GitHub Actions, BuildBuddy, or GCS cache)* | **Nothing ($0.00)** | Angular's workflows do not use Google Cloud Monitoring. Do **not** buy or enable anything for it. |
| **Self-Hosting Custom GCP Infra** *(e.g., GKE + Buildbarn RBE cluster)* | **No separate subscription** *(Included in standard Pay-As-You-Go GCP Billing Account)* | • **Native GCP system metrics** (GKE node CPU, memory, disk, GCS metrics): **$0 / Free**.<br>• **Chargeable custom / external / log-based metrics**: First **150 MiB/month free** per billing account; then **$0.2580 per MiB** (150–100,000 MiB tier). |
| **Using BuildBuddy Cloud or GitHub Actions** | **Nothing ($0.00)** | BuildBuddy provides its own build/cache monitoring UI, and GitHub Actions provides native workflow run monitoring out of the box. |
