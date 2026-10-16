import csv
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
import openpyxl
from app.services.discovery.base import DiscoveredLeadItem


class LicensedImportService:
    @staticmethod
    def parse_csv(
        file_bytes: bytes,
        license_name: str = "Imported Licensed Dataset",
        permitted_usage: str = "Permitted Storage & Enrichment"
    ) -> List[DiscoveredLeadItem]:
        decoded = file_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(decoded))
        return LicensedImportService._process_rows(reader, license_name, permitted_usage)

    @staticmethod
    def parse_xlsx(
        file_bytes: bytes,
        license_name: str = "Imported Licensed Dataset",
        permitted_usage: str = "Permitted Storage & Enrichment"
    ) -> List[DiscoveredLeadItem]:
        wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []

        header = [str(col).strip() if col is not None else f"col_{idx}" for idx, col in enumerate(rows[0])]
        dict_rows = []
        for row in rows[1:]:
            if not any(row):
                continue
            row_dict = {header[i]: (str(val).strip() if val is not None else "") for i, val in enumerate(row) if i < len(header)}
            dict_rows.append(row_dict)

        return LicensedImportService._process_rows(dict_rows, license_name, permitted_usage)

    @staticmethod
    def _normalize_key(key: str) -> str:
        return key.lower().replace(" ", "").replace("_", "").replace("-", "")

    @staticmethod
    def _process_rows(
        rows,
        license_name: str,
        permitted_usage: str
    ) -> List[DiscoveredLeadItem]:
        items: List[DiscoveredLeadItem] = []

        for idx, row in enumerate(rows):
            # Normalize dictionary keys
            norm_row = {LicensedImportService._normalize_key(k): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

            name = (
                norm_row.get("businessname") or
                norm_row.get("companyname") or
                norm_row.get("name") or
                norm_row.get("title")
            )
            if not name:
                continue

            category = (
                norm_row.get("category") or
                norm_row.get("industry") or
                norm_row.get("businesscategory") or
                "General Business"
            )

            city = (
                norm_row.get("city") or
                norm_row.get("district") or
                "India"
            )

            state = norm_row.get("state") or "India"
            locality = norm_row.get("locality") or norm_row.get("area")
            pincode = norm_row.get("pincode") or norm_row.get("postalcode") or norm_row.get("zip")
            address = norm_row.get("address") or norm_row.get("addressline") or norm_row.get("street")

            mobile = norm_row.get("mobile") or norm_row.get("mobilenumber")
            phone = mobile or norm_row.get("phone") or norm_row.get("phonenumber") or norm_row.get("landline")
            website = norm_row.get("website") or norm_row.get("websiteurl") or norm_row.get("url")
            email = norm_row.get("email") or norm_row.get("businessemail")
            whatsapp = norm_row.get("whatsapp") or norm_row.get("whatsappnumber")

            items.append(
                DiscoveredLeadItem(
                    external_id=f"LICENSED-IMPORT-{idx}-{name.replace(' ', '-').lower()[:30]}",
                    business_name=name,
                    category=category,
                    address_line=address,
                    locality=locality,
                    city=city,
                    state=state,
                    pincode=pincode,
                    country="India",
                    phone=phone,
                    website_url=website,
                    raw_payload={
                        "import_license": license_name,
                        "permitted_usage": permitted_usage,
                        "raw_row": row,
                        "mobile": mobile,
                        "email": email,
                        "whatsapp": whatsapp
                    },
                    is_eligible_for_crm=True,
                    source_code="licensed_csv",
                    license_status="permitted_storage",
                    is_demo=False
                )
            )

        return items

