from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_landing_promotes_agentic_workflow() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "Agentic engineering workflow" in html
    assert "issue, plan, isolated worktree, tests, visual evidence" in html
    assert "https://knitweb.github.io/k.nitweb.art/docs/AGENTIC_WORKFLOW.md" in html


def test_landing_links_dev_and_core_repositories() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    for text in (
        "https://5mart.ml/knitweb/dev",
        "https://github.com/Knitweb/pulse",
        "https://github.com/Knitweb/molgang",
    ):
        assert text in html
