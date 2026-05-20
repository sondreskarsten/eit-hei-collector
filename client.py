"""EIT HEI Initiative WordPress REST API client.

The EIT HEI website at eit-hei.eu runs WordPress with custom post types
and taxonomies exposed via the WP REST API at ``/wp-json/wp/v2/``.

Key endpoints:

* ``/wp/v2/project`` — 111 funded projects with ACF fields (budget,
  lead_partner, summary, objectives, phase amounts, timeline).
* ``/wp/v2/partner_institution`` — 1,342 taxonomy terms (one per
  consortium partner across all projects).
* ``/wp/v2/call_year`` — call years (2021, 2022, 2023, 2024, 2025).
* ``/wp/v2/country`` — country taxonomy.
* ``/wp/v2/kic_partner`` — KIC partner taxonomy.
* ``/wp/v2/org_type`` — organisation type taxonomy.

No authentication required.  No Playwright or headless browser needed.
"""

import time
import requests


BASE = "https://eit-hei.eu/wp-json/wp/v2"


class EitHeiClient:
    """WordPress REST API client for EIT HEI Initiative.

    Args:
        delay: Seconds between requests.  Default ``1.0``.
    """

    def __init__(self, delay=1.0):
        self.delay = delay
        self.request_count = 0
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "Registrum/1.0 (sondreskarsten@gmail.com; Norwegian public register monitoring)"

    def _get_json(self, url, params=None):
        self.request_count += 1
        r = self._session.get(url, params=params, timeout=30)
        time.sleep(self.delay)
        r.raise_for_status()
        total = int(r.headers.get("X-WP-Total", 0))
        total_pages = int(r.headers.get("X-WP-TotalPages", 0))
        return r.json(), total, total_pages

    def get_all_projects(self):
        """Paginate through all projects.

        Returns:
            List of project dicts with ACF fields.
        """
        projects = []
        page = 1
        while True:
            data, total, total_pages = self._get_json(
                f"{BASE}/project",
                params={"per_page": 100, "page": page},
            )
            projects.extend(data)
            print(f"  Projects page {page}/{total_pages}: {len(data)} items (total={total})", flush=True)
            if page >= total_pages:
                break
            page += 1
        return projects

    def get_all_taxonomy_terms(self, taxonomy):
        """Paginate through all terms of a taxonomy.

        Args:
            taxonomy: Taxonomy slug (e.g., ``"partner_institution"``).

        Returns:
            List of taxonomy term dicts.
        """
        terms = []
        page = 1
        while True:
            data, total, total_pages = self._get_json(
                f"{BASE}/{taxonomy}",
                params={"per_page": 100, "page": page},
            )
            terms.extend(data)
            if page >= total_pages:
                break
            page += 1
        print(f"  {taxonomy}: {len(terms)} terms (total={total})", flush=True)
        return terms

    def get_taxonomy_terms_by_ids(self, taxonomy, ids):
        """Fetch specific taxonomy terms by their IDs.

        Args:
            taxonomy: Taxonomy slug.
            ids: List of integer term IDs.

        Returns:
            List of taxonomy term dicts.
        """
        if not ids:
            return []
        id_str = ",".join(str(i) for i in ids)
        data, _, _ = self._get_json(
            f"{BASE}/{taxonomy}",
            params={"include": id_str, "per_page": 100},
        )
        return data
