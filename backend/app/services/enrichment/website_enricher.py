from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import Branch, BusinessContact, SocialProfile, EnrichmentJob
from app.services.enrichment.crawler import WebsiteCrawler
from app.services.enrichment.phone_extractor import IndianPhoneExtractor
from app.services.enrichment.email_extractor import EmailExtractor
from app.services.enrichment.social_extractor import SocialProfileExtractor


class WebsiteEnrichmentEngine:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.crawler = WebsiteCrawler()

    async def enrich_preview_item(
        self,
        website_url: str,
        business_name: str,
        max_pages: int = 2,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Visits authorized official website of a discovered business during preview,
        extracts valid phone/mobile/whatsapp numbers and emails with provenance evidence,
        WITHOUT saving anything to the permanent CRM database.
        """
        if not website_url or not isinstance(website_url, str):
            return {"success": False, "reason": "No website URL provided"}

        clean_url = website_url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = f"https://{clean_url}"

        try:
            crawler = WebsiteCrawler(max_pages=max_pages, timeout=timeout)
            pages = await crawler.crawl_site(clean_url)
            if not pages:
                return {"success": False, "reason": "No accessible pages or disallowed by robots.txt/SSRF"}

            all_phones: List[Dict[str, Any]] = []
            all_emails: List[Dict[str, str]] = []
            all_socials: List[Dict[str, str]] = []

            for page_url, html in pages.items():
                phones = IndianPhoneExtractor.extract_from_text_and_html(html, source_url=page_url)
                emails = EmailExtractor.extract_from_html(html, source_url=page_url)
                socials = SocialProfileExtractor.extract_from_html(html)

                all_phones.extend(phones)
                all_emails.extend(emails)
                all_socials.extend(socials)

            # Deduplicate extracted contacts
            unique_phones = {}
            for p in all_phones:
                key = (p.get("contact_type"), p.get("normalized_value"))
                if key not in unique_phones:
                    unique_phones[key] = p

            unique_emails = {}
            for e in all_emails:
                norm = e.get("normalized_value")
                if norm and norm not in unique_emails:
                    unique_emails[norm] = e

            unique_socials = {}
            for s in all_socials:
                norm = s.get("profile_url")
                if norm and norm not in unique_socials:
                    unique_socials[norm] = s

            return {
                "success": True,
                "pages_crawled": len(pages),
                "phones": list(unique_phones.values()),
                "emails": list(unique_emails.values()),
                "socials": list(unique_socials.values()),
            }
        except Exception as e:
            return {"success": False, "reason": str(e)}

    async def enrich_branch(self, branch_id: str) -> Dict[str, Any]:
        """
        Visits authorized public website of the branch and extracts verified contact details.
        """
        if not self.db:
            return {"success": False, "error": "Database session required for enrich_branch"}

        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            return {"success": False, "error": "Branch not found"}

        if not branch.website_url:
            branch.enrichment_status = "not_applicable"
            self.db.commit()
            return {"success": True, "message": "No website URL to enrich", "phones": 0, "emails": 0, "socials": 0}

        # Create enrichment job record
        job = EnrichmentJob(
            branch_id=branch.id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        self.db.commit()

        try:
            pages = await self.crawler.crawl_site(branch.website_url)

            all_phones: List[Dict[str, Any]] = []
            all_emails: List[Dict[str, str]] = []
            all_socials: List[Dict[str, str]] = []

            for page_url, html in pages.items():
                phones = IndianPhoneExtractor.extract_from_text_and_html(html, source_url=page_url)
                emails = EmailExtractor.extract_from_html(html, source_url=page_url)
                socials = SocialProfileExtractor.extract_from_html(html)

                all_phones.extend(phones)
                all_emails.extend(emails)
                all_socials.extend(socials)

            # Deduplicate extracted contacts
            unique_phones = {}
            for p in all_phones:
                unique_phones[p["normalized_value"]] = p

            unique_emails = {}
            for e in all_emails:
                unique_emails[e["normalized_value"]] = e

            unique_socials = {}
            for s in all_socials:
                unique_socials[s["profile_url"]] = s

            # Persist contacts
            phones_added = 0
            for p in unique_phones.values():
                existing = self.db.query(BusinessContact).filter(
                    BusinessContact.branch_id == branch.id,
                    BusinessContact.normalized_value == p["normalized_value"]
                ).first()
                if not existing:
                    contact = BusinessContact(
                        branch_id=branch.id,
                        contact_type=p["contact_type"],
                        original_value=p["original_value"],
                        normalized_value=p["normalized_value"],
                        is_primary=(phones_added == 0 and not branch.contacts),
                        is_verified=True,
                        source="website_enrichment",
                        source_url=p.get("source_url"),
                        evidence=p.get("evidence")
                    )
                    self.db.add(contact)
                    phones_added += 1

            emails_added = 0
            for e in unique_emails.values():
                existing = self.db.query(BusinessContact).filter(
                    BusinessContact.branch_id == branch.id,
                    BusinessContact.normalized_value == e["normalized_value"]
                ).first()
                if not existing:
                    contact = BusinessContact(
                        branch_id=branch.id,
                        contact_type="email",
                        original_value=e["original_value"],
                        normalized_value=e["normalized_value"],
                        is_primary=(emails_added == 0),
                        is_verified=True,
                        source="website_enrichment",
                        source_url=e.get("source_url"),
                        evidence=e.get("evidence")
                    )
                    self.db.add(contact)
                    emails_added += 1

            socials_added = 0
            for s in unique_socials.values():
                existing = self.db.query(SocialProfile).filter(
                    SocialProfile.branch_id == branch.id,
                    SocialProfile.profile_url == s["profile_url"]
                ).first()
                if not existing:
                    sp = SocialProfile(
                        branch_id=branch.id,
                        platform=s["platform"],
                        profile_url=s["profile_url"],
                        original_url=s["original_url"],
                        handle=s.get("handle")
                    )
                    self.db.add(sp)
                    socials_added += 1

            branch.enrichment_status = "completed"
            branch.last_checked_at = datetime.now(timezone.utc)

            job.status = "completed"
            job.pages_crawled = len(pages)
            job.phones_found = len(unique_phones)
            job.emails_found = len(unique_emails)
            job.socials_found = len(unique_socials)
            job.completed_at = datetime.now(timezone.utc)

            self.db.commit()

            return {
                "success": True,
                "pages_crawled": len(pages),
                "phones": len(unique_phones),
                "emails": len(unique_emails),
                "socials": len(unique_socials)
            }

        except Exception as e:
            self.db.rollback()
            branch.enrichment_status = "failed"
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return {"success": False, "error": str(e)}

