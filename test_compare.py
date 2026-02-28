"""Compare CEA analysis results against raw Gemini API call.

Usage:
    python test_compare.py

Requires:
    - CEA server running at http://localhost:8000
    - GEMINI_API_KEY in .env or environment
"""

import json
import os
import threading
import time

import requests
import socketio
from dotenv import load_dotenv

load_dotenv()

CEA_BASE = "http://localhost:8000"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_KEY = os.environ.get("ACCESS_TOKEN", "")
GEMINI_MODEL = os.environ.get("MODEL_ID", "gemini-2.5-flash")

# Read test file
TEST_FILE = "test.adoc"
with open(TEST_FILE, encoding="utf-8") as f:
    test_content = f.read()


def test_raw_gemini():
    """Send the raw text to Gemini with our system prompt and print results."""
    print("=" * 70)
    print("RAW GEMINI ANALYSIS")
    print("=" * 70)

    system_prompt = (
        "Technical documentation editor (IBM Style, Red Hat Supplementary, "
        "accessibility, modular docs). Analyze text for judgment-based "
        "editorial issues only.\n\n"
        "CHECK: comma splices, run-on sentences, semicolons, colons, "
        "unclear pronouns, complex sentence structure, inconsistent tone, "
        "wordiness, anthropomorphism (attributing human actions to software/"
        "systems — e.g. 'the system wants' or 'the system applies'), "
        "missing punctuation at end of list items or prerequisites.\n\n"
        "SKIP (deterministic rules handle these): word substitutions, "
        "spelling, banned terms, number formatting, known punctuation.\n\n"
        "SKIP (standard technical writing): 'placeholder' text, CLI/code "
        "references, imperative instructions, product names, short procedure "
        "steps, technical jargon, colons introducing lists/steps/code blocks, "
        "state-of-being constructions (is installed, is configured, was fixed, "
        "was added, was detected).\n\n"
        "Be conservative: only flag clear improvements. If in doubt, "
        "don't flag. Fewer high-quality issues over many marginal ones.\n\n"
        "Respond with a JSON array. Each object:\n"
        '{"flagged_text":"exact span","message":"explanation",'
        '"suggestions":["fix"],"severity":"low|medium|high",'
        '"category":"style|grammar|punctuation|audience",'
        '"sentence":"full sentence","sentence_index":0,"confidence":0.8}\n\n'
        "No issues → []. Return ONLY JSON, no additional text."
    )

    payload = {
        "model": GEMINI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"## Document Type: procedure\n\n## Text Block\n\n```\n{test_content}\n```"},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_KEY}",
    }

    resp = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=120)
    if resp.status_code != 200:
        print(f"ERROR: Gemini returned {resp.status_code}")
        print(resp.text[:500])
        return []

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
        # Handle wrapped responses (Gemini sometimes wraps in an object)
        if isinstance(parsed, dict):
            for key in ("issues", "results", "items", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Maybe it's a single issue dict
                if "flagged_text" in parsed:
                    parsed = [parsed]
                else:
                    print("WARNING: Gemini returned dict but no known list key")
                    print(json.dumps(parsed, indent=2)[:500])
                    return []
        issues = parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse Gemini response as JSON: {e}")
        print(content[:500])
        return []

    print(f"\nFound {len(issues)} issues:\n")
    for i, issue in enumerate(issues, 1):
        flagged = issue.get("flagged_text", "?")
        msg = issue.get("message", "?")
        sev = issue.get("severity", "?")
        cat = issue.get("category", "?")
        conf = issue.get("confidence", "?")
        print(f"  {i}. [{sev}/{cat}] (conf={conf})")
        print(f"     Flagged: {flagged[:100]}")
        print(f"     Message: {msg[:120]}")
        suggestions = issue.get("suggestions", [])
        if suggestions:
            print(f"     Suggestion: {suggestions[0][:100]}")
        print()

    return issues


def test_cea_with_websocket():
    """Send text to CEA via Socket.IO and capture ALL phases."""
    print("=" * 70)
    print("CEA ANALYSIS (via Socket.IO)")
    print("=" * 70)

    # Shared state between threads
    result = {
        "det_issues": [],
        "llm_granular_issues": [],
        "llm_global_issues": [],
        "final_issues": [],
        "done": threading.Event(),
        "session_id": None,
        "score": None,
        "events": [],
    }

    sio = socketio.Client()

    @sio.event
    def connect():
        print("  [WS] Connected")

    @sio.event
    def disconnect():
        print("  [WS] Disconnected")

    @sio.on("deterministic_complete")
    def on_det_complete(data):
        issues = data.get("issues", [])
        result["det_issues"] = issues
        result["session_id"] = data.get("session_id")
        print(f"  [WS] deterministic_complete: {len(issues)} issues")

    @sio.on("llm_granular_complete")
    def on_llm_granular(data):
        issues = data.get("issues", [])
        result["llm_granular_issues"] = issues
        print(f"  [WS] llm_granular_complete: {len(issues)} issues")

    @sio.on("llm_global_complete")
    def on_llm_global(data):
        issues = data.get("issues", [])
        result["llm_global_issues"] = issues
        print(f"  [WS] llm_global_complete: {len(issues)} issues")

    @sio.on("analysis_complete")
    def on_analysis_complete(data):
        issues = data.get("issues", [])
        result["final_issues"] = issues
        result["score"] = data.get("score")
        print(f"  [WS] analysis_complete: {len(issues)} final merged issues")
        result["done"].set()

    @sio.on("llm_skipped")
    def on_llm_skipped(data):
        print(f"  [WS] llm_skipped: {data}")
        result["events"].append(("llm_skipped", data))

    @sio.on("progress")
    def on_progress(data):
        stage = data.get("stage", "?")
        msg = data.get("message", "")
        pct = data.get("percent", 0)
        print(f"  [WS] progress: {stage} - {msg} ({pct}%)")

    # Connect via Socket.IO
    print("\nConnecting to CEA via Socket.IO...")
    sio.connect(CEA_BASE)

    # Send analysis via HTTP (Socket.IO events will come back)
    print("Sending analysis request via HTTP...")
    resp = requests.post(
        f"{CEA_BASE}/api/v1/analyze",
        json={"text": test_content, "content_type": "procedure"},
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"ERROR: CEA returned {resp.status_code}")
        print(resp.text[:500])
        sio.disconnect()
        return []

    data = resp.json()
    if not data.get("success"):
        print(f"ERROR: CEA returned success=false")
        sio.disconnect()
        return []

    session_id = data.get("session_id")
    initial_issues = data.get("issues", [])
    partial = data.get("partial", False)

    print(f"\nHTTP response:")
    print(f"  Session: {session_id}")
    print(f"  Partial: {partial}")
    print(f"  Initial issues: {len(initial_issues)}")

    if partial:
        print("\nWaiting for LLM phases via WebSocket...")
        completed = result["done"].wait(timeout=120)
        if not completed:
            print("WARNING: Timed out waiting for analysis_complete event")
    else:
        result["final_issues"] = initial_issues

    sio.disconnect()

    # Print results
    final = result["final_issues"]
    det_count = len([i for i in final if i.get("source") != "llm"])
    llm_count = len([i for i in final if i.get("source") == "llm"])

    print(f"\n{'=' * 50}")
    print(f"FINAL CEA RESULTS")
    print(f"{'=' * 50}")
    print(f"Total issues: {len(final)}")
    print(f"  Deterministic: {det_count}")
    print(f"  LLM: {llm_count}")

    if result["score"]:
        print(f"  Score: {result['score'].get('score', '?')}")

    print(f"\nAll issues:\n")
    for i, issue in enumerate(final, 1):
        flagged = issue.get("flagged_text", "?")
        msg = issue.get("message", "?")
        sev = issue.get("severity", "?")
        cat = issue.get("category", "?")
        rule = issue.get("rule_name", "?")
        source = issue.get("source", "?")
        conf = issue.get("confidence", "?")
        span = issue.get("span", [])
        print(f"  {i}. [{sev}/{cat}] ({source}) rule={rule} conf={conf} span={span}")
        print(f"     Flagged: {flagged[:100]}")
        print(f"     Message: {msg[:120]}")
        suggestions = issue.get("suggestions", [])
        if suggestions:
            print(f"     Suggestion: {suggestions[0][:100]}")
        print()

    return final


def compare_results(gemini_issues, cea_issues):
    """Compare Gemini and CEA issue sets."""
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\nRaw Gemini issues: {len(gemini_issues)}")
    print(f"CEA total issues: {len(cea_issues)}")

    cea_det = [i for i in cea_issues if i.get("source") != "llm"]
    cea_llm = [i for i in cea_issues if i.get("source") == "llm"]
    print(f"  CEA deterministic: {len(cea_det)}")
    print(f"  CEA LLM: {len(cea_llm)}")

    # Find Gemini issues not covered by CEA
    print(f"\n--- Gemini issues NOT found in CEA ---")
    gemini_flagged = set()
    for g in gemini_issues:
        gf = g.get("flagged_text", "").strip()
        gemini_flagged.add(gf)

    cea_flagged = set()
    for c in cea_issues:
        cf = c.get("flagged_text", "").strip()
        cea_flagged.add(cf)

    missing_count = 0
    for g in gemini_issues:
        gf = g.get("flagged_text", "").strip()
        # Check if any CEA issue covers similar text
        found = False
        for cf in cea_flagged:
            if gf in cf or cf in gf or (len(gf) > 10 and gf[:20] in cf):
                found = True
                break
        if not found:
            missing_count += 1
            print(f"  MISSING: [{g.get('severity')}/{g.get('category')}] {gf[:80]}")
            print(f"           {g.get('message', '')[:100]}")

    print(f"\nTotal Gemini issues missing from CEA: {missing_count}/{len(gemini_issues)}")

    # Find CEA extras not in Gemini
    print(f"\n--- CEA issues NOT found in Gemini ---")
    extra_count = 0
    for c in cea_issues:
        cf = c.get("flagged_text", "").strip()
        found = False
        for gf in gemini_flagged:
            if cf in gf or gf in cf or (len(cf) > 10 and cf[:20] in gf):
                found = True
                break
        if not found:
            extra_count += 1
            src = c.get("source", "?")
            print(f"  EXTRA ({src}): [{c.get('severity')}/{c.get('category')}] {cf[:80]}")
            print(f"                {c.get('message', '')[:100]}")

    print(f"\nTotal CEA extras not in Gemini: {extra_count}/{len(cea_issues)}")


def main():
    # Run raw Gemini first
    gemini_issues = test_raw_gemini()

    print("\n")

    # Run CEA with WebSocket to capture all phases
    cea_issues = test_cea_with_websocket()

    # Compare
    compare_results(gemini_issues, cea_issues)


if __name__ == "__main__":
    main()
