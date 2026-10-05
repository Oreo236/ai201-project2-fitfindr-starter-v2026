# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The three tools and planning loop are implemented. Search runs through the
> local MCP server; `--trace` shows the tool calls and their results.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

 **What it does:** Writes a short, post-ready caption for the new listing and suggested outfit.
 **Uncached three-run fit-card test command:**
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[0]; outfit='jeans and white sneakers'; print('\\n---\\n'.join(create_fit_card(outfit, item) for _ in range(3)))"
Scored these classic vintage Levi's 501 jeans on Depop for just $38.00, and I am obsessed with the perfectly worn-in medium wash and subtle knee fading. They have that ultimate effortless streetwear vibe that makes any outfit look instantly cool. Throw them on with crisp white sneakers and a simple tee for the easiest everyday uniform.
---
Nothing beats the authentic lived-in fade of these classic vintage Levi's 501 jeans, bringing the ultimate effortless streetwear vibe to your wardrobe. Style them simply with a crisp tee and white sneakers for an easy, timeless look. Grab this exact pair on Depop for just $38.00 before someone else does!
---
Scored these classic vintage Levi's 501 jeans with the perfect broken-in indigo wash and subtle knee fading for just $38 on Depop. They have that ultimate effortless streetwear vibe that instantly grounds any outfit. Style them with crisp white sneakers and a simple tee for an easy, timeless look.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## Milestone 1: Data Notes

- **Listing fields:** `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. `brand` can be `null`.
- **Wardrobe item fields:** `id`, `name`, `category`, `colors`, `style_tags`, and optional `notes` (which can be `null`).
- **Empty wardrobe:** `{"items": []}`.
- **Current check:** `python app.py ask 'vintage graphic tee under $30'` completes listing search, outfit suggestion, and fit-card generation.

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a natural-language clothing request, including optional size and
price limits, and searches local secondhand listings. It selects the highest
ranked match, asks a model for outfit ideas using the saved wardrobe, and
produces a short fit-card caption with listing facts.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters listings by optional size and maximum price, then ranks the remaining listings by how many request keywords appear in the listing's `title`, `description`, or `style_tags`. Ignore case, discard zero-keyword matches, and keep source order for ties.
- **Inputs:** `description` (str, request keywords); `size` (str | None, optional); `max_price` (float | None, optional, inclusive ceiling). Size matching is case-insensitive on a complete size token or slash-separated alternative, so `M` matches `S/M` but not `XL`.
- **Returns:** Up to `SEARCH_RESULT_LIMIT` listing dicts, best match first. Each has `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str | None), and `platform` (str).
- **When it has nothing:** Returns an empty list (`[]`), never `None`.

### `suggest_outfit`

- **What it does:** Suggests one or two ways to style a new listing, using the user's wardrobe when available.
- **Inputs:** `new_item` (listing dict with the fields and types listed under `search_listings`); `wardrobe` (dict with `items: list[wardrobe item]`; each item has `id` (str), `name` (str), `category` (str), `colors` (list[str]), `style_tags` (list[str]), and optional `notes` (str | None)).
- **Returns:** A non-empty string with one or two outfit suggestions; with wardrobe items, suggestions name pieces the user owns.
- **When it has nothing:** If `wardrobe["items"]` is empty, returns general styling advice for the new item as a non-empty string.

### `create_fit_card`

- **What it does:** Writes a short, post-ready caption for the new listing and suggested outfit.
- **Inputs:** `outfit` (str, the suggestion from `suggest_outfit`); `new_item` (listing dict with the fields and types listed under `search_listings`).
- **Returns:** A two-to-four-sentence caption that mentions the item, its price, and its platform once each, and gives a specific sense of its vibe.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a non-empty descriptive message about the listing instead of raising an error.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message telling the user what to change (for example, the item description, size, or price limit) and return the session without calling the other tools. Otherwise, save the results, select the first listing, pass it and the wardrobe to `suggest_outfit`, then pass that suggestion and listing to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract an optional size and a price ceiling; the remaining words become the search description.

**What moves through the session:** `query` -> `parsed` -> `search_results` -> `selected_item` -> `outfit_suggestion` -> `fit_card`. An empty result or model failure sets `error` and returns early.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('butterfly', size='M', max_price=18))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}]

```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Here are two wearable outfits centered around your new Vintage Levi's 501 Jeans:

**Outfit 1: Casual Streetwear**
* **Top:** White ribbed tank top
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Outfit 2: Layered & Edgy**
* **Top:** Black cropped zip hoodie
* **Outerwear:** Vintage black denim jacket
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt

```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[0]; outfit='jeans and white sneakers'; print('\\n---\\n'.join(create_fit_card(outfit, item) for _ in range(3)))"
Scored these classic vintage Levi's 501 jeans on Depop for just $38.00, and I am obsessed with the perfectly worn-in medium wash and subtle knee fading. They have that ultimate effortless streetwear vibe that makes any outfit look instantly cool. Throw them on with crisp white sneakers and a simple tee for the easiest everyday uniform.
---
Nothing beats the authentic lived-in fade of these classic vintage Levi's 501 jeans, bringing the ultimate effortless streetwear vibe to your wardrobe. Style them simply with a crisp tee and white sneakers for an easy, timeless look. Grab this exact pair on Depop for just $38.00 before someone else does!
---
Scored these classic vintage Levi's 501 jeans with the perfect broken-in indigo wash and subtle knee fading for just $38 on Depop. They have that ultimate effortless streetwear vibe that instantly grounds any outfit. Style them with crisp white sneakers and a simple tee for an easy, timeless look.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item ID reaches outfit tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has correct facts and length | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling is respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**

Criterion 1 from `results/run_2026-10-04_2229_before.md`, produced by
`agent.py::run_agent` and `tools.py::create_fit_card`:

```text
selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
Embrace ultimate nostalgia with this fitted white baby tee featuring a dreamy pink and purple butterfly graphic, giving off major early 2000s streetwear energy. I just scored it on depop for only $18.00! Style it effortlessly for the weekend by pairing it with baggy dark-wash straight-leg jeans, chunky white sneakers, and a vintage black denim jacket.
```

Criterion 2 from that run log, produced by `agent.py::run_agent`:
```text
No listings matched. Try a broader item description, a different size, or a higher price limit.
[2] search_listings (via MCP) -> [] (empty)
[3] empty_search_branch -> stopping before suggest_outfit
```

Criterion 3 from that run log, produced by `agent.py::run_agent`:
```text
[3] select_item out: lst_002: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit in: new_item.id=lst_002, wardrobe_items=10
```

Criterion 4 from that run log, produced by `tools.py::create_fit_card`:
```text
Embrace total nostalgic energy with this fitted Y2K baby tee, featuring a dreamy pink and purple butterfly graphic that gives off the ultimate early 2000s streetwear vibe. I just snagged this gem on Depop for $18, and it's practically begging to be styled with dark-wash baggy straight-leg jeans, a vintage black denim jacket, and chunky white sneakers.
```

Criterion 5 direct output from `tools.py::search_listings`:
```text
[('lst_002', 18.0), ('lst_006', 24.0), ('lst_017', 15.0), ('lst_033', 19.0), ('lst_011', 27.0), ('lst_015', 26.0)]
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4/5 | MET (5/5) | All five runs completed and returned a fit card. |
| 2 | Empty search stops before `suggest_outfit` | 5/5 | MET (5/5) | Each run returned an actionable message and stopped before the second tool. |
| 3 | Selected ID reaches the outfit tool | 5/5 | MET (5/5) | All five traces pass `lst_002` to `suggest_outfit`, matching the session selection. |
| 4 | Caption facts and length | 4/5 | MET (5/5) | All five baseline captions were 2-4 sentences and included the listing price and platform. |
| 5 | Price ceiling respected | 5/5 | MET (5/5) | All six results in each of five runs were at or below $30. |

**Diagnoses**

There were no criterion misses to diagnose. All five targets held for the
tested inputs. The main limitation is scenario variety: criteria 1, 3, and 4
repeat one matching query, so these results do not establish performance across
different listings or wording. I would broaden criterion 1's test set next.

**Failure-mode checks**

- **Empty search:** “No listings matched. Try a broader item description, a different size, or a higher price limit.” The trace stopped before `suggest_outfit`.
- **Empty wardrobe:** `suggest_outfit` returned: “Here are two ways to style the cropped denim jacket: 1. Monochromatic Casual: Pair the light-wash jacket with white or cream bottoms and a simple neutral t-shirt for a clean, cohesive look. 2. Proportion Play: Layer the cropped length over a longer flowy dress or tunic to create visual contrast with the structured shoulders.”
- **Model unavailable:** “The outfit suggestion model could not be reached. Check your API key and internet connection, then try again. Details: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.” The invalid character was applied only to a child process environment; `.env` remained unchanged. The handler caught the failure at `suggest_outfit` without a raw traceback.


---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```text
[1] parse_query
     in:  vintage graphic tee under $30
     out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
     in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
     out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
     in:  {'result_count': 10}
     out: lst_002: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
     in:  new_item.id=lst_002, wardrobe_items=10
     out: Here are two wearable outfits centered around your new Y2K Baby Tee — Butterfly Print: **Outfit 1: Y2K Streetwear…
[5] create_fit_card
     in:  item.id=lst_002, outfit=Here are two wearable outfits centered around your new Y2K Baby Tee — Butterfly Print:…
     out: Embrace total early 2000s energy with this sweet fitted crop top featuring a whimsical butterfly graphic…
```

**Empty search**

```text
[1] parse_query
     in:  designer ballgown size XXS under $5
     out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
     in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
     out: [] (empty)
[3] empty_search_branch
     in:  {'result_count': 0}
     out: No listings matched. Try a broader item description, a different size, or a higher price limit.
     →    stopping before suggest_outfit
```

**On the MCP move:** `agent.py::run_agent` now calls `search_listings` through
`mcp_client.call_tool`; `mcp_server.py` registers the typed function and delegates
to the existing implementation. `python mcp_client.py` listed the tool, and a
normal query returned the same list-of-dictionaries shape through MCP. The
empty-result branch continued to work on the MCP response.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** In `tools.py::create_fit_card`, I added a required canonical
listing sentence to the prompt and asked the model to copy it verbatim once,
without repeating the price or platform elsewhere.

**Which failure it was meant to fix:** Baseline
`results/run_2026-10-04_2229_before.md`, criterion 5 try 1, contained the
malformed rendered amount `$18.0f` in its incidental fit card. Search itself
passed; this was a caption-fact formatting defect.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item ID reaches outfit tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has correct facts and length | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling is respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** All five after-run captions include the
canonical `$18`/`depop` sentence, and all five still meet criterion 4's sentence
count and fact requirements. Scores remained 5/5 before and after; the change
corrected the observed malformed price representation but did not increase a
criterion score because no baseline target was missed.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No original criterion remains missed. The scenarios still cover only one
matching item and one query phrasing; broader query and listing coverage would
be the next useful test, but was outside this unit's single-improvement limit.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
