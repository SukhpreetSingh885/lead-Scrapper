import re
from urllib.parse import urlparse
from typing import Optional


class DataNormalizer:
    # Common corporate/entity suffixes in India
    LEGAL_SUFFIX_REGEX = re.compile(
        r'\b(?:private\s+limited|pvt\.?\s*ltd\.?|ltd\.?|limited|llp|inc\.?|corp\.?|co\.?|enterprises|services|solutions)\b',
        re.IGNORECASE
    )

    # Address noise words
    ADDRESS_ABBR = {
        r'\bsco\b': 'sco',
        r'\bscf\b': 'scf',
        r'\bshop\s*no\.?\b': 'shop',
        r'\bbooth\s*no\.?\b': 'booth',
        r'\bflr\b': 'floor',
        r'\b1st\b': 'first',
        r'\b2nd\b': 'second',
        r'\b3rd\b': 'third',
        r'\bsec\b': 'sector',
        r'\brd\b': 'road',
        r'\bmkt\b': 'market',
    }

    @classmethod
    def normalize_company_name(cls, name: str) -> str:
        """
        Normalizes company legal name for deterministic and fuzzy matching:
        - lowercase
        - strips demo tags like [DEMO DATA]
        - strips legal suffixes ('Pvt Ltd', 'LLP', 'Limited', etc.)
        - removes excessive whitespace & punctuation
        """
        if not name:
            return ""

        clean = name.strip()
        # Remove [DEMO DATA] prefix if present
        clean = re.sub(r'\[DEMO\s*DATA\]', '', clean, flags=re.IGNORECASE).strip()

        # Remove branch location suffix after hyphen or comma if it's there
        # e.g., "Glamour Studio Salon & Spa - Phase 7" -> "Glamour Studio Salon & Spa"
        if " - " in clean:
            clean = clean.split(" - ")[0].strip()

        # Remove legal suffixes
        clean = cls.LEGAL_SUFFIX_REGEX.sub('', clean)
        # Remove special characters
        clean = re.sub(r'[^\w\s]', ' ', clean)
        # Collapse whitespace
        clean = re.sub(r'\s+', ' ', clean).strip().lower()
        return clean

    @classmethod
    def normalize_branch_name(cls, name: str) -> str:
        """Normalizes full branch name including locality."""
        if not name:
            return ""
        clean = re.sub(r'\[DEMO\s*DATA\]', '', name, flags=re.IGNORECASE).strip()
        clean = re.sub(r'[^\w\s]', ' ', clean)
        return re.sub(r'\s+', ' ', clean).strip().lower()

    @classmethod
    def normalize_address(cls, address: Optional[str]) -> str:
        if not address:
            return ""
        clean = address.lower()
        # Remove dots from acronyms like S.C.O. -> sco
        clean = re.sub(r'\.', '', clean)
        for pat, repl in cls.ADDRESS_ABBR.items():
            clean = re.sub(pat, repl, clean, flags=re.IGNORECASE)
        clean = re.sub(r'[^\w\s]', ' ', clean)
        return re.sub(r'\s+', ' ', clean).strip()

    @classmethod
    def normalize_domain(cls, url_or_domain: Optional[str]) -> Optional[str]:
        if not url_or_domain:
            return None
        clean = url_or_domain.strip().lower()
        if clean.startswith("http://") or clean.startswith("https://"):
            parsed = urlparse(clean)
            domain = parsed.netloc
        else:
            domain = clean.split('/')[0]

        # Strip www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else None

    @classmethod
    def normalize_pincode(cls, pincode: Optional[str]) -> Optional[str]:
        if not pincode:
            return None
        digits = re.sub(r'\D', '', str(pincode))
        return digits if len(digits) == 6 else None

