# Knitweb 3D kennisgraaf — drill-down + Lens-zoek

`kennisgraaf.html` is the public 3D knowledge graph of the Knitweb suite, with a
**drill-down layer** focused on each repo's **mission & vision**, and a **search /
query** box so people *and agents* can find and ask.

## What it does
- **Top level** — the knitweb repos (Pulse, Lens, Molgang, vBank, Monitor, VirtualPC,
  Docs, News) around the **Knitweb** platform hub. Data: `knitweb_graph_drill.json`.
- **Drill-down** — click a repo (or open `kennisgraaf.html#pulse`) to zoom into its
  sub-graph: **Mission**, **Vision**, **Role**, and its key concepts. The panel shows
  mission + vision verbatim from the whitepaper charters.
- **Search** — type a term → highlights the matching repos and lists the mission/vision
  snippets that match (client-side, over the embedded `search_index`).
- **Query via Lens** — flip *via Lens* on (or click **Vraag**) to send a natural-language
  question to **Lens** (the reasoning lobe, `Knitweb/lens`). Wire it up by running
  `knitweb-lens serve` and setting `window.LENS_ENDPOINT` (default `/lens/query`); the
  page POSTs `{query, scope:"knitweb-graph"}` and renders `{answer, sources}`. If Lens is
  unreachable it falls back to the local keyword search — so the page always works.

## For agents (P2P searchability)
- Fetch `knitweb_graph_drill.json` directly — `core`, `drill.<repo>`, and a flat
  `search_index` of `{id, repo, kind:repo|mission|vision, text}`. In-page it's also on
  `window.KNITWEB_GRAPH`.
- Deep links: `kennisgraaf.html#<repo>` drills; `?q=<term>` pre-runs a search.
- For semantic retrieval point agents at the same Lens endpoint the UI uses.

## Rebuild the data
`python3 build_drill_data.py` regenerates `knitweb_graph_drill.json` from the ingested
repo charters (mission/vision/role per repo).
