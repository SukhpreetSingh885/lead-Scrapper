import re
from typing import List, Dict, Set, Optional
from email_validator import validate_email, EmailNotValidError


class EmailExtractor:
    MAILTO_REGEX = re.compile(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
    EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

    # Obvious placeholder / dummy email domains and prefixes
    PLACEHOLDER_DOMAINS = {
        "example.com", "example.org", "example.net",
        "domain.com", "yoursite.com", "yourdomain.com",
        "test.com", "mywebsite.com", "wix.com",
        "sentry.io", "cloudflare.com", "bootstrap.com"
    }

    PLACEHOLDER_USERNAMES = {
        "yourname", "username", "email", "name", "someone", "user",
        "admin@yourdomain.com", "test", "demo", "placeholder"
    }

    # Image/font extensions mistakenly matched as email domains
    INVALID_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "webp", "svg", "css", "js", "woff", "woff2", "ttf"
    }

    @classmethod
    def is_valid_business_email(cls, email: str) -> bool:
        if not email or "@" not in email:
            return False

        clean = email.strip().lower()

        # Check extension
        parts = clean.split(".")
        if len(parts) < 2 or parts[-1] in cls.INVALID_EXTENSIONS:
            return False

        username, domain = clean.split("@", 1)

        if username in cls.PLACEHOLDER_USERNAMES or domain in cls.PLACEHOLDER_DOMAINS:
            return False

        if any(dummy in domain for dummy in ("placeholder", "sample", "localhost")):
            return False

        try:
            # Syntax validation using email_validator
            valid = validate_email(clean, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    @classmethod
    def extract_from_html(cls, html_content: str, source_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extracts valid business emails from mailto: tags and page text.
        Deduplicates by normalized lowercase email.
        Records source_url and text evidence for each contact.
        """
        if not html_content:
            return []

        results: List[Dict[str, str]] = []
        seen: Set[str] = set()

        # 1. mailto: links (highest confidence)
        for match in cls.MAILTO_REGEX.finditer(html_content):
            email = match.group(1).strip().lower()
            if email not in seen and cls.is_valid_business_email(email):
                seen.add(email)
                results.append({
                    "original_value": match.group(1).strip(),
                    "normalized_value": email,
                    "contact_type": "email",
                    "source": "mailto_link",
                    "source_url": source_url,
                    "evidence": f"Mailto Link: {match.group(0)[:120]}"
                })

        # 2. Text emails
        # Strip script/style tags
        clean_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)

        for match in cls.EMAIL_REGEX.finditer(clean_text):
            raw_email = match.group(0).strip()
            norm_email = raw_email.lower()
            if norm_email not in seen and cls.is_valid_business_email(norm_email):
                seen.add(norm_email)
                start = max(0, match.start() - 35)
                end = min(len(clean_text), match.end() + 35)
                snippet = clean_text[start:end].strip()
                results.append({
                    "original_value": raw_email,
                    "normalized_value": norm_email,
                    "contact_type": "email",
                    "source": "body_text",
                    "source_url": source_url,
                    "evidence": f"Page Text: ...{snippet}..." if snippet else None
                })

        return results

