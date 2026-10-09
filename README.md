# scenetool

A tool for manipulating scene graphs — VUE diagrams in, SQLite scene graph in the middle, SVG/HTML out.

> **Terminology warning:** "vue" here is **VUE — Visual Understanding Environment**,
> the Tufts concept-mapping/diagramming app, and its `.vue` XML file format. It has
> nothing to do with the Vue.js JavaScript framework.

*State: two-day spike (Jul 25–27, 2013), ~10 commits. Prototype pipeline works end-to-end; never developed further.*

## What it is

An experiment in treating diagrams as data: take `.vue` files drawn in the VUE
diagramming tool, shred them into a normalized **SQLite scene graph**, manipulate
the graph with SQL, and render the result as SVG embedded in HTML.

## How it works

The pipeline lives in `spike/` and is driven by `vue2svg.py`:

1. **Parse** — `vue2svg.py` reads each `.vue` file with lxml (working around VUE's
   misplaced doctype by stripping everything before `<?xml`), walks the `child`
   elements recursively, and extracts ~30 fields per element (position, size, label,
   fill/stroke colors, font, edge endpoints, bezier control points, arrow state)
   into a raw `vuedata` table in `vuedata.sdb` (wiped and rebuilt on every run).
2. **Normalize** — `schema.sql` creates the scene-graph tables: `scene`, `font`,
   `style`, `lmtag` (`node`/`edge`/`group`), `elem` (common element: scene, style,
   tag, label, timestamp, x, y, z-order), `shape` (`rectangle`/`rounded`/`ellipse`),
   `node` (width/height), `edge` (endpoints + up to 2 bezier control points).
3. **Convert** — `vue2elem.sql` folds the raw VUE rows into the normalized schema:
   distinct fonts/styles are extracted, VUE node types (`link`/`node`/`group`) are
   mapped to `lmtag`s, and temp-table triggers split each row into `elem` + `node`
   / `edge` detail rows, assigning z-order sequentially.
4. **View** — `views.sql` builds `nodes`, `edges`, and the denormalized `scenes`
   view (filename, tag, shape, style, geometry) that the renderer queries.
5. **Render** — `vue2svg.py` queries `scenes`, emits per-style CSS classes, and
   prints an HTML document with one inline `<svg>` per input file (`<rect>` for
   nodes, `<line>` for edges).

Usage (from the docstring — note the Python version):

```
python3.2 spike/vue2svg.py test/vue/*.vue > out.html
```

Requires: Python 3, `lxml`, and the `sqlite3` CLI binary (the script shells out to
it to run the `.sql` files).

## Key files

| File | Role |
|---|---|
| `spike/vue2svg.py` | The whole pipeline driver: VUE→SQLite loader + SQL runner + SVG/HTML renderer. |
| `spike/schema.sql` | Normalized scene-graph schema. |
| `spike/vue2elem.sql` | VUE rows → scene elements (fonts/styles normalization, type mapping, triggers). |
| `spike/views.sql` | `nodes`, `edges`, `scenes` views. |
| `test/vue/*.vue` | 18 VUE fixture diagrams: empty, rectangles, circles, text, nested, edges, arrowheads, curves, beziers, dashed, groups, layers. |
| `test/README.txt` | Test plan (basic suite 0000–0700; extended text-styling suite 0201–0220 only partially present as files). |

## Current state

- **~10 commits over two days in July 2013.** Nothing since.
- The end-to-end spike works as a demo, but it's all one script plus SQL — no CLI
  beyond `vue2svg.py`, no manipulation API despite the "manipulating scene graphs"
  billing (the SQL schema *invites* manipulation; no tooling was built on top).
- Renderer is minimal: rectangles and straight lines only — bezier control points
  are extracted and stored but never rendered; circles/ellipses map to the `shape`
  table but the SVG template only handles `node`→rect and `edge`→line.
- MIT licensed.

## Notable findings

- **The gsd+vue import question: resolved — no action needed.** There are zero
  references to `gsd` anywhere in the repo, including full git history
  (`git log -S gsd` is empty). There are likewise no imports of the Vue.js
  framework or any `vue` Python module — the only imports in the codebase are
  Python stdlib (`os`, `sys`, `io`, `itertools`, `collections`, `sqlite3`) plus
  `lxml`. Every "vue" in the repo refers to the VUE *file format* (input data),
  never a dependency. Nothing is dead, nothing is subsumed, because nothing was
  ever imported.
- The schema design (`elem` + typed detail tables, z-order, style/font
  normalization) is the most reusable part — it's a clean little scene-graph model
  that could back a real tool; the VUE-specific loader is the throwaway part.
