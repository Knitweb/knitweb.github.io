#!/usr/bin/env python3
"""Build the drill-down + mission/vision + searchable data for the public
Knitweb 3D knowledge graph (5mart.ml/knitweb -> knitweb repo).

Reads the repo charters ingested from knitweb.github.io and emits
knitweb_graph_drill.json:
  { core: {nodes, links},            # top level: the repos + relations
    drill: { <repo>: {nodes, links}, # per-repo sub-graph: mission/vision/role/components
    search_index: [ {id, repo, text, kind} ]  # flat index for client + agent/Lens query
  }
Mission & vision are the focus (per the user) so each repo carries them and a
dedicated mission + vision sub-node in its drill graph.
"""
import json, re, os

KP = "/media/knight2/EDS2/root-offload/home/knight2/knowledge_pit"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knitweb_graph_drill.json")

# colour per repo (matches the live 5mart viewer palette feel)
COLOR = {"pulse": "#4a90d9", "lens": "#a05bd0", "molgang": "#3fa66a", "vbank": "#2e9e5b",
         "monitor": "#2aa39a", "virtualpc": "#d98a2b", "docs": "#2aa39a", "news": "#c0653a"}
ROLE_KW = {"mission": "#ffd479", "vision": "#7ee0ff", "role": "#9fb4c8"}


def parse(body):
    def grab(label, nxt):
        m = re.search(re.escape(label) + r":\s*(.*?)(?:\n\n|" + nxt + r":|$)", body, re.S)
        return (m.group(1).strip() if m else "")
    title = body.split("\n")[0].strip()
    return {
        "title": title,
        "vision": grab("VISION", "MISSION"),
        "mission": grab("MISSION", "ROLE"),
        "role": grab("ROLE", "ACADEMIC FIT"),
        "academic": grab("ACADEMIC FIT", "$"),
    }


def keywords(text, n=8):
    # cheap keyword extraction: distinctive lowercased words, deduped, length>4
    words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", text.lower())
    stop = {"which", "their", "these", "those", "where", "every", "without", "across",
            "knitweb", "weave", "while", "there", "other", "first", "about", "would"}
    seen, out = set(), []
    for w in words:
        if w in stop or w in seen:
            continue
        seen.add(w); out.append(w)
        if len(out) >= n:
            break
    return out


def main():
    rows = [json.loads(l) for l in open(f"{KP}/lightrag/knitweb_github_io_facts.jsonl") if l.strip()]
    charters = {r["name"].replace(" charter", "").split("/")[-1]: parse(r["content"])
                for r in rows if r.get("kind") == "repo_charter"}

    core_nodes, core_links, drill, index = [], [], {}, []
    for repo, c in charters.items():
        col = COLOR.get(repo, "#8899aa")
        kw = keywords(c["vision"] + " " + c["mission"])
        core_nodes.append({"id": repo, "name": repo, "color": col, "val": 18,
                           "group": "knitweb repo", "kw": "|".join(kw),
                           "desc": c["title"], "mission": c["mission"], "vision": c["vision"],
                           "hasDrill": True})
        # every repo is part of the Knitweb platform
        core_links.append({"source": repo, "target": "Knitweb", "rel": "part-of"})
        # per-repo drill sub-graph: hub + mission + vision + role (+ keyword leaves)
        dn = [{"id": f"{repo}", "name": repo, "color": col, "val": 16, "group": "repo",
               "desc": c["title"]},
              {"id": f"{repo}:mission", "name": "Mission", "color": ROLE_KW["mission"], "val": 11,
               "group": "mission", "desc": c["mission"]},
              {"id": f"{repo}:vision", "name": "Vision", "color": ROLE_KW["vision"], "val": 11,
               "group": "vision", "desc": c["vision"]},
              {"id": f"{repo}:role", "name": "Role in the whole", "color": ROLE_KW["role"], "val": 9,
               "group": "role", "desc": c["role"]}]
        dl = [{"source": f"{repo}:mission", "target": repo, "rel": "mission-of"},
              {"source": f"{repo}:vision", "target": repo, "rel": "vision-of"},
              {"source": f"{repo}:role", "target": repo, "rel": "role-of"}]
        for k in kw:
            dn.append({"id": f"{repo}:kw:{k}", "name": k, "color": "#5a6b80", "val": 4,
                       "group": "keyword", "desc": f"key concept of {repo}"})
            dl.append({"source": f"{repo}:kw:{k}", "target": repo, "rel": "concept-of"})
        drill[repo] = {"nodes": dn, "links": dl}
        # flat search index (client + Lens/agent queryable)
        index.append({"id": repo, "repo": repo, "kind": "repo", "text": c["title"]})
        index.append({"id": f"{repo}:mission", "repo": repo, "kind": "mission", "text": c["mission"]})
        index.append({"id": f"{repo}:vision", "repo": repo, "kind": "vision", "text": c["vision"]})

    # the platform hub node
    core_nodes.append({"id": "Knitweb", "name": "Knitweb", "color": "#caa64a", "val": 26,
                       "group": "platform", "kw": "weave|p2p|content-addressed|append-only|crdt|provenance|credence|graphrag",
                       "desc": "Knitweb — the P2P knowledge fabric (the weave) the whole suite rides on.",
                       "mission": "Be the single tiny deterministic substrate for a peer-to-peer knowledge commons.",
                       "vision": "A weave, not a chain: partial-order, contradiction-tolerant, provenance-bearing knowledge.",
                       "hasDrill": False})

    out = {"generated": "knitweb_public_drill",
           "core": {"nodes": core_nodes, "links": core_links},
           "drill": drill, "search_index": index,
           "repos": list(charters.keys())}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(core_nodes)} core nodes, {len(drill)} drill graphs, {len(index)} index rows")


if __name__ == "__main__":
    main()
