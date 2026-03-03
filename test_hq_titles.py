import asyncio
from app.scrapers.hqporner.scraper import list_videos, fetch_html

async def test_url(name, url):
    print(f"Testing {name}: {url}")
    v1 = await list_videos(url, 1)
    v2 = await list_videos(url, 2)
    print(f"{name} Page 1 length: {len(v1)}")
    print(f"{name} Page 2 length: {len(v2)}")
    if len(v1) > 0 and len(v2) > 0:
        duplicates = sum(1 for item in v2 if any(o['url'] == item['url'] for o in v1))
        print(f"{name} Duplicates in Page 2: {duplicates}")
    print("-" * 40)

async def test():
    urls = [
        ("Home", "https://hqporner.com/"),
        ("Top", "https://hqporner.com/top"),
        ("Amateur", "https://hqporner.com/category/Amateur")
    ]
    for name, url in urls:
        await test_url(name, url)

asyncio.run(test())
