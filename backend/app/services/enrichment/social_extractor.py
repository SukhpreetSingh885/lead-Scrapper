import re
from urllib.parse import urlparse, urlunparse
from typing import List, Dict, Set


class SocialProfileExtractor:
    PLATFORM_PATTERNS = {
        "facebook": re.compile(r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9.\-_]+)/?', re.IGNORECASE),
        "instagram": re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)/?', re.IGNORECASE),
        "linkedin": re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/([a-zA-Z0-9.\-_]+)/?', re.IGNORECASE),
        "youtube": re.compile(r'https?://(?:www\.)?youtube\.com/(?:@|c/|channel/)?([a-zA-Z0-9.\-_]+)/?', re.IGNORECASE),
        "twitter_x": re.compile(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?', re.IGNORECASE),
    }

    IGNORED_SLUGS = {
        "facebook": {"sharer", "share", "pages", "groups", "intent", "login", "dialog", "plugins"},
        "instagram": {"p", "explore", "stories", "reels", "accounts", "direct"},
        "linkedin": {"shareArticle", "sharing", "feed", "company-beta"},
        "youtube": {"watch", "playlist", "embed", "feed", "results", "share"},
        "twitter_x": {"intent", "share", "home", "search", "explore", "hashtag"},
    }

    @classmethod
    def extract_from_html(cls, html_content: str) -> List[Dict[str, str]]:
        if not html_content:
            return []

        results: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()

        for platform, pattern in cls.PLATFORM_PATTERNS.items():
            for match in pattern.finditer(html_content):
                full_url = match.group(0).rstrip('/')
                slug = match.group(1).lower().strip('/')

                if slug in cls.IGNORED_SLUGS.get(platform, set()):
                    continue

                # Clean query strings and fragments
                parsed = urlparse(full_url)
                clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', '', ''))

                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    results.append({
                        "platform": platform,
                        "profile_url": clean_url,
                        "original_url": full_url,
                        "handle": f"@{slug}" if not slug.startswith("@") else slug
                    })

        return results

