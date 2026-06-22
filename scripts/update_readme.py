#!/usr/bin/env python3
"""Fetch GitHub stats and render a terminal-style profile README."""

import os
import requests

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


def load_art():
    art_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "ascii",
        "cat.txt",
    )
    with open(art_path) as f:
        lines = [line.rstrip() for line in f]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def render_box(commits, stars, top_langs, art):
    art_w = max(len(line) for line in art)
    LPAD = 2
    GAP = 4

    BAR_W = 14
    lang_rows = []
    for name, pct in top_langs:
        filled = round(pct / 100 * BAR_W)
        bar = "=" * filled + "-" * (BAR_W - filled)
        lang_rows.append(f"[{bar}] {name:<12s} {pct:>3d}%")
    data_w = max(len(line) for line in lang_rows)

    right = []
    right.append("isneru")
    right.append("\u2500" * data_w)
    for label, val in [("commits", commits), ("stars", stars)]:
        formatted = f"{val:,}"
        right.append(f"{label}{formatted:>{data_w - len(label)}}")
    right.append("")
    right.append("languages")
    right.extend(lang_rows)

    right_w = max(len(line) for line in right)
    W = LPAD + art_w + GAP + right_w + 2

    total_lines = max(len(art), len(right))
    art_off = (total_lines - len(art)) // 2
    right_off = (total_lines - len(right)) // 2

    lines = []
    lines.append("\u256d" + "\u2500" * W + "\u256e")
    lines.append("\u2502" + " " * W + "\u2502")

    for i in range(total_lines):
        art_part = art[i - art_off] if art_off <= i < art_off + len(art) else ""
        right_part = (
            right[i - right_off] if right_off <= i < right_off + len(right) else ""
        )
        inner = " " * LPAD + art_part.ljust(art_w) + " " * GAP + right_part
        inner = inner.ljust(W)
        lines.append("\u2502" + inner + "\u2502")

    lines.append("\u2502" + " " * W + "\u2502")
    lines.append("\u2570" + "\u2500" * W + "\u256f")

    return "\n".join(lines)


def main():
    commits, stars, top_langs = fetch_stats()
    art = load_art()
    box = render_box(commits, stars, top_langs, art)

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
