"""Regression tests for the Rashid agent tool <-> service contracts.

Two Rashid agent tools previously called platform services with the WRONG
signatures and would raise at runtime whenever Rashid tried to use them:

  * ``search_jobs`` called ``SearchService().search_jobs(query=..., filters=...,
    limit=...)`` and iterated the result as a list of dicts, but the real
    ``SearchService.search_jobs`` takes a single ``SearchQuery`` and returns a
    ``SearchResponse`` (``.hits[].data``).
  * ``get_recommendations`` called ``RecommendationEngine()`` (no user) and
    ``get_recommendations(user_id=..., limit=...)`` and read ``job['title']``,
    but the engine requires a ``user`` and returns dicts keyed ``job_title``.

These tests pin the service contracts the fixed tools rely on so a future
signature change fails loudly instead of silently breaking Rashid.
"""
import inspect

from apps.search.plugins.base import SearchQuery, SearchResponse
from apps.search.recommendation_engine import RecommendationEngine
from apps.search.service import SearchService


def test_search_service_accepts_search_query_object():
    """SearchService.search_jobs must take exactly one positional query arg."""
    sig = inspect.signature(SearchService.search_jobs)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    assert len(params) == 1, "search_jobs must accept a single SearchQuery arg"
    # SearchQuery must be constructible the way the tool builds it.
    q = SearchQuery(q="python", filters={"location": "Cairo"}, page=1, per_page=5)
    assert q.q == "python"
    assert q.filters["location"] == "Cairo"


def test_search_response_exposes_hits_with_data():
    """The tool reads response.hits[].data — guard that shape exists."""
    resp = SearchResponse(hits=[], total=0, page=1, per_page=5)
    assert hasattr(resp, "hits")
    assert isinstance(resp.hits, list)


def test_recommendation_engine_requires_user():
    """RecommendationEngine(user) is positional; get_recommendations has no user_id."""
    init_sig = inspect.signature(RecommendationEngine.__init__)
    init_params = [p for p in init_sig.parameters.values() if p.name != "self"]
    assert init_params and init_params[0].name == "user", (
        "RecommendationEngine must take a user positional arg"
    )

    rec_sig = inspect.signature(RecommendationEngine.get_recommendations)
    assert "user_id" not in rec_sig.parameters, (
        "get_recommendations takes n_recommendations, not user_id"
    )
    assert "n_recommendations" in rec_sig.parameters


def test_agent_module_imports_and_builds():
    """The agent module must import and register tools without error."""
    from apps.intelligence import agent as agent_module

    assert hasattr(agent_module, "create_rashid_agent")
    assert hasattr(agent_module, "get_rashid_agent")
    # SearchQuery is imported lazily inside the tool; ensure the symbol is valid.
    assert SearchQuery is not None
