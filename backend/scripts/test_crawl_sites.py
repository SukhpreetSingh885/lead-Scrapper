import asyncio
import sys
sys.path.insert(0, 'backend')
from app.services.enrichment.crawler import WebsiteCrawler
from app.services.enrichment.phone_extractor import IndianPhoneExtractor

async def test_sites():
    crawler = WebsiteCrawler()
    for site in ['https://www.beigecafe.com/', 'https://www.hotelradius.com/', 'http://www.sodhihealthindia.com/']:
        print(f"=== Testing {site} ===")
        try:
            pages = await crawler.crawl_site(site)
            print(f"Crawled {len(pages)} pages")
            for url, html in pages.items():
                phones = IndianPhoneExtractor.extract_from_text_and_html(html, source_url=url)
                print(f"  {url} -> {len(phones)} phones:")
                for p in phones:
                    print(f"    * {p.get('contact_type')}: {p.get('normalized_value')} ({p.get('evidence')})")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sites())

