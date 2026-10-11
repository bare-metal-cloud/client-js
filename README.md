# bare-metal-cloud/client-js

TypeScript/JavaScript SDK client for the Bare Metal Cloud API. Generated from
the platform's OpenAPI specification, not written by hand — every endpoint,
request body and response model in this repository mirrors the API that the
control plane actually serves.

Two audiences:

- **External developers** building JavaScript/TypeScript integrations
  against the BMC platform API (browser and Node 18+ — the client uses the
  native `fetch` API).
- **BMC's own frontend**, which consumes the same client so the dashboard
  and third-party integrations share one typed surface. Today the frontend
  hand-writes per-domain API modules in `src/lib/*Api.ts`; this package is
  the path to replacing those with one generated source of truth.

Status: early scaffold, generated from `bare-metal-cloud/backend` at tag
**v1.2.0**. The client regenerates automatically whenever the backend
publishes a new release tag; the publishing target (npm registry) is still
being decided.

## Install

```bash
npm install @bare-metal-cloud/client
```

(Once the first version is published; until then, install from a git tag.)

## Quick start

```typescript
import { Configuration, DefaultApi } from "@bare-metal-cloud/client";

const config = new Configuration({
  basePath: "https://api.example.com",
  accessToken: "YOUR_API_TOKEN", // platform API token
});

const api = new DefaultApi(config);

// Example call — see docs/ for the full endpoint list.
// const result = await api.someEndpoint();
```

## How this repository works

- `spec/swagger.json` is the normalized snapshot of the API (Swagger 2.0)
  that the current generated code was built from. It is **not edited by
  hand** here; regeneration overwrites it.
- `spec/source-state.json` records which backend release tag the client
  currently mirrors, and the hash of the spec at that tag.
- `scripts/generate.sh` normalizes the snapshot and regenerates the client
  using `openapi-generator` in Docker (no local Java needed).
- `.github/workflows/generate.yml` keeps the client in lockstep with
  released backend API versions. Every hour (and on any
  `repository_dispatch` of type `api-spec-updated`, e.g. the backend's own
  notify workflow pinging at tag time) it compares the latest `v*` tag on
  `bare-metal-cloud/backend` against `spec/source-state.json`; when the tag
  or its spec moved, it fetches the spec **at that tag**, regenerates, and
  opens a pull request. The tag contract means the SDK always mirrors a
  released backend, not a moving branch.
- Generated code is committed under `src/`. Consumers get a reviewable
  release PR per API change, and git history documents every API delta.
- `README.md` and the CI workflows are hand-maintained; the generator is
  told to leave them alone via `.openapi-generator-ignore`.

## Regenerating locally

```bash
scripts/generate.sh
git diff   # review the API delta
```

`scripts/generate.sh` requires Docker and regenerates from the committed
snapshot. CI uses the same generator image, so local and CI output are
identical.

## Setup for the regeneration workflow

One repository secret, `BMC_BACKEND_SPEC_TOKEN`: a fine-grained personal
access token with **Contents: read** on `bare-metal-cloud/backend`. Without
it the tag-watch job skips (it cannot read the private backend repo).

## Versioning and publishing

npm packages publish from a git tag. Publishing is **disabled until the
registry decision is made** (npmjs vs. a self-hosted registry — the org has
a stated direction of leaving GitHub, so the publish step is kept
registry-agnostic on purpose). Until then, consumers install from a git tag:

```bash
npm install github:bare-metal-cloud/client-js#v0.1.0
```

## Visibility

Private for now (ruled 2026-10-11). The spec covers the **entire** API
surface, including internal and admin endpoints — if this repository ever
goes public, first decide whether to filter the spec down to
customer-facing endpoints (the generation pipeline would drop non-public
paths). Flipping visibility is a one-command change when that day comes.

## Known spec quirks handled by the pipeline

`scripts/normalize-spec.py` papers over three swag (backend annotation
generator) defects; each becomes a no-op once the backend annotations are
fixed upstream:

1. Eight operations ship no `responses` section — backfilled as untyped 200.
2. The k8s-watch wildcard route declares `{proxyPath}` without defining it —
   backfilled as a required string path parameter.
3. No operation carries an `operationId` — all are assigned deterministic
   names (`postOrgsOrg_idVaultRotatePassword`-style), and the two operations
   tagged `vault` **and** `org` are trimmed to their first tag so types are
   not emitted twice.

## License

Apache-2.0 (matches the org's convention for developer-facing repositories).
