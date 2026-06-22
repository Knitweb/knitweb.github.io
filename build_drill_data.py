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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "knitweb_graph_drill.json")

# Charters live in-repo (knitweb_charters.jsonl) so the build is portable and
# leaks no local machine paths. KNITWEB_CHARTERS can point at a richer local
# source (e.g. the LightRAG facts dump) when rebuilding from the knowledge pit.
CHARTERS = os.environ.get("KNITWEB_CHARTERS", os.path.join(HERE, "knitweb_charters.jsonl"))

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
    rows = [json.loads(l) for l in open(CHARTERS) if l.strip()]
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

    # ── merge the domain knitwebs from the existing 5mart viewer (agriknit, mediweave …) ──
    # so the graph is "compleet": core repos (mission/vision drill) + domain applications.
    existing = os.path.join(os.path.dirname(os.path.abspath(__file__)), "existing_5mart_view.json")
    if os.path.exists(existing):
        view = json.load(open(existing))
        have = {n["id"] for n in core_nodes}
        lower = {n["id"].lower(): n["id"] for n in core_nodes}   # merge "Pulse" onto charter "pulse"
        idmap = {}
        for n in view["nodes"]:
            nid = n["id"]
            if nid.lower() in lower:
                idmap[nid] = lower[nid.lower()]; continue
            idmap[nid] = nid
            if nid in have:
                continue
            have.add(nid)
            core_nodes.append({"id": nid, "name": n.get("name", nid), "color": n.get("color", "#6b7a8f"),
                               "val": n.get("val", 9), "group": n.get("group", "domain knitweb"),
                               "kw": n.get("kw", ""), "desc": n.get("desc", ""), "hasDrill": True})
            dn = [{"id": nid, "name": n.get("name", nid), "color": n.get("color", "#6b7a8f"),
                   "val": 14, "group": n.get("group", "domain knitweb"), "desc": n.get("desc", "")}]
            dl = []
            for k in (n.get("kw", "").split("|") if n.get("kw") else []):
                if not k:
                    continue
                kid = f"{nid}:kw:{k}"
                dn.append({"id": kid, "name": k, "color": "#5a6b80", "val": 4, "group": "keyword",
                           "desc": f"key concept of {nid}"})
                dl.append({"source": kid, "target": nid, "rel": "concept-of"})
            drill[nid] = {"nodes": dn, "links": dl}
            index.append({"id": nid, "repo": nid, "kind": "domain",
                          "text": (n.get("desc", "") + " " + n.get("kw", "")).strip()})
        seen = {(l["source"], l["target"]) for l in core_links}
        for l in view.get("links", []):
            s, t = idmap.get(l.get("source"), l.get("source")), idmap.get(l.get("target"), l.get("target"))
            if s and t and s != t and (s, t) not in seen and (t, s) not in seen:
                seen.add((s, t)); core_links.append({"source": s, "target": t, "rel": l.get("rel", "")})

    out = {"generated": "knitweb_public_drill",
           "core": {"nodes": core_nodes, "links": core_links},
           "drill": drill, "search_index": index,
           "repos": list(charters.keys())}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(core_nodes)} core nodes, {len(drill)} drill graphs, {len(index)} index rows")


if __name__ == "__main__":
    main()
