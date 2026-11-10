import requests
from bs4 import BeautifulSoup

URL = "https://www.xbox.com/es-MX/games/all-games"


def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def parse_games(html):
    soup = BeautifulSoup(html, "html.parser")
    games = []

    for card in soup.select("a[href*='/games/']"):
        title = card.get_text(strip=True)
        href = card.get("href")
        if title and href:
            games.append({"title": title, "url": href})

    return games


def main():
    html = fetch_page(URL)
    games = parse_games(html)

    print(f"Se encontraron {len(games)} posibles juegos.")
    for game in games[:10]:
        print(f"- {game['title']}: {game['url']}")


if __name__ == "__main__":
    main()
