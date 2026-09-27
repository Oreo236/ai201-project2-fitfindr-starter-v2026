"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

Build and test each tool independently before wiring them into the loop.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import json
import re

import config
from generate import generate
from utils.data_loader import load_listings


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def _matches_size(requested: str, listed: str) -> bool:
    listed_tokens = _tokens(listed)
    alternatives = requested.split("/")
    return any(
        tokens and tokens.issubset(listed_tokens)
        for tokens in (_tokens(alternative) for alternative in alternatives)
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = _tokens(description)
    if not keywords:
        return []

    matches = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _matches_size(size, listing["size"]):
            continue

        searchable_text = " ".join(
            [listing["title"], listing["description"], *listing["style_tags"]]
        )
        score = len(keywords & _tokens(searchable_text))
        if score:
            matches.append((score, listing))

    matches.sort(key=lambda match: match[0], reverse=True)
    return [
        listing
        for _, listing in matches[: config.SEARCH_RESULT_LIMIT]
    ]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    wardrobe_items = wardrobe.get("items") or []
    item_details = json.dumps(new_item, ensure_ascii=False, indent=2)
    wardrobe_details = json.dumps(wardrobe_items, ensure_ascii=False, indent=2)
    title = new_item.get("title", "this item")

    if wardrobe_items:
        system = (
            "You are a practical personal stylist. Suggest one or two concise, "
            "wearable outfits centered on the new item. Use only clothing and "
            "accessories named in the user's wardrobe, and name the pieces you "
            "use. Do not invent item details."
        )
        prompt = (
            f"New item:\n{item_details}\n\n"
            f"Wardrobe items:\n{wardrobe_details}\n\n"
            "Suggest one or two outfits that incorporate the new item."
        )
        fallback = (
            f"Try styling {title} with {wardrobe_items[0].get('name', 'a piece')} "
            "from your wardrobe, then add simple shoes that suit the occasion."
        )
    else:
        system = (
            "You are a practical personal stylist. Give one or two concise, "
            "general styling ideas for the new item. The user has not provided "
            "a wardrobe, so do not imply they own any specific pieces. Do not "
            "invent details about the item."
        )
        prompt = (
            f"New item:\n{item_details}\n\n"
            "The user's wardrobe is empty. Suggest one or two general ways to "
            "style this item without assuming they own particular pieces."
        )
        fallback = (
            f"Build an outfit around {title} with a simple base layer and shoes "
            "that suit its silhouette."
        )

    return generate(prompt, system=system).strip() or fallback


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    title = new_item.get("title", "This item")
    price = new_item.get("price", "an unknown price")
    if isinstance(price, (int, float)):
        price = f"${price:g}"
    else:
        price = str(price)
    platform = new_item.get("platform", "the listing platform")
    listing_sentence = f"{title} is listed for {price} on {platform}."
    outfit_text = outfit.strip()

    if not outfit_text:
        description = new_item.get("description") or (
            f"A {new_item.get('condition', 'pre-owned')} "
            f"{new_item.get('category', 'piece')} with a distinct look."
        )
        return f"{listing_sentence} {description}"

    item_details = json.dumps(new_item, ensure_ascii=False, indent=2)
    system = (
        "Write a genuine, concise social caption for a secondhand fashion find. "
        "Return one 2-4 sentence caption, not a list. Mention the item, its "
        "exact price, and its platform once each. Use the outfit suggestion "
        "and describe the item's vibe specifically. Do not invent listing facts."
    )
    prompt = (
        f"Listing details:\n{item_details}\n\n"
        f"Suggested outfit:\n{outfit_text}\n\n"
        "Write a post-ready caption using the listing facts and outfit above."
    )
    fallback = f"{listing_sentence} Style it with {outfit_text} for a look with a clear point of view."
    return generate(prompt, system=system).strip() or fallback
