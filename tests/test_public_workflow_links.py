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
        "quantum-machines.html",
        "chemistry-minerals.html",
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
    assert "publishable slices may ship" in html.lower()
    assert "maskPriv" not in html
    assert "onlyPriv" not in html
    assert "private masked" not in html
    assert "private only" not in html
    assert "innerHTML" not in html
    assert "http://localhost:8765/interpret" not in html
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


def test_readme_links_quantum_machine_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/quantum-machines.html" in readme
    assert "https://5mart.ml/intel/" in readme
    assert "data/quantum_machines.json" in readme


def test_readme_links_chemistry_mineral_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/chemistry-minerals.html" in readme
    assert "https://5mart.ml/intel/chemistry-minerals.html" in readme
    assert "data/chemistry_minerals.json" in readme


def test_quantum_machine_page_exposes_search_and_record_gui() -> None:
    html = (ROOT / "quantum-machines.html").read_text(encoding="utf-8")

    assert "<title>KnitWeb - Quantum Machine Index</title>" in html
    assert "data/quantum_machines.json" in html
    assert "WNW Quantum Systems Intel" in html
    assert "renderWnwIntel" in html
    assert "renderQueryEstimate" in html
    assert "scoreMachine" in html
    assert "levenshtein" in html
    assert "KnitWeb Machine Record" in html
    assert "grid-template-columns:repeat(auto-fit,minmax(120px,1fr))" in html
    assert "min-height:78px" in html
    assert ".stat .n.long" in html
    assert "valueNode.title = value" in html
    assert "localStorage" in html
    assert "innerHTML" not in html
    assert 'onclick="' not in html
    assert "onclick='" not in html


def test_quantum_machine_seed_data_integrity() -> None:
    data = json.loads((ROOT / "data" / "quantum_machines.json").read_text(encoding="utf-8"))
    machines = data["machines"]
    ids = {machine["id"] for machine in machines}

    assert data["meta"]["schema"] == "knitweb.quantum-machine-index.v1"
    assert data["meta"]["coverage"] == "curated_seed_not_exhaustive"
    assert len(machines) >= 45
    assert len(ids) == len(machines)
    assert len(data["meta"]["wnw_intel"]["layers"]) >= 6

    for required in (
        "ibm-quantum-system-two-heron",
        "google-willow",
        "quantinuum-h2",
        "quera-aquila",
        "intel-tunnel-falls",
        "origin-quantum-wukong",
        "riken-64-qubit-superconducting",
    ):
        assert required in ids

    for machine in machines:
        for field in ("id", "name", "provider", "architecture", "modality", "status", "source_urls"):
            assert machine.get(field), f"{machine.get('id', '<missing>')} missing {field}"
        assert isinstance(machine["source_urls"], list)
        assert all(str(url).startswith("https://") for url in machine["source_urls"])


def test_chemistry_mineral_page_exposes_search_and_enrichment_gui() -> None:
    html = (ROOT / "chemistry-minerals.html").read_text(encoding="utf-8")

    assert "<title>KnitWeb - Chemistry Mineral Index</title>" in html
    assert "data/chemistry_minerals.json" in html
    assert "scoreItem" in html
    assert "levenshtein" in html
    assert "renderEnrichment" in html
    assert "renderIsotopeTable" in html
    assert "ideal_formula_mass_percent" in html
    assert "Photons, photos, and sources" in html
    assert "grid-template-columns:repeat(auto-fit,minmax(120px,1fr))" in html
    assert "min-height:82px" in html
    assert ".stat .n.long" in html
    assert "valueNode.title = value" in html
    assert "innerHTML" not in html
    assert 'onclick="' not in html
    assert "onclick='" not in html


def test_chemistry_mineral_seed_data_integrity() -> None:
    data = json.loads((ROOT / "data" / "chemistry_minerals.json").read_text(encoding="utf-8"))
    elements = data["elements"]
    minerals = data["minerals"]
    edges = data["edges"]
    element_ids = {element["id"] for element in elements}
    mineral_ids = {mineral["id"] for mineral in minerals}
    element_symbols = {element["symbol"] for element in elements}

    assert data["meta"]["schema"] == "knitweb.chemistry-mineral-index.v1"
    assert data["meta"]["coverage"] == "pubchem_all_118_elements_curated_mineral_seed_not_exhaustive"
    assert data["meta"]["routes"]["display_mirror"] == "https://5mart.ml/intel/chemistry-minerals.html"
    assert len(elements) == 118
    assert len(minerals) >= 35
    assert len(element_ids) == len(elements)
    assert len(mineral_ids) == len(minerals)

    silicon = next(element for element in elements if element["symbol"] == "Si")
    assert silicon["neutral_electron_count"] == 14
    assert {"Si-28", "Si-29", "Si-30", "Si-31"}.issubset(
        {isotope["isotope"] for isotope in silicon["isotope_variants"]}
    )

    required_minerals = {
        "mineral:quartz",
        "mineral:spodumene",
        "mineral:hematite",
        "mineral:vanadinite",
        "mineral:carnotite",
    }
    assert required_minerals.issubset(mineral_ids)

    for mineral in minerals:
        assert set(mineral["element_symbols"]).issubset(element_symbols)
        assert sum(row["mass_percent_bps"] for row in mineral["ideal_formula_mass_percent"]) == 10000
        assert mineral["composition_basis"] == "ideal_formula_mass_percent_from_formula"

    for edge in edges:
        assert edge["source"] in mineral_ids
        assert edge["target"] in element_ids
        assert edge["rel"] == "contains-element"
        assert 0 < edge["weight_bps"] <= 10000

    profile_symbols = {profile["symbol"] for profile in data["enrichment_profiles"]}
    for symbol in ("Si", "Li", "V", "U", "Fe"):
        assert symbol in profile_symbols


def test_quantum_circuit_catalog_is_public_and_queryable() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    data = json.loads((ROOT / "data" / "quantum_circuits.json").read_text(encoding="utf-8"))
    circuits = data["circuits"]
    ids = {circuit["id"] for circuit in circuits}

    assert "data/quantum_circuits.json" in readme
    assert data["meta"]["schema"] == "knitweb.lens.quantum-circuit-index.v1"
    assert data["meta"]["count"] == len(circuits)
    assert data["meta"]["routes"]["intelfield"] == "/intel/data/quantum_circuits.json"
    assert len(circuits) >= 100
    assert len(ids) == len(circuits)

    for circuit in circuits:
        for field in ("id", "name", "family", "language", "operations", "qubits", "schema", "tags"):
            assert circuit.get(field), f"{circuit.get('id', '<missing>')} missing {field}"
        assert circuit["schema"] == "knitweb.lens.quantum-circuit.v1"
        assert isinstance(circuit["operations"], list)
        assert all(operation.get("gate") for operation in circuit["operations"])
