#!/usr/bin/env python3
"""Fetch GitHub stats and render a terminal-style profile README."""

import os
import requests
from datetime import datetime

USERNAME = "isneru"
GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
{
  user(login: "%s") {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    repositories(ownerAffiliations: OWNER, first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY % USERNAME},
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()["data"]["user"]

    contrib = data["contributionsCollection"]
    commits = (
        contrib["totalCommitContributions"]
        + contrib["restrictedContributionsCount"]
    )

    stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])

    lang_sizes = {}
    for repo in data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_sizes[name] = lang_sizes.get(name, 0) + edge["size"]

    sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)
    total_size = sum(s for _, s in sorted_langs)

    top_langs = []
    for name, size in sorted_langs[:5]:
        pct = round(size / total_size * 100) if total_size else 0
        top_langs.append((name, pct))

    return commits, stars, top_langs


def render_box(commits, stars, top_langs):
    year = datetime.now().year
    W = 52

    cat = [
        r"  /\_/\  ",
        r" ( o.o ) ",
        r"  > ^ <  ",
        r" /|   |\ ",
        r"(_|   |_)",
    ]
    CAT_W = 9
    GAP = 5

    right = []
    val_w = max(len(f"{commits:,}"), len(f"{stars:,}"))
    stat_w = 28
    right.append("isneru")
    right.append("\u2500" * stat_w)
    for label, val in [(f"commits ({year})", commits), ("stars", stars)]:
        formatted = f"{val:>{val_w},}"
        dots = "\u00b7" * (stat_w - len(label) - 1 - len(formatted) - 1)
        right.append(f"{label} {dots} {formatted}")
    right.append("")
    right.append("languages")

    BAR_W = 14
    for name, pct in top_langs:
        filled = round(pct / 100 * BAR_W)
        bar = "\u2588" * filled + "\u2591" * (BAR_W - filled)
        right.append(f"{bar} {name:<12s} {pct:>3d}%")

    total_lines = max(len(cat), len(right))

    lines = []
    lines.append("\u256d" + "\u2500" * W + "\u256e")
    lines.append("\u2502" + " " * W + "\u2502")

    for i in range(total_lines):
        cat_part = cat[i] if i < len(cat) else " " * CAT_W
        right_part = right[i] if i < len(right) else ""
        inner = "  " + cat_part + " " * GAP + right_part
        inner = inner.ljust(W)
        lines.append("\u2502" + inner + "\u2502")

    lines.append("\u2502" + " " * W + "\u2502")
    lines.append("\u2570" + "\u2500" * W + "\u256f")

    return "\n".join(lines)


def main():
    commits, stars, top_langs = fetch_stats()
    box = render_box(commits, stars, top_langs)

    readme = f"```\n{box}\n```\n"

    readme_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "README.md",
    )
    with open(readme_path, "w") as f:
        f.write(readme)

    print("README.md updated successfully")
    print(box)


if __name__ == "__main__":
    main()
