# P1 cloud migration and acceptance runbook

Status: implementation, not a claim of deployment or ten-minute reliability.
The Google Cloud project, billing approval, IAM access, secret versions, and
Healthchecks monitor must be supplied before deployment. No cloud resources or
monitoring accounts are created just by committing these files.

## Design

- A **private Cloud Run HTTP service** runs the existing deterministic Python
  watcher. This deliberately refines the original background-job proposal:
  the scheduler receives HTTP 200 only after the scan, durable state writes,
  required notification submissions, and heartbeat acknowledgement succeed.
- Cloud Scheduler calls `/run` every ten minutes in UTC using OIDC and a
  dedicated service account with only service-level `roles/run.invoker`.
- Firestore database `imax-watcher`, document `watcher_states/imax`, contains
  persistent baselines, queued notifications, recent run evidence, and a
  transactional lease. No service-account keys are created.
- ntfy retains the existing topic. A successful HTTP publish means ntfy
  accepted the alert; it does **not** prove delivery to a phone.
- Healthchecks.io is independent of Google Cloud. Configure a simple
  **10-minute period + 5-minute grace**, with email notifications independent
  of ntfy. Only a fully successful automatic check sends a success ping.
- `/health` is readiness, not scan health. `/check` is a real **manual** scan;
  it saves state and may send seat alerts, but cannot send health heartbeats
  or count as scheduler proof. `watcher.py --test-notify` is notification-only.
- A 270-second scan budget includes pacing/retries, Cloud Run timeout is
  330 seconds, and the lease expires after 360 seconds. Contention, backoff,
  parsing, storage, notification, and heartbeat failures are non-success.

### What a successful observation does and does not mean

The site can return today's listings when a requested future date is not in
the advertised calendar. Such a result is recorded as `date_not_published`.
It is not a seat check or proof that the movie is sold out. An advertised date
that unexpectedly returns a different date is an error. Missing/changed seat
markup is also an error, not zero seats.

Polling remains bounded: up to five discovery pages and eight selected seat
maps per movie per run. It does **not** poll every seat of every performance
every ten minutes. Each selected map has its own `seat_checked_at` timestamp.
New-showtime overflow stays queued. The initial baseline is incremental; until
both baselines finish, the overall result is `initializing`/failed, not healthy.
Importing the existing baseline avoids that startup delay.

Keep the site's request pacing and 403/429 backoff. Do not bypass access
controls, CAPTCHAs, or retry restrictions. Google Cloud egress may be treated
differently from a local machine; live deployment validation is mandatory.

### Delivery semantics

Observations and the alert outbox are saved before publishing. Each successful
publish acknowledgement removes its queue entry durably. Normal reruns do not
duplicate the alert. A crash after ntfy accepts but before the acknowledgement
is saved can produce a duplicate: delivery is **at least once**, not exactly
once. Unsent alerts expire after 15 minutes to avoid presenting old inventory
as fresh; expiration records an error. A later check must re-observe inventory.
Queued alerts are prioritized for a new seat-map observation on retries. If
their specific seats have gone, the old alert is cancelled. A failed or stale
recheck cannot publish an old "available" result.

## Prerequisites and costs

Use an existing, preferably dedicated, billing-enabled Google Cloud project.
Approve an estimated monthly budget before provisioning. Runtime is metered:
144 daily runs at 2.5 minutes is approximately **180 instance-hours per 30-day
month**, plus retries and startup. Check current regional Cloud Run, Scheduler,
Firestore, build, registry, and monitoring pricing; do not assume it is free.
Billing-budget alerts are **not** hard spending caps.

The deployer needs permission to enable the specified APIs, provision these
resources, build/push the image, and assign the listed IAM roles. Runtime has
Firestore user access and access only to the two named secrets; Scheduler only
invokes this service. Do not grant allUsers or allAuthenticatedUsers access.

Authenticate through your normal secure Google Cloud login/Cloud Shell.
Terraform and the seed command use Application Default Credentials. Never
paste access tokens, ntfy topics, or heartbeat URLs into chat or public git.

## Deployment (operator-reviewed, no automatic billing changes)

From a clean checkout, use Terraform >=1.6 and <2, gcloud, and Python 3.12+.
Retain Terraform state securely; it is gitignored. In a team, configure a
private remote Terraform backend with locking before deployment.

1. Set your **approved existing project ID**, authenticate, and inspect the plan:

   ```bash
   export PROJECT_ID='YOUR_APPROVED_PROJECT_ID'
   export REGION='us-central1'
   gcloud config set project "$PROJECT_ID"
   terraform -chdir=infra init
   terraform -chdir=infra plan -var="project_id=$PROJECT_ID"
   terraform -chdir=infra apply -var="project_id=$PROJECT_ID"
   ```

   With `image` empty, this provisions prerequisites only: API enablement,
   registry, a named Firestore database, service accounts, IAM, and secret
   containers. No running service or schedule exists yet. Do not later omit
   `image` once a service has been deployed; that would propose its removal.

2. Create the Healthchecks check (10-minute period, 5-minute grace) and select
   the verified email destination in that service. Use its notification test
   to verify email delivery; do not fabricate production success pings.
   Securely add secret versions through Google Secret Manager's console:

   - `imax-ntfy-topic`: the existing ntfy topic.
   - `imax-healthchecks-ping`: the check's `https://hc-ping.com/<uuid>` URL.

   Terraform creates metadata only; secret values are never in the Terraform
   variables/state or repository. Service redeployment is needed after rotating
   a secret because these are environment-variable secrets.

3. Build, resolve the immutable digest, and deploy with the scheduler paused:

   ```bash
   export IMAGE_REPO="$REGION-docker.pkg.dev/$PROJECT_ID/imax-watcher/watcher"
   export IMAGE_TAG="$IMAGE_REPO:$(git rev-parse --short HEAD)"
   gcloud builds submit --tag "$IMAGE_TAG" .
   export IMAGE_DIGEST="$(gcloud artifacts docker images describe "$IMAGE_TAG" --format='value(image_summary.digest)')"
   export IMAGE="$IMAGE_REPO@$IMAGE_DIGEST"
   terraform -chdir=infra plan -var="project_id=$PROJECT_ID" -var="image=$IMAGE"
   terraform -chdir=infra apply -var="project_id=$PROJECT_ID" -var="image=$IMAGE"
   ```

4. **Cutover maintenance window:** set GitHub repository variable
   `CLOUD_WATCHER_ACTIVE=true`, then let any already-running legacy scan finish.
   This disables normal legacy scheduled/manual scans but preserves the
   notification-only test. Refresh the checkout's `state.json` from `main`
   before seeding, so acknowledged alerts/backoff are not lost. Keep the cloud
   scheduler paused while importing. Do not run both independent state stores
   in production simultaneously: they cannot deduplicate each other's alerts.

   ```bash
   git pull --ff-only
   python3 -m venv .venv-deploy
   .venv-deploy/bin/pip install -r requirements.txt
   GCP_PROJECT_ID="$PROJECT_ID" .venv-deploy/bin/python cloud_service.py --seed-state state.json
   ```

   The import refuses an existing state document and preserves any backoff.
   It never creates fresh health timestamps or sends a heartbeat.

5. Perform an IAM-authenticated POST to the service's `/check` route using
   your normal Google Cloud tooling and operator identity. The operator must
   have service-level invocation permission. This route is **manual**; it
   cannot prove cadence or activate the health monitor. Inspect the JSON:
   both configured movies must have valid observations and `status=success`.
   Diagnose any 403/429, schema, date, credential, or state failure before
   continuing. Do not test by spoofing Scheduler headers.

6. Review and activate the real schedule:

   ```bash
   terraform -chdir=infra plan -var="project_id=$PROJECT_ID" -var="image=$IMAGE" -var='scheduler_paused=false'
   terraform -chdir=infra apply -var="project_id=$PROJECT_ID" -var="image=$IMAGE" -var='scheduler_paused=false'
   ```

   Wait for the next natural ten-minute slot. Verify a real successful run and
   that Healthchecks becomes Up. A newly created monitor may remain New before
   its first success; **do not leave rollout unattended before that first
   automatic success**. If startup never succeeds, rollout is failed.

## Acceptance: P1 stays open until these pass live

1. Send one clearly labelled ntfy test and confirm it arrives on the phone.
2. After the first automatic success, pause Cloud Scheduler. Confirm the
   independent missing-heartbeat email after the 10+5-minute threshold and
   record its time. Resume and verify recovery. Exclude this deliberate failure
   interval from the subsequent cadence measurement.
3. Unit tests inject site errors, parsing failures, storage/ntfy/heartbeat
   failures, overlaps, and duplicates. Repeat representative failure tests
   against a **separate staging service/monitor**, not live seat inventory.
4. Observe a full subsequent **24 hours**, with 144 distinct automatic slots,
   every movie validated, no start >2 minutes late, no completion >5 minutes
   after its slot, and no successful-completion gap >15 minutes. These are
   acceptance targets, not provider guarantees.
5. Export Cloud Run logs from that exact interval. Example (replace START/END):

   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="imax-watcher" AND jsonPayload.event="check_completed" AND timestamp>="START" AND timestamp<"END"' --project="$PROJECT_ID" --format=json --limit=1000
   python3 verify_cadence.py EXPORTED_LOGS.json --start START --hours 24
   ```

   Save the first command's JSON output as `EXPORTED_LOGS.json`. Allow five
   minutes beyond the last scheduled slot for completion. The verifier ignores
   manual runs and retries cannot fill missing slots or inflate counts.
   Cross-check Cloud Scheduler execution logs for the same interval and Cloud
   Audit Logs for `google.cloud.scheduler.v1.CloudScheduler.RunJob`. If anyone
   forced Scheduler runs, exclude those slots or choose a clean interval;
   application headers alone cannot prove that an operator never forced a run.
   Application logs are evidence, not cryptographic attestation.

If cloud rollout fails before acceptance, keep the P1 open. To roll back,
pause the cloud scheduler and wait for its active request/lease to finish
before clearing `CLOUD_WATCHER_ACTIVE`. Reconcile/export cloud state into the
legacy format first if cloud checks already sent alerts; otherwise rollback
can resend alerts. Do not destroy the Firestore database or overwrite state.

## Local checks

```bash
python3 -m unittest discover -v
python3 watcher.py --dry-run --max-seconds 270
terraform -chdir=infra fmt -check
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
docker build -t imax-watcher:test .
```

The dry run contacts Cinemark but changes no state, sends no notification, and
cannot send a heartbeat. Unit tests use synthetic responses and fake state
storage. Passing them is **not** proof of live cloud credentials, Firestore
transactions across real instances, website access from cloud egress, phone
delivery, watchdog-email delivery, or scheduled execution cadence.

References: [Cloud Run + Scheduler](https://docs.cloud.google.com/run/docs/triggering/using-scheduler),
[Scheduler request headers](https://docs.cloud.google.com/scheduler/docs/reference/rest/v1/projects.locations.jobs),
[Healthchecks semantics](https://healthchecks.io/docs/).
