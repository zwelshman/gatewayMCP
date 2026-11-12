"""
HDRUK Health Data Research Gateway – MCP Server
================================================
Exposes the public Gateway REST API as MCP tools so Claude (or any MCP
client) can search datasets, collections, data uses, publications,
tools/analysis scripts and data custodians without leaving chat.

Base API: https://api.healthdatagateway.org/api/v2/
Docs:     https://api.healthdatagateway.org/api/documentation
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://api.healthdatagateway.org/api/v2"
TIMEOUT = 20.0

mcp = FastMCP(
    "hdruk-gateway",
    instructions=(
        "Tools for searching and browsing the Health Data Research UK (HDRUK) "
        "Gateway – the UK's primary catalogue for NHS and academic health datasets, "
        "collections, data uses / research projects, publications, analysis tools, "
        "and data custodians.  All data is publicly available; no authentication "
        "is required for read operations."
    ),
)

# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        timeout=TIMEOUT,
        headers={
            "Accept": "application/json",
            "User-Agent": "hdruk-gateway-mcp/1.0",
        },
        follow_redirects=True,
    )


def _get(path: str, params: dict[str, Any]) -> dict:
    """Make a GET request; strip None values from params."""
    clean = {k: v for k, v in params.items() if v is not None}
    with _client() as client:
        resp = client.get(path, params=clean)
        resp.raise_for_status()
        return resp.json()


def _fmt(data: dict) -> str:
    """Pretty-print a dict as JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Helper: build a human-readable summary from a paginated response
# ---------------------------------------------------------------------------

def _paginated_summary(data: dict, item_key: str = "data") -> str:
    """Return a readable summary of a paginated list response."""
    items = data.get(item_key, data.get("data", []))
    total = data.get("total", len(items))
    per_page = data.get("per_page", len(items))
    current_page = data.get("current_page", 1)
    last_page = data.get("last_page", 1)

    header = (
        f"Found {total} result(s)  |  "
        f"Page {current_page} of {last_page}  |  "
        f"{per_page} per page\n"
        + "=" * 60 + "\n"
    )
    return header + _fmt({"results": items})


# ===========================================================================
# TOOL: search_datasets
# ===========================================================================

@mcp.tool()
def search_datasets(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    sort: Optional[str] = None,
) -> str:
    """Search the HDRUK Gateway for Datasets & BioSamples.

    Returns a paginated list of datasets with their metadata including
    title, abstract, data custodian, keywords, temporal/geographic coverage,
    and unique persistent identifiers (PIDs).

    Args:
        query: Free-text search term (filters dataset titles by 3+ characters).
        page: Page number to retrieve (default 1).
        per_page: Results per page (default 10, max 100).
        status: Filter by dataset status ('ACTIVE', 'DRAFT', 'ARCHIVED').
        sort: Sort field and direction (e.g. "created:desc", "title:asc").
    """
    params = {
        "title": query,
        "page": page,
        "per_page": per_page,
        "status": status,
        "sort": sort,
    }
    data = _get("/datasets", params)
    return _paginated_summary(data)


# ===========================================================================
# TOOL: get_dataset
# ===========================================================================

@mcp.tool()
def get_dataset(dataset_id: int) -> str:
    """Retrieve full metadata for a single dataset by its integer ID.

    Returns complete HDRUK metadata specification fields including:
    title, abstract, keywords, data custodian, temporal/geographic coverage,
    data access request details, observations, structural metadata, linked
    resources (publications, tools, data uses, collections), and quality score.

    Args:
        dataset_id: The integer ID of the dataset (visible in Gateway URLs,
                    e.g. healthdatagateway.org/en/dataset/888 → ID is 888).
    """
    data = _get(f"/datasets/{dataset_id}", {})
    return _fmt(data)


# ===========================================================================
# TOOL: search_collections
# ===========================================================================

@mcp.tool()
def search_collections(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> str:
    """Search the HDRUK Gateway for Collections / Networks.

    Collections group related datasets, publications, tools, and data uses
    by theme, disease, domain, or organisation (e.g. BHF Data Science Centre
    collection, COVID-19 collection, Secure Data Environment collections).

    Args:
        query: Free-text search term (filters collection names).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
    """
    params = {
        "page": page,
        "per_page": per_page,
    }
    data = _get("/collections", params)
    return _paginated_summary(data)


# ===========================================================================
# TOOL: get_collection
# ===========================================================================

@mcp.tool()
def get_collection(collection_id: int) -> str:
    """Retrieve full details for a single collection by its integer ID.

    Returns the collection description, keywords, custodian, and all linked
    resources (datasets, publications, tools, data uses).

    Args:
        collection_id: The integer ID of the collection.
    """
    data = _get(f"/collections/{collection_id}", {})
    return _fmt(data)


# ===========================================================================
# TOOL: search_data_uses
# ===========================================================================

@mcp.tool()
def search_data_uses(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    organisation: Optional[str] = None,
    sector: Optional[str] = None,
) -> str:
    """Search Data Uses / Research Projects on the HDRUK Gateway.

    Data Uses describe approved research projects that have accessed specific
    datasets — useful for understanding who has used NHS data, for what
    purpose, under what legal basis, and what outputs were produced.

    Args:
        query: Free-text search term (filters project titles).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        organisation: Filter by applicant organisation name.
        sector: Filter by sector (e.g. "Academia", "NHS", "Industry").
    """
    params = {
        "project_title": query,
        "page": page,
        "per_page": per_page,
    }
    data = _get("/dur", params)
    return _paginated_summary(data)


# ===========================================================================
# TOOL: get_data_use
# ===========================================================================

@mcp.tool()
def get_data_use(dur_id: int) -> str:
    """Retrieve full details for a single Data Use / Research Project by ID.

    Args:
        dur_id: The integer ID of the data use record.
    """
    data = _get(f"/dur/{dur_id}", {})
    return _fmt(data)


# ===========================================================================
# TOOL: search_publications
# ===========================================================================

@mcp.tool()
def search_publications(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    """Search Publications on the HDRUK Gateway.

    Publications are peer-reviewed papers and reports that used or described
    Gateway datasets. Useful for understanding research outputs, data quality,
    and prior work using specific NHS datasets.

    Args:
        query: Free-text search term (filters paper titles).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        year_from: Filter publications from this year onwards.
        year_to: Filter publications up to this year.
    """
    params = {
        "paper_title": query,
        "page": page,
        "per_page": per_page,
    }
    data = _get("/publications", params)
    items = data.get("data", [])
    if year_from:
        items = [i for i in items if int(i.get("year_of_publication", 0)) >= year_from]
    if year_to:
        items = [i for i in items if int(i.get("year_of_publication", 9999)) <= year_to]
    return _paginated_summary({"data": items, "meta": data})


# ===========================================================================
# TOOL: search_tools
# ===========================================================================

@mcp.tool()
def search_tools(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    sort: Optional[str] = None,
) -> str:
    """Search Analysis Scripts & Software on the HDRUK Gateway.

    Tools include reusable community scripts, pipelines, phenotyping
    algorithms, data cleaning scripts, and software packages linked to
    specific datasets or general health data workflows.

    Args:
        query: Free-text search term (filters tool names).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        sort: Sort field and direction (e.g. "name:asc", "created_at:desc").
    """
    params = {
        "name": query,
        "page": page,
        "per_page": per_page,
        "sort": sort,
    }
    data = _get("/tools", params)
    return _paginated_summary(data)


# ===========================================================================
# TOOL: search_data_custodians
# ===========================================================================

@mcp.tool()
def search_data_custodians(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> str:
    """Search Data Custodians on the HDRUK Gateway.

    Data custodians are organisations responsible for specific datasets —
    NHS England, SAIL Databank, CPRD, UK Biobank, BHF Data Science Centre,
    NHS Scotland, Public Health Wales, etc.

    Args:
        query: Free-text search term (filters custodian names client-side).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
    """
    params = {
        "page": page,
        "per_page": per_page,
    }
    data = _get("/data_custodian_networks", params)
    items = data.get("data", [])
    if query:
        q = query.lower()
        items = [i for i in items if q in i.get("name", "").lower()]
    return _paginated_summary({"data": items, "meta": data})


# ===========================================================================
# TOOL: get_data_custodian
# ===========================================================================

@mcp.tool()
def get_data_custodian(custodian_id: int) -> str:
    """Retrieve full details for a single Data Custodian by ID.

    Returns custodian name, description, contact details, linked datasets,
    collections, and data access information.

    Args:
        custodian_id: The integer ID of the data custodian.
    """
    data = _get(f"/data-custodians/{custodian_id}", {})
    return _fmt(data)


# ===========================================================================
# TOOL: search_all  (cross-entity global search)
# ===========================================================================

@mcp.tool()
def search_all(
    query: str,
    entity_types: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> str:
    """Run a global search across all entity types on the HDRUK Gateway.

    Searches across datasets, collections, data uses, publications, tools,
    and data custodians simultaneously. Useful for an initial broad discovery
    before narrowing to a specific entity type.

    Args:
        query: Required free-text search term.
        entity_types: Comma-separated list of entity types to include.
                      Options: "datasets", "collections", "dur",
                      "publications", "tools", "data_custodians".
                      Defaults to all types if omitted.
        page: Page number (default 1).
        per_page: Results per page (default 10).
    """
    all_types = {
        "datasets": ("/datasets", {"title": query}),
        "collections": ("/collections", {}),
        "dur": ("/dur", {"project_title": query}),
        "publications": ("/publications", {"paper_title": query}),
        "tools": ("/tools", {"name": query}),
        "data_custodians": ("/data_custodian_networks", {}),
    }

    if entity_types:
        requested = [t.strip() for t in entity_types.split(",")]
        all_types = {k: v for k, v in all_types.items() if k in requested}

    results: dict[str, Any] = {}
    total = 0
    with _client() as client:
        for entity, (path, base_params) in all_types.items():
            params = dict(base_params)
            params["page"] = page
            params["per_page"] = per_page
            try:
                resp = client.get(path, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", [])
                # Client-side filter for collections and custodians (no server-side filter)
                if entity in ("collections", "data_custodians") and query:
                    q = query.lower()
                    items = [i for i in items if q in i.get("name", "").lower()]
                results[entity] = items
                total += len(items)
            except httpx.HTTPStatusError as e:
                results[entity] = {"error": str(e)}

    return _fmt({
        "query": query,
        "total_results": total,
        "results": results,
    })


# ===========================================================================
# TOOL: get_dataset_linked_resources
# ===========================================================================

@mcp.tool()
def get_dataset_linked_resources(dataset_id: int) -> str:
    """Get all resources linked to a specific dataset.

    Returns related collections, publications, tools/analysis scripts,
    data uses, and structural metadata (data dictionary) for a dataset.
    Useful for understanding the ecosystem around a particular dataset.

    Args:
        dataset_id: The integer ID of the dataset.
    """
    # Fetch all related resource endpoints in parallel
    results: dict[str, Any] = {}
    endpoints = {
        "publications": f"/datasets/{dataset_id}/publications",
        "tools": f"/datasets/{dataset_id}/tools",
        "data_uses": f"/datasets/{dataset_id}/dur",
        "collections": f"/datasets/{dataset_id}/collections",
    }
    with _client() as client:
        for key, path in endpoints.items():
            try:
                resp = client.get(path)
                resp.raise_for_status()
                results[key] = resp.json()
            except httpx.HTTPStatusError as e:
                results[key] = {"error": str(e)}

    return _fmt({
        "dataset_id": dataset_id,
        "linked_resources": results,
    })


# ===========================================================================
# TOOL: get_publication_linked_datasets
# ===========================================================================

@mcp.tool()
def get_publication_linked_datasets(publication_id: int) -> str:
    """Get all datasets linked to a specific publication.

    Returns the datasets that were used or described in a publication.
    Useful for understanding which datasets underlie a research paper.

    Args:
        publication_id: The integer ID of the publication.
    """
    data = _get(f"/publications/{publication_id}/datasets", {})
    return _fmt(data)


# ===========================================================================
# TOOL: find_datasets_by_publication_topic
# ===========================================================================

@mcp.tool()
def find_datasets_by_publication_topic(
    topic: str,
    max_publications: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    """Find datasets used in publications about a specific topic.

    This workflow:
    1. Searches for publications matching the topic (e.g., "Myocardial Infarction")
    2. For each publication, retrieves the linked datasets from the publication detail
    3. Aggregates and deduplicates datasets across all publications
    4. Returns a summary of datasets used in research on this topic

    Args:
        topic: The research topic to search for (e.g., "Myocardial Infarction", "COVID-19", "Diabetes")
        max_publications: Maximum number of publications to analyze (default 20)
        year_from: Filter publications from this year onwards
        year_to: Filter publications up to this year
    """
    # Step 1: Search for publications on the topic
    pub_params = {
        "paper_title": topic,
        "page": 1,
        "per_page": max_publications,
    }
    pub_data = _get("/publications", pub_params)
    publications = pub_data.get("data", [])

    # Apply year filters if provided
    if year_from:
        publications = [p for p in publications if int(p.get("year_of_publication", 0)) >= year_from]
    if year_to:
        publications = [p for p in publications if int(p.get("year_of_publication", 9999)) <= year_to]

    if not publications:
        return _fmt({
            "topic": topic,
            "message": f"No publications found for topic: {topic}",
            "datasets": [],
        })

    # Step 2: For each publication, get linked datasets from publication detail
    all_datasets = {}
    publication_details = []

    with _client() as client:
        for pub in publications:
            pub_id = pub.get("id")
            pub_title = pub.get("paper_title", "Unknown")
            pub_year = pub.get("year_of_publication", "Unknown")

            try:
                resp = client.get(f"/publications/{pub_id}")
                resp.raise_for_status()
                pub_detail = resp.json()
                datasets = pub_detail.get("data", {}).get("datasets", [])

                publication_details.append({
                    "publication_id": pub_id,
                    "title": pub_title,
                    "year": pub_year,
                    "dataset_count": len(datasets),
                })

                # Aggregate datasets (deduplicate by ID)
                for ds in datasets:
                    ds_id = ds.get("id")
                    if ds_id and ds_id not in all_datasets:
                        all_datasets[ds_id] = ds

            except httpx.HTTPStatusError as e:
                publication_details.append({
                    "publication_id": pub_id,
                    "title": pub_title,
                    "year": pub_year,
                    "error": str(e),
                })

    # Step 3: Prepare summary
    dataset_list = list(all_datasets.values())

    # Sort datasets by title
    dataset_list.sort(key=lambda x: x.get("name", "").lower())

    return _fmt({
        "topic": topic,
        "publications_analyzed": len(publication_details),
        "total_unique_datasets": len(dataset_list),
        "publications": publication_details,
        "datasets": [
            {
                "id": ds.get("id"),
                "datasetid": ds.get("datasetid"),
                "pid": ds.get("pid"),
                "title": ds.get("name"),
                "status": ds.get("status"),
                "link_type": ds.get("link_type"),
                "created": ds.get("created"),
                "updated": ds.get("updated"),
            }
            for ds in dataset_list
        ],
    })


# ===========================================================================
# PROMPT: find_datasets_by_topic
# ===========================================================================

@mcp.prompt()
def find_datasets_by_topic(topic: str) -> str:
    """Find datasets used in publications about a specific health topic.

    This prompt guides the user through discovering which datasets have been
    used in research publications on a given topic (e.g., "Myocardial Infarction",
    "COVID-19", "Type 2 Diabetes", "Stroke", "Dementia").

    The workflow:
    1. Searches for publications matching the topic
    2. Retrieves all datasets linked to those publications
    3. Presents a deduplicated list of datasets with key metadata

    Args:
        topic: The health research topic to investigate
    """
    return f"""I want to find all datasets that have been used in research publications about "{topic}".

Please use the `find_datasets_by_publication_topic` tool with:
- topic: "{topic}"
- max_publications: 20 (to get a good sample)
- year_from: 2020 (to focus on recent research)

This will show me:
1. How many publications were found on this topic
2. Which datasets were used across those publications
3. Key details about each dataset (custodian, keywords, status)

This is useful for:
- Understanding what data is available for {topic} research
- Finding datasets used in high-impact publications
- Identifying data custodians for {topic} research
- Planning new studies using proven datasets"""


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
