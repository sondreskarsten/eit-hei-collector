"""EIT-HEI collector orchestrating WP REST API pagination and GCS upload.

Downloads all projects and taxonomy terms from the EIT HEI Initiative
WordPress site via its REST API.  Stores everything — all projects,
all partners, all countries — not just Norwegian.  Filtering is the
parser's job.

For each project, the partner_institution taxonomy IDs are stored
inline.  A separate partner_institution.jsonl maps term IDs to names.
The parser resolves names → Norwegian orgnrs.
"""

from datetime import datetime, timezone


TAXONOMIES = [
    "partner_institution",
    "call_year",
    "country",
    "kic_partner",
    "org_type",
]


def collect_all(client, store, snapshot_date):
    """Download all projects and taxonomies for one snapshot date.

    Args:
        client: :class:`~client.EitHeiClient` instance.
        store: :class:`~storage.GCSStore` instance.
        snapshot_date: ``yyyy-mm-dd`` string.

    Returns:
        Manifest dict.
    """
    if store.manifest_exists(snapshot_date):
        print(f"  Manifest exists for {snapshot_date}, skipping", flush=True)
        return None

    fetched_at = datetime.now(timezone.utc).isoformat()

    projects = client.get_all_projects()
    store.upload_jsonl(snapshot_date, "projects.jsonl", projects)
    print(f"  Uploaded {len(projects)} projects", flush=True)

    taxonomy_counts = {}
    for tax in TAXONOMIES:
        terms = client.get_all_taxonomy_terms(tax)
        store.upload_jsonl(snapshot_date, f"{tax}.jsonl", terms)
        taxonomy_counts[tax] = len(terms)

    manifest = {
        "snapshot_date": snapshot_date,
        "fetched_at_utc": fetched_at,
        "projects": len(projects),
        "taxonomies": taxonomy_counts,
        "source": "https://eit-hei.eu/wp-json/wp/v2/",
    }

    store.upload_manifest(snapshot_date, manifest)
    print(f"  Manifest written: {len(projects)} projects, {sum(taxonomy_counts.values())} taxonomy terms", flush=True)

    return manifest
