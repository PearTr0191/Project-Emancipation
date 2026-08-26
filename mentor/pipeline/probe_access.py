"""Probe which anonymous Instagram access routes still work (Aug 2026)."""

from __future__ import annotations

import json
import re

import requests

TARGET = "ultimateivyleagueguide"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "Sec-Fetch-Mode": "navigate",
}


def main() -> None:
    s = requests.Session()
    s.headers.update(HEADERS)

    print("=== probe 1: profile HTML page ===")
    r = s.get(f"https://www.instagram.com/{TARGET}/", timeout=30)
    print("status:", r.status_code, "bytes:", len(r.text))
    markers = [
        '"user_id"',
        "ProfilePage",
        "xdt_api__v1__feed__user_timeline_graphql_connection",
        "edge_owner_to_timeline_media",
        '"shortcode"',
        "LoginAndSignupPage",
        "request_full_access",
    ]
    for m in markers:
        print(f"  {m!r}: {m in r.text}")

    uid_match = re.search(r'"user_id":"(\d+)"', r.text)
    print("user_id found:", uid_match.group(1) if uid_match else None)

    sc_matches = re.findall(r'"shortcode":"([A-Za-z0-9_-]+)"', r.text)
    print("shortcodes in HTML:", len(set(sc_matches)), sorted(set(sc_matches))[:15])

    cap_count = r.text.count('"caption"') + r.text.count("caption{")
    print("caption mentions:", cap_count)

    print("\n=== probe 2: web_profile_info endpoint ===")
    r2 = s.get(
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={TARGET}",
        headers={**HEADERS, "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Referer": f"https://www.instagram.com/{TARGET}/"},
        timeout=30,
    )
    print("status:", r2.status_code, "body head:", r2.text[:200])

    if uid_match:
        print("\n=== probe 3: anonymous feed/user chunks endpoint ===")
        r3 = s.get(
            f"https://www.instagram.com/api/v1/feed/user/{uid_match.group(1)}/?count=33",
            headers={**HEADERS, "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Referer": f"https://www.instagram.com/{TARGET}/"},
            timeout=30,
        )
        print("status:", r3.status_code, "body head:", r3.text[:200])

        print("\n=== probe 4: graphql PolarisProfileContentContainer ===")
        variables = json.dumps({"id": uid_match.group(1), "first": 50, "after": None})
        r4 = s.post(
            "https://www.instagram.com/graphql/query",
            params={"query_hash": "003056d32c2554def87228bc3ca9a78f", "variables": variables},
            headers={**HEADERS, "Accept": "*/*", "Referer": f"https://www.instagram.com/{TARGET}/"},
            timeout=30,
        )
        print("status:", r4.status_code, "body head:", r4.text[:300])

        print("\n=== probe 5: graphql doc_id (PolarisProfilePostsQuery) ===")
        r5 = s.post(
            "https://www.instagram.com/graphql/query",
            data={
                "av": "0",
                "__d": "www",
                "__user": "0",
                "lsd": "AVqbxe3J_YA",
                "variables": json.dumps({"data": {"context_key": "username:" + TARGET, "include_reel": True, "fetch_media_count": 50}}),
                "doc_id": "9510064595728286",
            },
            headers={**HEADERS, "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded", "Referer": f"https://www.instagram.com/{TARGET}/", "X-FB-LSD": "AVqbxe3J_YA"},
            timeout=30,
        )
        print("status:", r5.status_code, "body head:", r5.text[:300])


if __name__ == "__main__":
    main()
