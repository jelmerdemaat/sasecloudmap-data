#!/usr/bin/env -S uv run
import argparse
import sys

import httpx
from utils.base import convert_to_geojson
from utils.http_config import http_request_kwargs
from utils.output import write_geojson_output
from utils.post_data import write_and_post
from utils.skeleton import geojson_skeleton

AKAMAI_NETWORK_MAP_URL = "https://www.akamai.com/site/en.linode-network-map.json"

AKAMAI_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def get_data():
    """Fetch Akamai Linode network locations and return location records."""
    resp = httpx.get(
        AKAMAI_NETWORK_MAP_URL,
        headers=AKAMAI_REQUEST_HEADERS,
        **http_request_kwargs(),
    )
    resp.raise_for_status()
    data = resp.json()

    locations = []
    seen = set()

    for location_type in ("core", "distributed", "edge"):
        for loc in data.get(location_type, []):
            name = loc.get("name", "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            locations.append(
                {
                    "name": name,
                    "coordinates": [loc["latitude"], loc["longitude"]],
                }
            )

    return locations


if __name__ == "__main__":
    provider_name = "akamai"
    friendly_name = "Akamai"
    app_type = ["cdn"]

    parser = argparse.ArgumentParser(
        description="Update dev, prod or both environments."
    )
    parser.add_argument("--refresh", action="store_true", help="refresh from source")
    parser.add_argument("--dev", action="store_true", help="Update dev environment")
    parser.add_argument("--prod", action="store_true", help="Update prod environment")
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()

    if args.refresh:
        output = get_data()
        geojson = convert_to_geojson(output)
        geojson_data = geojson_skeleton(geojson)

        write_geojson_output(provider_name, geojson_data)

    write_and_post(
        provider_name,
        friendly_name,
        app_type,
        update_dev=args.dev,
        update_prod=args.prod,
    )
