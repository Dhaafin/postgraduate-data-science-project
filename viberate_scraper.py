"""
Viberate Top Artists Scraper

Scrapes the list of top artists from Indonesia on Viberate's music chart page.
Uses requests for HTTP and BeautifulSoup for HTML parsing. Artist names are
deduplicated while maintaining their original chart order.

Target URL: https://www.viberate.com/music-charts/top-artists-from-indonesia-0/
"""

import sys
import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://www.viberate.com/music-charts/top-artists-from-indonesia-0/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url: str) -> BeautifulSoup:
    """
    Fetch a web page and return a BeautifulSoup parse tree.

    Args:
        url: The URL to fetch.

    Returns:
        A BeautifulSoup object representing the parsed HTML.

    Raises:
        requests.HTTPError: If the HTTP response indicates an error status.
        requests.RequestException: For other network-related failures.
    """
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_artist_names(soup: BeautifulSoup) -> list[str]:
    """
    Extract unique artist names from the parsed Viberate chart page.

    Artist anchor tags link to paths matching '/artist/<slug>/'.
    Each artist appears twice in the DOM (heading + body), so a seen-set
    is used to yield each name exactly once in chart order.

    Args:
        soup: A BeautifulSoup parse tree of the Viberate chart page.

    Returns:
        An ordered list of unique artist name strings.
    """
    seen: set[str] = set()
    artists: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href: str = anchor["href"]

        if not href.startswith("/artist/"):
            continue

        name = anchor.get_text(strip=True)
        if not name or name in seen:
            continue

        seen.add(name)
        artists.append(name)

    return artists


def main() -> None:
    """
    Entry point. Fetches the Viberate chart and prints each artist name.
    """
    print(f"Fetching: {TARGET_URL}\n")

    try:
        soup = fetch_page(TARGET_URL)
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        sys.exit(1)

    artists = extract_artist_names(soup)

    if not artists:
        print("No artists found. The page structure may have changed.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(artists)} artists:\n")
    for rank, name in enumerate(artists, start=1):
        print(f"  {rank:>3}. {name}")


if __name__ == "__main__":
    main()
