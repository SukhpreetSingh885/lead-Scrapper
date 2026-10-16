from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from rapidfuzz import fuzz

from app.models import IndiaLocation
from app.schemas.location import LocationSuggestion, LocationValidationResult


class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def suggest_locations(self, query: str, limit: int = 10) -> List[LocationSuggestion]:
        if not query or len(query.strip()) < 1:
            # Return top major cities by default
            records = self.db.query(IndiaLocation).limit(limit).all()
        else:
            clean_q = query.strip().lower()
            # If query is digits, match PIN code
            if clean_q.isdigit():
                records = self.db.query(IndiaLocation).filter(
                    IndiaLocation.pincode.like(f"{clean_q}%")
                ).limit(limit).all()
            else:
                records = self.db.query(IndiaLocation).filter(
                    or_(
                        IndiaLocation.city.ilike(f"%{clean_q}%"),
                        IndiaLocation.locality.ilike(f"%{clean_q}%"),
                        IndiaLocation.district.ilike(f"%{clean_q}%"),
                        IndiaLocation.state.ilike(f"%{clean_q}%"),
                    )
                ).limit(limit).all()

        suggestions = []
        for r in records:
            display_parts = [r.city]
            if r.locality:
                display_parts.insert(0, r.locality)
            if r.district and r.district != r.city:
                display_parts.append(r.district)
            display_parts.append(r.state)
            if r.pincode:
                display_parts.append(r.pincode)

            display_name = ", ".join(display_parts) + ", India"
            suggestions.append(
                LocationSuggestion(
                    id=r.id,
                    city=r.city,
                    state=r.state,
                    district=r.district,
                    locality=r.locality,
                    pincode=r.pincode,
                    display_name=display_name
                )
            )
        return suggestions

    def validate_indian_location(self, raw_input: str) -> LocationValidationResult:
        if not raw_input or not raw_input.strip():
            return LocationValidationResult(
                is_valid=False,
                message="Location input cannot be empty."
            )

        clean = raw_input.strip()
        # Remove trailing ", India" if typed
        clean_no_country = clean.replace(", India", "").replace(",India", "").strip()

        # Check by PIN code
        if clean_no_country.isdigit() and len(clean_no_country) == 6:
            loc = self.db.query(IndiaLocation).filter(IndiaLocation.pincode == clean_no_country).first()
            if loc:
                return LocationValidationResult(
                    is_valid=True,
                    resolved_city=loc.city,
                    resolved_state=loc.state,
                    resolved_district=loc.district,
                    resolved_pincode=loc.pincode,
                    candidates=[LocationSuggestion(
                        id=loc.id,
                        city=loc.city,
                        state=loc.state,
                        district=loc.district,
                        locality=loc.locality,
                        pincode=loc.pincode,
                        display_name=f"{loc.locality or loc.city}, {loc.state} - {loc.pincode}, India"
                    )]
                )

        # Search matching records
        candidates = self.suggest_locations(clean_no_country, limit=5)
        if not candidates:
            # Fuzzy match across all distinct cities in database
            all_locs = self.db.query(IndiaLocation).all()
            scored = []
            for loc in all_locs:
                score = fuzz.token_set_ratio(clean_no_country.lower(), loc.city.lower())
                if score >= 75:
                    scored.append((score, loc))

            if scored:
                scored.sort(key=lambda x: x[0], reverse=True)
                top = scored[0][1]
                return LocationValidationResult(
                    is_valid=True,
                    resolved_city=top.city,
                    resolved_state=top.state,
                    resolved_district=top.district,
                    resolved_pincode=top.pincode,
                    ambiguous=len(scored) > 1,
                    candidates=[
                        LocationSuggestion(
                            id=l.id,
                            city=l.city,
                            state=l.state,
                            district=l.district,
                            locality=l.locality,
                            pincode=l.pincode,
                            display_name=f"{l.city}, {l.state}, India"
                        ) for _, l in scored[:3]
                    ]
                )

            # Location not recognized within India
            return LocationValidationResult(
                is_valid=False,
                message=f"'{raw_input}' was not recognized as a valid location in India. Please enter an Indian city, district, state, or 6-digit PIN code."
            )

        # Found candidates
        exact_match = next((c for c in candidates if c.city.lower() == clean_no_country.lower()), None)
        if exact_match:
            return LocationValidationResult(
                is_valid=True,
                resolved_city=exact_match.city,
                resolved_state=exact_match.state,
                resolved_district=exact_match.district,
                resolved_pincode=exact_match.pincode,
                ambiguous=False,
                candidates=candidates
            )

        first = candidates[0]
        return LocationValidationResult(
            is_valid=True,
            resolved_city=first.city,
            resolved_state=first.state,
            resolved_district=first.district,
            resolved_pincode=first.pincode,
            ambiguous=len(candidates) > 1,
            candidates=candidates
        )

