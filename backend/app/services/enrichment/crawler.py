import asyncio
import logging
from typing import List, Set, Optional, Dict
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

from app.core.config import settings
from app.utils.ssrf_guard import is_safe_url

logger = logging.getLogger(__name__)


class WebsiteCrawler:
    CONTACT_PAGE_KEYWORDS = ["contact", "about", "reach", "support", "location", "touch"]

    def __init__(
        self,
        max_pages: int = None,
        timeout: float = None,
        user_agent: str = None
    ):
        self.max_pages = max_pages or settings.ENRICHMENT_MAX_PAGES_PER_DOMAIN
        self.timeout = timeout or settings.ENRICHMENT_REQUEST_TIMEOUT_SECONDS
        self.user_agent = user_agent or settings.ENRICHMENT_USER_AGENT

    async def check_robots_txt(self, base_url: str) -> bool:
        """Checks whether crawling is allowed by robots.txt."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        safe, reason = is_safe_url(robots_url)
        if not safe:
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                res = await client.get(robots_url, headers={"User-Agent": self.user_agent})
                if res.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(res.text.splitlines())
                    return rp.can_fetch(self.user_agent, base_url)
        except Exception:
            pass  # If robots.txt cannot be fetched or doesn't exist, proceed politely
        return True

    async def crawl_site(self, target_url: str) -> Dict[str, str]:
        """
        Crawls the homepage and up to max_pages relevant contact/about subpages.
        Returns a dictionary mapping {page_url: html_content}.
        """
        safe, reason = is_safe_url(target_url)
        if not safe:
            logger.warning(f"Blocked unsafe URL {target_url}: {reason}")
            return {}

        allowed = await self.check_robots_txt(target_url)
        if not allowed:
            logger.warning(f"robots.txt disallowed crawling for {target_url}")
            return {}

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        pages_content: Dict[str, str] = {}
        visited: Set[str] = set()
        queue: List[str] = [target_url]
        base_domain = urlparse(target_url).netloc.lower()

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
            while queue and len(visited) < self.max_pages:
                current_url = queue.pop(0)
                if current_url in visited:
                    continue

                safe, reason = is_safe_url(current_url)
                if not safe:
                    continue

                visited.add(current_url)

                try:
                    res = await client.get(current_url, headers=headers)
                    if res.status_code != 200:
                        continue

                    content_type = res.headers.get("content-type", "").lower()
                    if "text/html" not in content_type:
                        continue

                    html = res.text
                    pages_content[current_url] = html

                    # Find internal links to contact / about pages
                    soup = BeautifulSoup(html, "html.parser")
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"].strip()
                        full_link = urljoin(current_url, href)
                        parsed_link = urlparse(full_link)

                        # Must stay on same domain
                        if parsed_link.netloc.lower() != base_domain:
                            continue

                        # Check if link or text matches contact/about keywords
                        link_path = parsed_link.path.lower()
                        link_text = a_tag.get_text().strip().lower()

                        if any(kw in link_path or kw in link_text for kw in self.CONTACT_PAGE_KEYWORDS):
                            clean_link = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}"
                            if clean_link not in visited and clean_link not in queue:
                                queue.append(clean_link)

                    # Polite rate limit delay
                    await asyncio.sleep(settings.ENRICHMENT_RATE_LIMIT_DELAY)

                except Exception as e:
                    logger.debug(f"Failed to fetch {current_url}: {e}")
                    continue

        return pages_content

