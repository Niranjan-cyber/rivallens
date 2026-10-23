"""Milestone 1 (first useful insight): from what a business has collected, the setup steps, what data is covered or missing,
the findings the data actually supports (each with its evidence) and the one next action. Pure, so it is tested without a DB."""

LIKE_FOR_LIKE = 3  # fewer comparable prices than this is not a market median
SHORT_RUNWAY = 6   # months
SUSPECT_GAP = 60   # % from the median: more likely a different size or pack than a real price gap


def _inr(x: float) -> str:
    return f"₹{x:,.0f}"


def _act(label: str, href: str | None = None, kind: str = "link", **extra) -> dict:
    return {"label": label, "href": href, "kind": kind, **extra}


def _steps(s: dict, base: str) -> list[dict]:
    card, products, disc, comp, mon = s["card"], s["products"], s["discovery"], s["competitors"], s["monitoring"]
    out = []

    missing = [w for w, k in (("who your customers are", "target_customer"), ("where you sell", "markets")) if not card.get(k)]
    out.append({"key": "business", "title": "Your business and target market",
                "status": "todo" if missing else "done",
                "detail": f"Add {' and '.join(missing)}: competitors are judged against them." if missing
                          else f"Customers: {card['target_customer']}. Where: {', '.join(card['markets'])}.",
                "action": _act("Edit business card", f"{base}/card")})

    unpriced = [p for p in products if p["price"] is None]
    uncategorised = [p for p in products if not p["category_path"]]
    if not products:
        st = {"status": "todo", "detail": "Add what you sell, so it can be compared with the same products.", "action": _act("Add a product", f"{base}/product")}
    elif unpriced:
        p = unpriced[0]
        st = {"status": "todo", "detail": f"Add the price of {p['name']}: without it we can't place it against the market.",
              "action": _act(f"Add the price of {p['name']}", kind="price", product_id=p["id"], product=p["name"], unit=p["unit"])}
    elif uncategorised:
        p = uncategorised[0]
        st = {"status": "done", "detail": f"{p['name']} has no product category, so it can't be compared. Pick one if one fits.",
              "action": _act("Choose a category", f"{base}/product-detail?id={p['id']}")}
    else:
        st = {"status": "done", "detail": f"{len(products)} product{'s' if len(products) > 1 else ''}, each priced and in an exact category.",
              "action": _act("Open products", f"{base}/product")}
    out.append({"key": "products", "title": "Your products and prices"} | st)

    if comp["selected"]:
        st = {"status": "done", "detail": f"{comp['selected']} competitor{'s' if comp['selected'] > 1 else ''} selected to watch.",
              "action": _act("Review competitors", f"{base}/competitors")}
    elif disc and disc["status"] in ("queued", "running"):
        st = {"status": "running", "detail": "Searching the web and checking each site…", "action": _act("Finding competitors", kind="wait")}
    elif disc and disc["status"] in ("failed", "stale"):
        st = {"status": "blocked", "detail": f"The search stopped: {disc.get('error') or 'unknown error'}. Try again, or add a competitor by URL.",
              "action": _act("Add a competitor by URL", f"{base}/competitors")}
    elif disc and disc["status"] == "done" and not disc["verified"]:
        why = "; ".join(disc["reasons"][:3]) or "none passed the checks"
        st = {"status": "blocked", "detail": f"We checked {disc['rejected']} sites and none passed (reachable, robots.txt allows it, sells in India): {why}. "
                                              "Add one you know by URL.", "action": _act("Add a competitor by URL", f"{base}/competitors")}
    elif comp["total"]:
        st = {"status": "todo", "detail": "Competitors were found but none is selected to watch.", "action": _act("Choose competitors", f"{base}/competitors")}
    else:
        st = {"status": "todo", "detail": "We search the web for Indian competitors and keep only sites we can verify.",
              "action": _act("Find competitors", kind="discover")}
    out.append({"key": "competitors", "title": "Competitors in India"} | st)

    cat = [p for p in products if p["category_path"]]
    good = [p for p in cat if p["like_for_like"] >= LIKE_FOR_LIKE]
    if not cat:
        st = {"status": "blocked", "detail": "Needs a product with a category first.", "action": None}
    elif good:
        st = {"status": "done", "detail": "; ".join(f"{p['name']}: {p['like_for_like']} like-for-like products" for p in good) + ".",
              "action": _act("Compare", f"{base}/product-detail?id={good[0]['id']}")}
    else:
        p = cat[0]
        leaf = p["category_path"].split(" > ")[-1]
        why = (f"{p['broad']} products share the broad category {leaf}, but not {p['niche'] or p['name']}, so we won't compare prices yet. "
               if p["broad"] else "")
        st = {"status": "todo", "detail": f"{why}We read Indian stores' product pages and keep only {(p['niche'] or p['name']).lower()}.",
              "action": _act(f"Find products like {p['name']}", kind="comparables", product_id=p["id"])}
    out.append({"key": "comparables", "title": "Like-for-like products"} | st)

    failed = f" Couldn't read: {', '.join(mon['failed'])} (not counted as changes)." if mon["failed"] else ""
    if not comp["selected"]:
        st = {"status": "blocked", "detail": "Needs at least one competitor.", "action": None}
    elif mon["baseline_at"]:
        st = {"status": "done", "detail": f"Watching since {mon['baseline_at']}; last checked {mon['last_run_at']}.{failed}",
              "action": _act("Open market", f"{base}/dashboard")}
    else:
        st = {"status": "todo", "detail": "Save today's version of each competitor's pricing page, so later changes can be proven.",
              "action": _act("Start watching", kind="monitor")}
    out.append({"key": "monitoring", "title": "Watch competitors' pricing pages"} | st)

    m = s["money"]
    if not m["transactions"]:
        st = {"status": "optional", "detail": "Upload sales and costs (CSV or Excel) to see margin and runway.", "action": _act("Upload", f"{base}/finance")}
    elif not m["has_costs"]:
        st = {"status": "optional", "detail": "Sales are in, but no costs yet, so margin, burn and runway stay unknown.", "action": _act("Add costs", f"{base}/finance")}
    else:
        st = {"status": "done", "detail": f"{m['transactions']} transactions.", "action": _act("Open finance", f"{base}/finance")}
    out.append({"key": "finance", "title": "Your sales and costs"} | st)

    c = s["customers"]
    st = ({"status": "done", "detail": f"{c['total']} reviews and comments.", "action": _act("Open customers", f"{base}/customers")} if c["total"] else
          {"status": "optional", "detail": "Upload reviews or comments to see what customers ask for.", "action": _act("Upload", f"{base}/customers")})
    out.append({"key": "customers", "title": "What customers say"} | st)
    return out


def _findings(s: dict, base: str) -> list[dict]:
    out = []
    m = s["money"]
    if m["has_costs"] and m["runway_months"] is not None and m["runway_months"] < SHORT_RUNWAY:
        out.append({"kind": "runway", "text": f"{m['runway_months']:g} months of runway at your current burn.",
                    "evidence": {"label": "Your uploaded sales and costs", "href": f"{base}/finance"},
                    "action": _act("See which price raises margin", f"{base}/product")})
    r = s["receipt"]
    if r:
        out.append({"kind": "receipt", "text": f"{r['text']} (seen {r['observed_at']}).",
                    "evidence": {"label": "Receipt: the page before and after", "href": f"{base}/receipt?id={r['id']}"},
                    "action": _act("Check your price against it", f"{base}/product")})
    for p in s["products"]:
        pos = p["position"]
        if p["price"] is None or p["like_for_like"] < LIKE_FOR_LIKE or not pos or pos.get("pct_vs_median") is None:
            continue
        pct, href = pos["pct_vs_median"], f"{base}/product-detail?id={p['id']}"
        if abs(pct) > SUSPECT_GAP:  # a slice against whole cakes, a sample against a pack: not a pricing conclusion
            out.append({"kind": "check", "text": f"{p['name']} at {_inr(p['price'])} is far from the median {_inr(pos['median'])} of "
                                                 f"{p['like_for_like']} similar products. They may be a different size or pack, so we draw no conclusion yet.",
                        "evidence": {"label": "The products compared, each with its page", "href": href},
                        "action": _act("Check the products compared", href)})
            continue
        where = "in line with" if abs(pct) < 10 else f"{abs(pct)}% {'below' if pct < 0 else 'above'}"
        action = (_act("Test a higher price in its simulator", href) if pct <= -15 else
                  _act("See what the premium products include", href) if pct >= 15 else _act("Watch for competitor price moves", f"{base}/dashboard"))
        out.append({"kind": "price", "text": f"{p['name']} at {_inr(p['price'])} is {where} the median {_inr(pos['median'])} of "
                                             f"{p['like_for_like']} like-for-like products ({', '.join(p['sources'][:3])}, seen {p['seen']}).",
                    "evidence": {"label": "The products compared, each with its page", "href": href}, "action": action})
    c = s["customers"]["complaint"]
    if c:
        out.append({"kind": "complaint", "text": f"Most common complaint: {c['label']} ({c['count']} mentions).",
                    "evidence": {"label": "The quotes", "href": f"{base}/customers"}, "action": _act("Read what they say", f"{base}/customers")})
    return out


def _coverage(s: dict) -> list[dict]:
    mon, comp = s["monitoring"], s["competitors"]
    market = ("failed", f"{len(mon['failed'])} page{'s' if len(mon['failed']) > 1 else ''} couldn't be read") if mon["failed"] else \
             ("ok", f"{comp['selected']} watched, last checked {mon['last_run_at']}") if mon["baseline_at"] else \
             ("missing", "No competitor pages watched yet")
    good = [p for p in s["products"] if p["like_for_like"] >= LIKE_FOR_LIKE]
    products = ("ok", f"{len(good)} of {len(s['products'])} products have like-for-like prices") if good else \
               ("missing", "No product has enough like-for-like prices for a market median")
    m = s["money"]
    finance = ("ok", f"{m['transactions']} transactions") if m["has_costs"] else \
              ("missing", "Sales only, no costs") if m["transactions"] else ("missing", "Nothing uploaded")
    c = s["customers"]
    customers = ("ok", f"{c['total']} mentions") if c["total"] else ("missing", "Nothing uploaded")
    return [{"area": a, "status": st, "detail": d} for a, (st, d) in
            (("Market", market), ("Products", products), ("Finance", finance), ("Customers", customers))]


def plan(s: dict, base: str) -> dict:
    steps, findings = _steps(s, base), _findings(s, base)
    todo = next((st for st in steps if st["status"] == "todo" and st["action"]), None)
    if todo:
        nxt = todo["action"] | {"key": todo["key"], "why": todo["detail"]}
    elif findings:
        nxt = findings[0]["action"] | {"key": "finding", "why": findings[0]["text"]}
    else:
        opt = next((st for st in steps if st["status"] == "optional"), None)
        nxt = (opt["action"] | {"key": opt["key"], "why": opt["detail"]}) if opt else \
              _act("Check competitors again", f"{base}/dashboard") | {"key": "done", "why": "Everything is set up. Check weekly for changes."}
    return {"steps": steps, "findings": findings, "coverage": _coverage(s), "next_action": nxt,
            "complete": all(st["status"] in ("done", "optional", "blocked") for st in steps if st["key"] not in ("finance", "customers"))}
