#!/usr/bin/env python3
"""
Automated Google Scholar Citation Updater
Fetches live metrics from Syed Shubha's public Google Scholar profile and syncs:
- data/portfolio_data.json
- data/portfolio_data.js
- index.html (fallback values)
- README.md (badges and text)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

SCHOLAR_USER_ID = "8EK8VJMAAAAJ"
SCHOLAR_URL = f"https://scholar.google.com/citations?user={SCHOLAR_USER_ID}&hl=en"

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON_PATH = os.path.join(REPO_DIR, "data", "portfolio_data.json")
DATA_JS_PATH = os.path.join(REPO_DIR, "data", "portfolio_data.js")
INDEX_HTML_PATH = os.path.join(REPO_DIR, "index.html")
README_PATH = os.path.join(REPO_DIR, "README.md")


def fetch_scholar_metrics():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(SCHOLAR_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"[WARN] Network error fetching Google Scholar: {e}")
        return None

    matches = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
    if len(matches) < 6:
        print(f"[WARN] Unexpected HTML response (found {len(matches)} metric cells). Possible CAPTCHA or format change.")
        return None

    try:
        citations = int(matches[0])
        h_index = int(matches[2])
        i10_index = int(matches[4])
    except ValueError:
        print("[WARN] Could not parse integer values from cells.")
        return None

    return {
        "citations": citations,
        "h_index": h_index,
        "i10_index": i10_index,
    }


def update_data_files(metrics):
    if not os.path.exists(DATA_JSON_PATH):
        print(f"[ERR] File not found: {DATA_JSON_PATH}")
        return False

    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = data.setdefault("profile", {})
    metrics_list = profile.setdefault("metrics", [])

    old_citations = None
    old_h = None
    old_i10 = None

    for m in metrics_list:
        lbl = m.get("label", "").lower()
        if "citations" in lbl:
            old_citations = m.get("value")
            m["value"] = str(metrics["citations"])
        elif "h-index" in lbl:
            old_h = m.get("value")
            m["value"] = str(metrics["h_index"])
        elif "i10-index" in lbl:
            old_i10 = m.get("value")
            m["value"] = str(metrics["i10_index"])

    changed = (
        str(old_citations) != str(metrics["citations"])
        or str(old_h) != str(metrics["h_index"])
        or str(old_i10) != str(metrics["i10_index"])
    )

    if not changed:
        print(f"[INFO] No changes detected. Citations: {metrics['citations']}, h-index: {metrics['h_index']}, i10-index: {metrics['i10_index']}")
        return False

    # Safety check: avoid resetting to lower numbers due to temporary glitch
    if old_citations and old_citations.isdigit() and metrics["citations"] < int(old_citations):
        print(f"[WARN] Parsed citations ({metrics['citations']}) is lower than existing ({old_citations}). Skipping update for safety.")
        return False

    # Save portfolio_data.json
    json_text = json.dumps(data, indent=2, ensure_ascii=False)
    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        f.write(json_text + "\n")

    # Save portfolio_data.js
    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write("window.PORTFOLIO_DATA = " + json_text + ";\n")

    print(
        f"[OK] Updated data files: "
        f"Citations: {old_citations} -> {metrics['citations']}, "
        f"h-index: {old_h} -> {metrics['h_index']}, "
        f"i10-index: {old_i10} -> {metrics['i10_index']}"
    )
    return True


def update_index_html(metrics):
    if not os.path.exists(INDEX_HTML_PATH):
        return

    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Update static metric cards in index.html
    html_new = re.sub(
        r'(<div class="impact-metric-val">)\d+(</div>\s*<div class="impact-metric-lbl">Citations \(Google Scholar ↗\)</div>)',
        rf'\g<1>{metrics["citations"]}\g<2>',
        html,
    )
    html_new = re.sub(
        r'(<div class="impact-metric-val">)\d+(</div>\s*<div class="impact-metric-lbl">h-index \(Google Scholar ↗\)</div>)',
        rf'\g<1>{metrics["h_index"]}\g<2>',
        html_new,
    )
    html_new = re.sub(
        r'(<div class="impact-metric-val">)\d+(</div>\s*<div class="impact-metric-lbl">i10-index \(Google Scholar ↗\)</div>)',
        rf'\g<1>{metrics["i10_index"]}\g<2>',
        html_new,
    )

    if html_new != html:
        with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html_new)
        print("[OK] Updated static metrics in index.html")


def update_readme(metrics):
    if not os.path.exists(README_PATH):
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content_new = re.sub(
        r'Google_Scholar-\d+_Citations',
        f'Google_Scholar-{metrics["citations"]}_Citations',
        content,
    )
    content_new = re.sub(
        r'Live citation metrics \(\d+ citations, h-index \d+, i10-index \d+\)',
        f'Live citation metrics ({metrics["citations"]} citations, h-index {metrics["h_index"]}, i10-index {metrics["i10_index"]})',
        content_new,
    )

    if content_new != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content_new)
        print("[OK] Updated metrics in README.md")


def main():
    print("[*] Checking Google Scholar metrics for Syed Shubha...")
    metrics = fetch_scholar_metrics()
    if not metrics:
        print("[*] Could not retrieve fresh metrics. Exiting gracefully without modifications.")
        sys.exit(0)

    changed = update_data_files(metrics)
    if changed:
        update_index_html(metrics)
        update_readme(metrics)
        print("[SUCCESS] All files updated successfully.")
    else:
        print("[*] Repository already has latest citation counts.")


if __name__ == "__main__":
    main()
