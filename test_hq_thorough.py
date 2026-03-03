import asyncio
from app.scrapers.hqporner.scraper import list_videos

async def test_section(name, url):
    print(f"--- Testing {name}: {url} ---")
    v1 = await list_videos(url, 1)
    v2 = await list_videos(url, 2)
    print(f"Page 1: {len(v1)} items")
    print(f"Page 2: {len(v2)} items")
    
    if v1 and v2:
        p1_titles = [i['title'] for i in v1[:5]]
        p2_titles = [i['title'] for i in v2[:5]]
        print(f"P1 Top 5: {p1_titles}")
        print(f"P2 Top 5: {p2_titles}")
        
        duplicates = [i['url'] for i in v2 if any(o['url'] == i['url'] for o in v1)]
        print(f"Duplicates: {len(duplicates)}")
    print("\n")

async def test():
    sections = [
        ("Home", "https://hqporner.com/"),
        ("Amateur", "https://hqporner.com/category/Amateur"),
        ("Search 'mom'", "https://hqporner.com/?q=mom")
    ]
    for name, url in sections:
        await test_section(name, url)

asyncio.run(test())
