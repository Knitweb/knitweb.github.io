import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_landing_promotes_agentic_workflow() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "Agentic engineering workflow" in html
    assert "issue, plan, isolated worktree, tests, visual evidence" in html
    assert "https://knitweb.github.io/k.nitweb.art/docs/AGENTIC_WORKFLOW.md" in html
    assert 'href="professions/"' in html


def test_landing_links_dev_and_core_repositories() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    for text in (
        "https://5mart.ml/knitweb/dev",
        "https://github.com/Knitweb/pulse",
        "https://github.com/Knitweb/molgang",
        "professions/",
    ):
        assert text in html

def test_readme_links_public_kennisgraaf_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/kennisgraaf.html" in readme
    assert "KENNISGRAAF.md" in readme


def test_kennisgraaf_page_exposes_agent_queryable_graph() -> None:
    html = (ROOT / "kennisgraaf.html").read_text(encoding="utf-8")

    assert "knitweb_graph_drill.json" in html
    assert "window.KNITWEB_GRAPH" in html
    assert "data-drill" in html
    assert "data-term" in html
    assert 'onclick="' not in html
    assert "onclick='" not in html


def test_kennisgraaf_graph_data_integrity() -> None:
    data = json.loads((ROOT / "knitweb_graph_drill.json").read_text(encoding="utf-8"))
    nodes = data["core"]["nodes"]
    node_ids = {node["id"] for node in nodes}

    assert len(nodes) >= 20
    assert "Knitweb" in node_ids
    assert len(node_ids) == len(nodes)

    for link in data["core"]["links"]:
        assert link["source"] in node_ids
        assert link["target"] in node_ids

    indexed = {(row["repo"], row["kind"]) for row in data["search_index"]}
    for repo in data["repos"]:
        assert repo in data["drill"]
        assert data["drill"][repo]["nodes"]
        assert (repo, "mission") in indexed
        assert (repo, "vision") in indexed


def test_professions_artifact_is_published() -> None:
    html = (ROOT / "professions" / "index.html").read_text(encoding="utf-8")

    assert "The Ideal Workflow for 100 Professions" in html
    assert "Those 490 requests, deduplicated, become the product backlog" in html
    assert (ROOT / "professions" / "The_Ideal_Workflow_for_100_Professions.pdf").exists()


def test_readme_links_public_weave_graph_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/graph.html" in readme
    assert "data/weave_public.json" in readme


def test_weave_graph_loads_public_data() -> None:
    html = (ROOT / "graph.html").read_text(encoding="utf-8")

    assert "<title>KnitWeb — Shared-Fabric Knowledge Graph</title>" in html
    assert "weave_public" in html
    # no inline event handlers (CSP-friendly, matches kennisgraaf discipline)
    assert 'onclick="' not in html
    assert "onclick='" not in html


def test_weave_public_data_is_knit_safe() -> None:
    """Privacy regression guard: only publish-allowed nodes may ship to the public repo."""
    data = json.loads((ROOT / "data" / "weave_public.json").read_text(encoding="utf-8"))
    nodes = data["nodes"]
    meta = data["meta"]

    assert len(nodes) >= 100
    assert meta["knitted_nodes"] == len(nodes)
    # every shipped node must be publish-allowed (the private warp never leaves the source machine)
    assert all(node.get("publish") for node in nodes), "private node leaked into public weave data"

    # belt-and-suspenders: no local machine paths or secret markers in shipped content
    blob = json.dumps(data).lower()
    for marker in ("/home/", "/media/", "api_key", "password", "secret", "familie"):
        assert marker not in blob, f"suspicious marker {marker!r} in public weave data"

    # edges must reference shipped nodes only
    node_ids = {n["id"] for n in nodes}
    for edge in data["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
