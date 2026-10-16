import csv
import io
from typing import List, Dict, Any, Generator
from app.models import Branch


def sanitize_formula_injection(value: Any) -> str:
    """
    Escapes spreadsheet formula injection vulnerability.
    If value begins with =, +, -, @, \t, or \r, prepends a single quote.
    """
    if value is None:
        return "Not Available"
    val_str = str(value).strip()
    if not val_str:
        return "Not Available"
    if val_str[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{val_str}"
    return val_str


class CsvExportService:
    HEADERS = [
        "Business Name",
        "Category",
        "Mobile Number",
        "Phone Number",
        "WhatsApp Number",
        "Email",
        "Website",
        "Address",
        "Locality",
        "City",
        "District",
        "State",
        "PIN Code",
        "Country",
        "Facebook",
        "Instagram",
        "LinkedIn",
        "Other Social Links",
        "Data Source",
        "Permission Status",
        "Enrichment Status",
        "Last Verified"
    ]

    @staticmethod
    def branch_to_row(branch: Branch) -> List[str]:
        # Extract contact values
        mobile = None
        landline = None
        whatsapp = None
        email = None

        for c in branch.contacts:
            if c.contact_type == "mobile" and not mobile:
                mobile = c.normalized_value or c.original_value
            elif c.contact_type in ("landline", "phone") and not landline:
                landline = c.normalized_value or c.original_value
            elif c.contact_type == "whatsapp" and not whatsapp:
                whatsapp = c.normalized_value or c.original_value
            elif c.contact_type == "email" and not email:
                email = c.normalized_value or c.original_value

        fb, insta, linkedin, others = None, None, None, []
        for s in branch.social_profiles:
            if s.platform == "facebook" and not fb:
                fb = s.profile_url
            elif s.platform == "instagram" and not insta:
                insta = s.profile_url
            elif s.platform == "linkedin" and not linkedin:
                linkedin = s.profile_url
            else:
                others.append(s.profile_url)

        source_name = branch.source.name if branch.source else "Independently Verified"
        if branch.is_demo:
            source_name = "[DEMO DATA] Deterministic Offline Fixture"

        verified_date = branch.last_checked_at.strftime("%Y-%m-%d %H:%M") if branch.last_checked_at else "Not Available"

        row = [
            sanitize_formula_injection(branch.branch_name),
            sanitize_formula_injection(branch.company.primary_category if branch.company else "Not Available"),
            sanitize_formula_injection(mobile),
            sanitize_formula_injection(landline),
            sanitize_formula_injection(whatsapp),
            sanitize_formula_injection(email),
            sanitize_formula_injection(branch.website_url),
            sanitize_formula_injection(branch.address_line),
            sanitize_formula_injection(branch.locality),
            sanitize_formula_injection(branch.city),
            sanitize_formula_injection(branch.district),
            sanitize_formula_injection(branch.state),
            sanitize_formula_injection(branch.pincode),
            sanitize_formula_injection(branch.country),
            sanitize_formula_injection(fb),
            sanitize_formula_injection(insta),
            sanitize_formula_injection(linkedin),
            sanitize_formula_injection("; ".join(others) if others else None),
            sanitize_formula_injection(source_name),
            sanitize_formula_injection(branch.source_permission_status),
            sanitize_formula_injection(branch.enrichment_status),
            sanitize_formula_injection(verified_date),
        ]
        return row

    @classmethod
    def generate_csv_stream(cls, branches: List[Branch]) -> Generator[str, None, None]:
        """Streams CSV content with UTF-8 BOM encoding for seamless Excel opening."""
        # Yield UTF-8 BOM
        yield '\ufeff'

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cls.HEADERS)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for branch in branches:
            writer.writerow(cls.branch_to_row(branch))
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    @classmethod
    def generate_csv_bytes(cls, branches: List[Branch]) -> bytes:
        return "".join(list(cls.generate_csv_stream(branches))).encode("utf-8-sig")

