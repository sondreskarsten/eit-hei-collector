"""GCS storage operations for the EIT-HEI collector.

Manages GCS path hierarchy::

    gs://{bucket}/{prefix}/
    └── raw/{snapshot_date}/
        ├── projects.jsonl
        ├── partner_institution.jsonl
        ├── call_year.jsonl
        ├── country.jsonl
        ├── kic_partner.jsonl
        ├── org_type.jsonl
        └── manifest.json
"""

import json

from google.cloud import storage as gcs_lib


class GCSStore:

    def __init__(self, bucket_name, prefix="eit_hei"):
        self._client = gcs_lib.Client()
        self.bucket = self._client.bucket(bucket_name)
        self.prefix = prefix.rstrip("/")

    def raw_path(self, snapshot_date, filename):
        return f"{self.prefix}/raw/{snapshot_date}/{filename}"

    def manifest_path(self, snapshot_date):
        return f"{self.prefix}/raw/{snapshot_date}/manifest.json"

    def upload_jsonl(self, snapshot_date, filename, records):
        """Upload a list of dicts as JSONL.

        Args:
            snapshot_date: ``yyyy-mm-dd`` string.
            filename: e.g., ``"projects.jsonl"``.
            records: List of dicts.

        Returns:
            GCS blob path.
        """
        lines = [json.dumps(r, ensure_ascii=False) for r in records]
        content = "\n".join(lines) + "\n"
        path = self.raw_path(snapshot_date, filename)
        blob = self.bucket.blob(path)
        blob.upload_from_string(content, content_type="application/jsonl")
        return path

    def upload_manifest(self, snapshot_date, manifest_dict):
        path = self.manifest_path(snapshot_date)
        blob = self.bucket.blob(path)
        blob.upload_from_string(
            json.dumps(manifest_dict, indent=2, ensure_ascii=False),
            content_type="application/json",
        )

    def manifest_exists(self, snapshot_date):
        blob = self.bucket.blob(self.manifest_path(snapshot_date))
        return blob.exists()

    def list_snapshot_dates(self):
        prefix = f"{self.prefix}/raw/"
        dates = set()
        iterator = self.bucket.list_blobs(prefix=prefix, delimiter="/")
        for page in iterator.pages:
            for p in page.prefixes:
                date_part = p.rstrip("/").split("/")[-1]
                if len(date_part) == 10:
                    dates.add(date_part)
        return sorted(dates)
