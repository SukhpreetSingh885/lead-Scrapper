import pytest
from app.services.enrichment.phone_extractor import IndianPhoneExtractor
from app.services.enrichment.email_extractor import EmailExtractor
from app.services.enrichment.social_extractor import SocialProfileExtractor


SAMPLE_SALON_HTML = """
<!DOCTYPE html>
<html>
<head><title>Glamour Studio Salon Mohali</title></head>
<body>
  <header>
    <h1>Glamour Studio - Phase 7 Mohali</h1>
    <a href="tel:+919876543210">Call Us: +91 98765 43210</a>
    <a href="https://wa.me/919876543210">Chat on WhatsApp</a>
  </header>
  <main>
    <p>Contact our customer desk at info@glamourstudiosalon.in or book via support@glamourstudiosalon.in.</p>
    <p>Alternate landline: 0172-2214567.</p>
    <a href="mailto:phase7@glamourstudiosalon.in">Email Manager</a>

    <!-- Obvious dummy emails that MUST be discarded -->
    <p>Template demo: example@example.com, test@test.com, icon@2x.png</p>
  </main>
  <footer>
    <a href="https://instagram.com/glamourstudiomohali">Follow on Instagram</a>
    <a href="https://facebook.com/glamourstudiopunjab">Like us on Facebook</a>
    <a href="https://linkedin.com/company/glamourstudiosalon">LinkedIn Company</a>
    <a href="https://youtube.com/@glamourstudiosalon">YouTube Channel</a>
    <!-- Social share URLs that should be ignored -->
    <a href="https://facebook.com/sharer/sharer.php?u=foo">Share on FB</a>
    <a href="https://twitter.com/intent/tweet?text=hi">Tweet</a>
  </footer>
</body>
</html>
"""


def test_phone_extraction_from_html():
    phones = IndianPhoneExtractor.extract_from_text_and_html(SAMPLE_SALON_HTML)
    assert len(phones) >= 2

    normalized_vals = [p["normalized_value"] for p in phones]
    assert "+919876543210" in normalized_vals

    types = [p["contact_type"] for p in phones]
    assert "whatsapp" in types or "mobile" in types


def test_email_extraction_and_placeholder_filtering():
    emails = EmailExtractor.extract_from_html(SAMPLE_SALON_HTML)
    assert len(emails) >= 2

    norm_emails = [e["normalized_value"] for e in emails]
    assert "phase7@glamourstudiosalon.in" in norm_emails
    assert "info@glamourstudiosalon.in" in norm_emails

    # Must reject placeholder emails
    assert "example@example.com" not in norm_emails
    assert "test@test.com" not in norm_emails
    assert not any(e.endswith(".png") for e in norm_emails)


def test_social_profile_extraction():
    socials = SocialProfileExtractor.extract_from_html(SAMPLE_SALON_HTML)
    assert len(socials) >= 4

    platforms = {s["platform"] for s in socials}
    assert "instagram" in platforms
    assert "facebook" in platforms
    assert "linkedin" in platforms
    assert "youtube" in platforms

    # Verify share slugs were ignored
    urls = [s["profile_url"] for s in socials]
    assert not any("sharer" in u for u in urls)
    assert not any("intent" in u for u in urls)

