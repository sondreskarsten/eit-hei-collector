"""Pipeline entrypoint for the EIT-HEI collector.

Downloads all projects and taxonomy terms from the EIT HEI Initiative
WordPress REST API and stores as versioned JSONL snapshots on GCS.

Modes:

* ``daily`` — download all for today.  Idempotent.
* ``backfill`` — download for a specific date.
* ``check`` — print project count without writing.

Environment variables:

======================== ============================================= =================
Variable                 Description                                   Default
======================== ============================================= =================
GCS_BUCKET               GCS bucket                                    sondre_brreg_data
GCS_PREFIX               Path prefix                                   eit_hei
RUN_MODE                 ``daily``, ``backfill``, or ``check``         daily
SNAPSHOT_DATE            Date for backfill mode                        today
======================== ============================================= =================
"""

import os
import sys
from datetime import date

from client import EitHeiClient
from storage import GCSStore
from collector import collect_all

GCS_BUCKET = os.environ.get("GCS_BUCKET", "sondre_brreg_data")
GCS_PREFIX = os.environ.get("GCS_PREFIX", "eit_hei")
RUN_MODE = os.environ.get("RUN_MODE", "daily")
SNAPSHOT_DATE = os.environ.get("SNAPSHOT_DATE", date.today().isoformat())


def main():
    print(f"{'='*60}", flush=True)
    print(f"  eit-hei-collector — mode: {RUN_MODE}", flush=True)
    print(f"  {date.today().isoformat()}", flush=True)
    print(f"  GCS: gs://{GCS_BUCKET}/{GCS_PREFIX}/", flush=True)
    print(f"{'='*60}", flush=True)

    client = EitHeiClient(delay=1.0)
    store = GCSStore(GCS_BUCKET, GCS_PREFIX)

    if RUN_MODE == "daily":
        snapshot = date.today().isoformat()
        collect_all(client, store, snapshot)

    elif RUN_MODE == "backfill":
        collect_all(client, store, SNAPSHOT_DATE)

    elif RUN_MODE == "check":
        projects = client.get_all_projects()
        print(f"  Projects: {len(projects)}", flush=True)
        for p in projects[:5]:
            acf = p.get("acf", {})
            print(f"    {p['slug']}: partners={len(p.get('partner_institution', []))}, lead={acf.get('lead_partner')}", flush=True)

    else:
        print(f"  Unknown RUN_MODE: {RUN_MODE}", flush=True)
        sys.exit(1)

    print(f"\n  Requests: {client.request_count}", flush=True)


if __name__ == "__main__":
    main()
