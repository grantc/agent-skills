#!/usr/bin/env python3
"""
Analyze readiness of portfolio items for closing.

Cross-references subfeatures with their children to determine which items
have all children closed and are ready to close.

Usage:
    python3 analyze_readiness.py --subfeatures subfeatures.json --children children.json --output report.json
"""
import argparse
import json
import sys
from datetime import date


EFFECTIVELY_DONE_STATUSES = {"done", "not doing"}


def is_effectively_done(child):
    """A child is effectively done if formally Closed OR has a terminal status.

    This is broader than just checking AssetState==128 (Closed). Many teams mark
    items as Done without formally closing them. We consider a child effectively
    done if:
    - AssetState is Closed (128), OR
    - Status is "Done" or "DONE" (case-insensitive), OR
    - Status is "Not Doing"
    """
    if child["asset_state_code"] == 128:
        return True
    status = (child.get("status") or "").strip().lower()
    return status in EFFECTIVELY_DONE_STATUSES


def main():
    parser = argparse.ArgumentParser(description="Analyze portfolio item readiness for closing")
    parser.add_argument("--subfeatures", required=True, help="Subfeatures JSON file (from fetch_subfeatures.py)")
    parser.add_argument("--children", required=True, help="Children JSON file (from fetch_children.py)")
    parser.add_argument("-o", "--output", required=True, help="Output report JSON file")
    args = parser.parse_args()

    with open(args.subfeatures) as f:
        sf_data = json.load(f)
    with open(args.children) as f:
        ch_data = json.load(f)

    items = sf_data["items"]
    children = ch_data["children"]

    # Group children by parent
    children_by_parent = {}
    for c in children:
        pn = c["parent_number"]
        if pn not in children_by_parent:
            children_by_parent[pn] = []
        children_by_parent[pn].append(c)

    # Analyze each item
    analysis = []
    counts = {
        "already_closed": 0,
        "all_children_closed": 0,
        "all_children_effectively_done": 0,
        "has_open_children": 0,
        "no_children": 0,
        "total": len(items),
    }

    for item in items:
        item_children = children_by_parent.get(item["number"], [])
        total = len(item_children)
        closed = sum(1 for c in item_children if c["asset_state_code"] == 128)
        effectively_done = sum(1 for c in item_children if is_effectively_done(c))
        active = sum(1 for c in item_children if c["asset_state_code"] == 64)
        stories = [c for c in item_children if c["type"] == "Story"]
        defects = [c for c in item_children if c["type"] == "Defect"]

        is_already_closed = item["asset_state_code"] == 128
        all_formally_closed = total > 0 and closed == total
        all_effectively_done = total > 0 and effectively_done == total

        # Children that are NOT effectively done (truly open work)
        open_children = [
            {
                "number": c["number"],
                "name": c["name"],
                "type": c["type"],
                "status": c["status"],
                "asset_state": c["asset_state"],
            }
            for c in item_children
            if not is_effectively_done(c)
        ]

        if is_already_closed:
            counts["already_closed"] += 1
            disposition = "already_closed"
        elif all_formally_closed:
            counts["all_children_closed"] += 1
            disposition = "all_children_closed"
        elif all_effectively_done:
            counts["all_children_effectively_done"] += 1
            disposition = "all_children_effectively_done"
        elif total == 0:
            counts["no_children"] += 1
            disposition = "no_children"
        else:
            counts["has_open_children"] += 1
            disposition = "has_open_children"

        entry = {
            "number": item["number"],
            "name": item["name"],
            "oid": item["oid"],
            "oid_num": item["oid_num"],
            "status": item["status"],
            "asset_state": item["asset_state"],
            "asset_state_code": item["asset_state_code"],
            "team": item["team"],
            "owners": item["owners"],
            "total_children": total,
            "total_stories": len(stories),
            "total_defects": len(defects),
            "closed_children": closed,
            "effectively_done_children": effectively_done,
            "active_children": active,
            "all_formally_closed": all_formally_closed,
            "all_effectively_done": all_effectively_done,
            "disposition": disposition,
            "open_children": open_children,
            "url": item["url"],
        }
        analysis.append(entry)

    # Sort: all_children_closed first, then effectively_done, then open, then no_children, then already_closed
    disposition_order = {
        "all_children_closed": 0,
        "all_children_effectively_done": 1,
        "has_open_children": 2,
        "no_children": 3,
        "already_closed": 4,
    }
    analysis.sort(key=lambda x: (disposition_order.get(x["disposition"], 99), x["number"]))

    result = {
        "query": {
            "subfeatures_file": args.subfeatures,
            "children_file": args.children,
            "generated_at": str(date.today()),
            "scope": sf_data["query"]["scope"],
            "category": sf_data["query"]["category"],
        },
        "counts": counts,
        "analysis": analysis,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"Planning Level Cleanup Report: {sf_data['query']['scope']}")
    print(f"Category: {sf_data['query']['category']}")
    print(f"{'=' * 60}")
    print(f"Total items:                     {counts['total']}")
    print(f"Already closed:                  {counts['already_closed']}")
    print(f"All children formally closed:    {counts['all_children_closed']}")
    print(f"All children effectively done:   {counts['all_children_effectively_done']}")
    print(f"Has open children:               {counts['has_open_children']}")
    print(f"No children:                     {counts['no_children']}")
    print()

    ready_close = [a for a in analysis if a["disposition"] == "all_children_closed"]
    if ready_close:
        print(f"ALL CHILDREN FORMALLY CLOSED - Ready to Inactivate ({len(ready_close)}):")
        print(f"{'-' * 60}")
        for a in ready_close:
            team = a["team"] or "No Team"
            owners = a["owners"] or "No Owner"
            print(f"  {a['number']:8s} | {a['status'] or 'None':<12s} | {team:<16s} | {owners}")
            print(f"           {a['name']}")
            print(f"           Children: {a['total_stories']}S + {a['total_defects']}D = {a['total_children']} (all closed)")
        print()

    eff_done = [a for a in analysis if a["disposition"] == "all_children_effectively_done"]
    if eff_done:
        print(f"ALL CHILDREN EFFECTIVELY DONE - Ready for Completed status ({len(eff_done)}):")
        print(f"{'-' * 60}")
        for a in eff_done:
            team = a["team"] or "No Team"
            owners = a["owners"] or "No Owner"
            done_but_open = a["effectively_done_children"] - a["closed_children"]
            print(f"  {a['number']:8s} | {a['status'] or 'None':<12s} | {team:<16s} | {owners}")
            print(f"           {a['name']}")
            print(f"           Children: {a['total_children']} total, {a['closed_children']} closed, {done_but_open} done-but-open")
        print()

    open_items = [a for a in analysis if a["disposition"] == "has_open_children"]
    if open_items:
        print(f"HAS OPEN CHILDREN ({len(open_items)}):")
        print(f"{'-' * 60}")
        for a in open_items:
            open_count = len(a["open_children"])
            print(f"  {a['number']:8s} | {a['name'][:50]}")
            print(f"           {a['effectively_done_children']}/{a['total_children']} effectively done, {open_count} truly open")

    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
