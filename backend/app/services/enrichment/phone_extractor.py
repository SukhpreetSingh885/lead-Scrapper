import re
from typing import List, Dict, Optional, Tuple, Set, Any
import phonenumbers
from phonenumbers import PhoneNumberType, PhoneNumberFormat


class IndianPhoneExtractor:
    # Common Indian phone regex matching patterns in text/HTML:
    # Handles: +91 98765 43210, +91-98765-43210, 09876543210, 9876543210, 0172-2214567, etc.
    PHONE_REGEX = re.compile(
        r'(?:(?:\+|0{0,2})91[\s.-]*)?(?:\(0\))?[6-9]\d{9}|'  # Indian Mobile (starts with 6, 7, 8, 9)
        r'(?:0\d{2,4}[-\s]?)?\d{6,8}'                          # Indian Landlines (with STD codes e.g. 0172-2214567, 011-23344556)
    )

    WHATSAPP_LINK_REGEX = re.compile(
        r'(?:https?://(?:api\.)?whatsapp\.com/send\?phone=|https?://wa\.me/)([\d+]+)',
        re.IGNORECASE
    )

    TEL_LINK_REGEX = re.compile(
        r'tel:([+\d\s().-]+)',
        re.IGNORECASE
    )

    @classmethod
    def expand_slashed_numbers(cls, raw_val: str) -> List[str]:
        """
        Expands slash-delimited Indian phone formats such as:
        '0172-5044436/37' -> ['0172-5044436', '01725044437']
        '0172-5044436 / 5044437' -> ['0172-5044436', '0172-5044437']
        '+91 98140 12345 / +91 98140 67890' -> ['+91 98140 12345', '+91 98140 67890']
        """
        if not raw_val or "/" not in raw_val or raw_val.startswith("http"):
            return [raw_val]

        parts = [p.strip() for p in raw_val.split("/") if p.strip()]
        if len(parts) == 2:
            base, suffix = parts[0], parts[1]
            results = [base]
            base_digits = re.sub(r'\D', '', base)

            if re.fullmatch(r'\d{1,3}', suffix) and len(base_digits) >= len(suffix):
                # Suffix replaces last N digits of base
                new_digits = base_digits[:-len(suffix)] + suffix
                results.append(new_digits)
            elif re.fullmatch(r'\d{6,8}', suffix):
                # Suffix is a local number; extract STD code if present in base
                m = re.match(r'(?:(?:\+|0{0,2})91[\s.-]*)?(0\d{2,4})', base)
                if m:
                    results.append(f"{m.group(1)}-{suffix}")
                else:
                    results.append(suffix)
            else:
                results.append(suffix)
            return results

        return parts

    @classmethod
    def extract_multiple_phones(
        cls,
        raw_string: str,
        default_type: Optional[str] = None,
        source: str = "raw",
        source_url: Optional[str] = None,
        evidence: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Splits a string potentially containing multiple Indian phone numbers
        (separated by commas, semicolons, slashes, pipes, 'and', 'or', etc.)
        and returns a deduplicated list of normalized phone dictionaries.
        """
        if not raw_string or not isinstance(raw_string, str):
            return []

        # First expand slash patterns
        candidate_tokens = []
        for token in cls.expand_slashed_numbers(raw_string):
            # Split by delimiters: comma, semicolon, pipe, newlines, 'and', 'or', '&'
            subparts = re.split(r'[,;|\n\r]+|\s+(?:and|or|&)\s+', token, flags=re.IGNORECASE)
            for sp in subparts:
                sp_clean = sp.strip()
                if sp_clean:
                    candidate_tokens.append(sp_clean)

        results: List[Dict[str, Any]] = []
        seen_normalized: Set[str] = set()

        for token in candidate_tokens:
            norm = cls.normalize_phone(token, default_type=default_type)
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                norm["source"] = source
                if source_url:
                    norm["source_url"] = source_url
                if evidence:
                    norm["evidence"] = evidence
                results.append(norm)

        return results

    @classmethod
    def extract_all_contacts_from_osm_tags(
        cls,
        tags: Dict[str, Any],
        elem_type: str = "node",
        elem_id: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts and normalizes all available contact channels from OpenStreetMap element tags:
        - contact:mobile
        - mobile
        - contact:whatsapp
        - contact:phone
        - phone
        Deduplicates by (contact_type, normalized_value) and preserves provenance.
        """
        if not tags or not isinstance(tags, dict):
            return []

        source_url = f"https://www.openstreetmap.org/{elem_type}/{elem_id}" if elem_id else None
        results: List[Dict[str, Any]] = []
        seen_keys: Set[Tuple[str, str]] = set()

        # Tag definitions with priority and default type hint
        tag_definitions = [
            ("contact:whatsapp", "whatsapp"),
            ("whatsapp", "whatsapp"),
            ("contact:mobile", "mobile"),
            ("mobile", "mobile"),
            ("contact:phone", None),
            ("phone", None),
        ]

        for tag_key, default_type in tag_definitions:
            tag_val = tags.get(tag_key)
            if tag_val and isinstance(tag_val, str) and tag_val.strip():
                extracted = cls.extract_multiple_phones(
                    raw_string=tag_val.strip(),
                    default_type=default_type,
                    source="osm",
                    source_url=source_url,
                    evidence=f"OSM tag: {tag_key}={tag_val.strip()}"
                )
                for item in extracted:
                    c_key = (item["contact_type"], item["normalized_value"])
                    if c_key not in seen_keys:
                        seen_keys.add(c_key)
                        results.append(item)

        return results

    STD_MAP = {
        "mohali": "0172",
        "chandigarh": "0172",
        "panchkula": "0172",
        "delhi": "011",
        "new delhi": "011",
        "mumbai": "022",
        "kolkata": "033",
        "chennai": "044",
        "bengaluru": "080",
        "bangalore": "080",
        "hyderabad": "040",
        "pune": "020",
        "jaipur": "0141",
        "lucknow": "0522",
        "ludhiana": "0161",
        "amritsar": "0183",
        "jalandhar": "0181",
        "patiala": "0175",
        "shimla": "0177",
        "dehradun": "0135",
    }

    @classmethod
    def normalize_phone(
        cls,
        raw_input: str,
        default_type: Optional[str] = None,
        city_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Validates and normalizes an Indian phone number into E.164 using phonenumbers library.
        Supports mobile (10-digit starting 6-9), landline (with STD code or city_context resolution),
        and WhatsApp numbers.
        Returns dict with:
          - original_value
          - normalized_value (E.164 e.g. +919876543210 or +911725044436)
          - contact_type: 'mobile', 'landline', or 'whatsapp'
          - is_valid: True
        or None if invalid.
        """
        if not raw_input or not isinstance(raw_input, str):
            return None

        cleaned = re.sub(r'[\r\n\t]', ' ', raw_input).strip()
        # Remove non-phone punctuation except +
        cleaned = re.sub(r'[^\d+]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        digits = re.sub(r'\D', '', cleaned)
        if digits.startswith("091") and len(digits) == 13 and digits[3] in '6789':
            cleaned = f"+91{digits[3:]}"
        elif digits.startswith("91") and len(digits) == 12 and digits[2] in '6789':
            cleaned = f"+91{digits[2:]}"
        elif digits.startswith("0") and len(digits) == 11 and digits[1] in '6789':
            cleaned = f"+91{digits[1:]}"
        elif len(digits) == 10 and digits[0] in '6789':
            cleaned = f"+91{digits}"
        elif len(digits) in (6, 7, 8) and city_context:
            c_key = city_context.strip().lower()
            if c_key in cls.STD_MAP:
                std_prefix = cls.STD_MAP[c_key]
                cleaned = f"{std_prefix}{digits}"

        try:
            parsed = phonenumbers.parse(cleaned, "IN")
            if not phonenumbers.is_valid_number(parsed):
                return None

            e164_val = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            num_type = phonenumbers.number_type(parsed)

            if default_type == "whatsapp":
                contact_type = "whatsapp"
            elif num_type == PhoneNumberType.MOBILE:
                contact_type = "mobile"
            elif num_type in (PhoneNumberType.FIXED_LINE, PhoneNumberType.FIXED_LINE_OR_MOBILE):
                contact_type = "landline"
            else:
                # If digits start with Indian mobile prefixes (6, 7, 8, 9)
                d = re.sub(r'\D', '', e164_val)
                if len(d) == 12 and d.startswith("91") and d[2] in '6789':
                    contact_type = "mobile"
                else:
                    contact_type = "landline"

            return {
                "original_value": raw_input.strip(),
                "normalized_value": e164_val,
                "contact_type": contact_type,
                "is_valid": True
            }

        except Exception:
            return None

    @classmethod
    def extract_from_text_and_html(cls, html_content: str, source_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts all valid Indian phone numbers and WhatsApp numbers from HTML page content,
        href="tel:..." links, and wa.me links.
        Deduplicates by normalized E.164 number.
        Records source_url and text evidence for each contact.
        """
        if not html_content:
            return []

        results: List[Dict[str, Any]] = []
        seen_normalized: Set[str] = set()

        # 1. Look for explicit WhatsApp links
        for match in cls.WHATSAPP_LINK_REGEX.finditer(html_content):
            raw_num = match.group(1)
            norm = cls.normalize_phone(raw_num, default_type="whatsapp")
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                norm["source"] = "website_enrichment"
                norm["source_url"] = source_url
                norm["evidence"] = f"WhatsApp Link: {match.group(0)[:120]}"
                results.append(norm)

        # 2. Look for href="tel:..." links
        for match in cls.TEL_LINK_REGEX.finditer(html_content):
            raw_tel = match.group(1)
            extracted = cls.extract_multiple_phones(
                raw_string=raw_tel,
                source="website_enrichment",
                source_url=source_url,
                evidence=f"Tel Link: {match.group(0)[:120]}"
            )
            for norm in extracted:
                if norm["normalized_value"] not in seen_normalized:
                    seen_normalized.add(norm["normalized_value"])
                    results.append(norm)

        # 3. Look for text occurrences of Indian phone numbers
        # Remove script and style tags content first
        clean_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)

        for match in cls.PHONE_REGEX.finditer(clean_text):
            raw_match = match.group(0)
            norm = cls.normalize_phone(raw_match)
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                start = max(0, match.start() - 35)
                end = min(len(clean_text), match.end() + 35)
                snippet = clean_text[start:end].strip()
                norm["source"] = "website_enrichment"
                norm["source_url"] = source_url
                norm["evidence"] = f"Page Text: ...{snippet}..." if snippet else None
                results.append(norm)

        return results


