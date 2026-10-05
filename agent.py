"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import MCPError, call_tool
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

     The query is parsed with regular expressions. Listing search runs over MCP;
     an empty result stops before either model-backed tool. ModelUnavailable is
     caught at both model tools and returned as an actionable session error.
     Each executed step is recorded in the trace.
     """
    session = new_session(query, wardrobe)

    iteration = 0
    while True:
        iteration += 1
        trace.check_iterations(iteration)

        price_match = re.search(
            r"\b(?:under|below|less than|at most|max(?:imum)?)\s+\$?(\d+(?:\.\d+)?)\b",
            query,
            re.IGNORECASE,
        )
        size_match = re.search(
            r"\b(?:size\s+|in\s+size\s+)([A-Za-z0-9]+(?:/[A-Za-z0-9]+)*)",
            query,
            re.IGNORECASE,
        )
        description = query
        if price_match:
            description = description.replace(price_match.group(0), " ")
        if size_match:
            description = description.replace(size_match.group(0), " ")
        parsed = {
            "description": re.sub(r"\s+", " ", description).strip(" ,"),
            "size": size_match.group(1) if size_match else None,
            "max_price": float(price_match.group(1)) if price_match else None,
        }
        session["parsed"] = parsed
        trace.step("parse_query", inputs=query, returned=parsed)

        search_inputs = parsed.copy()
        try:
            results = call_tool("search_listings", search_inputs)
        except MCPError as exc:
            trace.step(
                "search_listings (via MCP)",
                inputs=search_inputs,
                returned=f"MCPError: {exc}",
            )
            session["error"] = (
                "The listing search service could not be reached. Check that the "
                "MCP server is available, then try your search again. "
                f"Details: {exc}"
            )
            return session

        session["search_results"] = results
        trace.step("search_listings (via MCP)", inputs=search_inputs, returned=results)
        if not results:
            session["error"] = (
                "No listings matched. Try a broader item description, a different "
                "size, or a higher price limit."
            )
            trace.step(
                "empty_search_branch",
                inputs={"result_count": 0},
                returned=session["error"],
                note="stopping before suggest_outfit",
            )
            return session

        session["selected_item"] = results[0]
        selected_item = session["selected_item"]
        trace.step(
            "select_item",
            inputs={"result_count": len(results)},
            returned=selected_item,
        )

        try:
            outfit = suggest_outfit(selected_item, session["wardrobe"])
        except ModelUnavailable as exc:
            trace.step(
                "suggest_outfit",
                inputs=(
                    f"new_item.id={selected_item.get('id')}, "
                    f"wardrobe_items={len(session['wardrobe'].get('items') or [])}"
                ),
                returned=f"ModelUnavailable: {exc}",
            )
            session["error"] = (
                "The outfit suggestion model could not be reached. Check your API "
                "key and internet connection, then try again. "
                f"Details: {exc}"
            )
            return session
        session["outfit_suggestion"] = outfit
        trace.step(
            "suggest_outfit",
            inputs=(
                f"new_item.id={selected_item.get('id')}, "
                f"wardrobe_items={len(session['wardrobe'].get('items') or [])}"
            ),
            returned=outfit,
        )

        try:
            fit_card = create_fit_card(outfit, selected_item)
        except ModelUnavailable as exc:
            trace.step(
                "create_fit_card",
                inputs=f"item.id={selected_item.get('id')}, outfit={outfit}",
                returned=f"ModelUnavailable: {exc}",
            )
            session["error"] = (
                "The fit-card model could not be reached. Check your API key and "
                "internet connection, then try again. "
                f"Details: {exc}"
            )
            return session
        session["fit_card"] = fit_card
        trace.step(
            "create_fit_card",
            inputs=f"item.id={selected_item.get('id')}, outfit={outfit}",
            returned=fit_card,
        )
        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
