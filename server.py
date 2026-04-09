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
    meta = data.get("meta", {})
    items = data.get(item_key, data.get("data", []))
    total = meta.get("total", len(items))
    per_page = meta.get("per_page", len(items))
    current_page = meta.get("current_page", 1)
    last_page = meta.get("last_page", 1)

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
    data_custodian_id: Optional[int] = None,
    geographic_coverage: Optional[str] = None,
    publisher: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search the HDRUK Gateway for Datasets & BioSamples.

    Returns a paginated list of datasets with their metadata including
    title, abstract, data custodian, keywords, temporal/geographic coverage,
    and unique persistent identifiers (PIDs).

    Args:
        query: Free-text search term (searches title, abstract, keywords,
               and enriched medical terms such as ICD-10, SNOMED, OMOP).
        page: Page number to retrieve (default 1).
        per_page: Results per page (default 10, max 100).
        data_custodian_id: Filter by a specific data custodian / publisher ID.
        geographic_coverage: Filter by geographic coverage (e.g. "England",
                             "Wales", "Scotland", "United Kingdom").
        publisher: Filter by publisher name (partial match).
        start_date: Filter datasets updated after this date (YYYY-MM-DD).
        end_date: Filter datasets updated before this date (YYYY-MM-DD).
        sort_by: Field to sort by (e.g. "title", "updated_at").
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "data_custodian_id": data_custodian_id,
        "geographic_coverage": geographic_coverage,
        "publisher": publisher,
        "start_date": start_date,
        "end_date": end_date,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
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
    data_custodian_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search the HDRUK Gateway for Collections / Networks.

    Collections group related datasets, publications, tools, and data uses
    by theme, disease, domain, or organisation (e.g. BHF Data Science Centre
    collection, COVID-19 collection, Secure Data Environment collections).

    Args:
        query: Free-text search term.
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        data_custodian_id: Filter by data custodian ID.
        sort_by: Field to sort by.
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "data_custodian_id": data_custodian_id,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
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
    dataset_id: Optional[int] = None,
    organisation: Optional[str] = None,
    sector: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search Data Uses / Research Projects on the HDRUK Gateway.

    Data Uses describe approved research projects that have accessed specific
    datasets — useful for understanding who has used NHS data, for what
    purpose, under what legal basis, and what outputs were produced.

    Args:
        query: Free-text search term (project title, lay summary, etc.).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        dataset_id: Filter data uses linked to a specific dataset ID.
        organisation: Filter by applicant organisation name.
        sector: Filter by sector (e.g. "Academia", "NHS", "Industry").
        sort_by: Field to sort by.
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "dataset_id": dataset_id,
        "organisation": organisation,
        "sector": sector,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
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
    dataset_id: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search Publications on the HDRUK Gateway.

    Publications are peer-reviewed papers and reports that used or described
    Gateway datasets. Useful for understanding research outputs, data quality,
    and prior work using specific NHS datasets.

    Args:
        query: Free-text search term (title, abstract, DOI, authors).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        dataset_id: Filter publications linked to a specific dataset ID.
        year_from: Filter publications from this year onwards.
        year_to: Filter publications up to this year.
        sort_by: Field to sort by.
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "dataset_id": dataset_id,
        "year_from": year_from,
        "year_to": year_to,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
    }
    data = _get("/publications", params)
    return _paginated_summary(data)


# ===========================================================================
# TOOL: search_tools
# ===========================================================================

@mcp.tool()
def search_tools(
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    category: Optional[str] = None,
    programming_language: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search Analysis Scripts & Software on the HDRUK Gateway.

    Tools include reusable community scripts, pipelines, phenotyping
    algorithms, data cleaning scripts, and software packages linked to
    specific datasets or general health data workflows.

    Args:
        query: Free-text search term.
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        category: Filter by tool category (e.g. "Analysis", "Phenotyping").
        programming_language: Filter by language (e.g. "R", "Python", "SQL").
        sort_by: Field to sort by.
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "category": category,
        "programming_language": programming_language,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
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
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> str:
    """Search Data Custodians on the HDRUK Gateway.

    Data custodians are organisations responsible for specific datasets —
    NHS England, SAIL Databank, CPRD, UK Biobank, BHF Data Science Centre,
    NHS Scotland, Public Health Wales, etc.

    Args:
        query: Free-text search term (organisation name).
        page: Page number (default 1).
        per_page: Results per page (default 10, max 100).
        sort_by: Field to sort by.
        sort_direction: "asc" or "desc".
    """
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
    }
    data = _get("/data-custodians", params)
    return _paginated_summary(data)


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
    params = {
        "search": query,
        "page": page,
        "perPage": per_page,
    }
    if entity_types:
        params["type"] = entity_types

    data = _get("/search", params)
    return _paginated_summary(data)


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
# Entry point
# ===========================================================================

if __name__ == "__main__":
    mcp.run()
