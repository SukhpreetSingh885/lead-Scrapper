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

    @staticmethod
    def normalize_phone(raw_input: str) -> Optional[Dict[str, Any]]:
        """
        Validates and normalizes an Indian phone number into E.164.
        Returns dict with:
          - original_value
          - normalized_value (E.164 e.g. +919876543210)
          - contact_type: 'mobile', 'landline', or 'phone'
          - is_valid: True
        or None if invalid.
        """
        if not raw_input or not isinstance(raw_input, str):
            return None

        cleaned = re.sub(r'[\r\n\t]', ' ', raw_input).strip()
        # Remove non-phone punctuation
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

        try:
            parsed = phonenumbers.parse(cleaned, "IN")
            if not phonenumbers.is_valid_number(parsed):
                return None

            e164_val = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            num_type = phonenumbers.number_type(parsed)

            if num_type == PhoneNumberType.MOBILE:
                contact_type = "mobile"
            elif num_type in (PhoneNumberType.FIXED_LINE, PhoneNumberType.FIXED_LINE_OR_MOBILE):
                contact_type = "landline"
            else:
                contact_type = "phone"

            return {
                "original_value": raw_input.strip(),
                "normalized_value": e164_val,
                "contact_type": contact_type,
                "is_valid": True
            }

        except Exception:
            return None

    @classmethod
    def extract_from_text_and_html(cls, html_content: str) -> List[Dict[str, Any]]:
        """
        Extracts all valid Indian phone numbers and WhatsApp numbers from HTML page content,
        href="tel:..." links, and wa.me links.
        Deduplicates by normalized E.164 number.
        """
        if not html_content:
            return []

        results: List[Dict[str, Any]] = []
        seen_normalized: Set[str] = set()

        # 1. Look for explicit WhatsApp links
        for match in cls.WHATSAPP_LINK_REGEX.finditer(html_content):
            raw_num = match.group(1)
            norm = cls.normalize_phone(raw_num)
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                norm["contact_type"] = "whatsapp"
                results.append(norm)

        # 2. Look for href="tel:..." links
        for match in cls.TEL_LINK_REGEX.finditer(html_content):
            raw_tel = match.group(1)
            norm = cls.normalize_phone(raw_tel)
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                results.append(norm)

        # 3. Look for text occurrences of Indian phone numbers
        # Remove script and style tags content first
        clean_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)

        matches = cls.PHONE_REGEX.findall(clean_text)
        for raw_match in matches:
            norm = cls.normalize_phone(raw_match)
            if norm and norm["normalized_value"] not in seen_normalized:
                seen_normalized.add(norm["normalized_value"])
                results.append(norm)

        return results

