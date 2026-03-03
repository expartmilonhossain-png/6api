import asyncio
from app.scrapers.hqporner.scraper import list_videos

async def test():
    print("Page 1 length:", len(await list_videos("https://hqporner.com/category/Amateur", 1)))
    print("Page 2 length:", len(await list_videos("https://hqporner.com/category/Amateur", 2)))

asyncio.run(test())
