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

        # Check predefined Indian city coordinates
        from app.services.discovery.overpass_provider import INDIAN_CITY_COORDINATES
        clean_lower = clean_no_country.lower()
        if clean_lower in INDIAN_CITY_COORDINATES:
            lat, lon, st = INDIAN_CITY_COORDINATES[clean_lower]
            return LocationValidationResult(
                is_valid=True,
                resolved_city=clean_lower.title(),
                resolved_state=st,
                resolved_district=clean_lower.title(),
                candidates=[LocationSuggestion(
                    id=None,
                    city=clean_lower.title(),
                    state=st,
                    district=clean_lower.title(),
                    locality=None,
                    pincode=None,
                    display_name=f"{clean_lower.title()}, {st}, India"
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

    def parse_and_validate_locations(
        self,
        raw_input: str,
        locations_list: Optional[List[str]] = None
    ) -> Tuple[bool, List[Tuple[str, str]], Optional[str]]:
        """
        Parses and validates one or multiple Indian locations.
        Returns:
            (is_valid, list_of_(resolved_city, resolved_state), error_message_or_None)
        """
        targets = []
        if locations_list and len(locations_list) > 0:
            targets = [loc.strip() for loc in locations_list if loc and loc.strip()]
        else:
            raw_str = raw_input.strip()
            if "+" in raw_str:
                parts = [p.strip() for p in raw_str.split("+") if p.strip()]
            elif ";" in raw_str:
                parts = [p.strip() for p in raw_str.split(";") if p.strip()]
            elif "," in raw_str:
                single_res = self.validate_indian_location(raw_str)
                parts = [p.strip() for p in raw_str.split(",") if p.strip()]
                if len(parts) > 1:
                    all_parts_valid = True
                    temp_resolved = []
                    for p in parts:
                        p_res = self.validate_indian_location(p)
                        if p_res.is_valid and p_res.resolved_city:
                            temp_resolved.append((p_res.resolved_city, p_res.resolved_state or "India"))
                        else:
                            all_parts_valid = False
                            break
                    if all_parts_valid:
                        seen = set()
                        deduped = []
                        for c, s in temp_resolved:
                            if c.lower() not in seen:
                                seen.add(c.lower())
                                deduped.append((c, s))
                        return True, deduped, None

                if single_res.is_valid:
                    return True, [(single_res.resolved_city or raw_str.title(), single_res.resolved_state or "India")], None
            else:
                parts = [raw_str]

            targets = parts

        if not targets:
            return False, [], "Location input cannot be empty."

        resolved_list = []
        seen = set()
        for target in targets:
            res = self.validate_indian_location(target)
            if not res.is_valid or not res.resolved_city:
                return False, [], f"'{target}' was not recognized as a valid location in India."
            if res.resolved_city.lower() not in seen:
                seen.add(res.resolved_city.lower())
                resolved_list.append((res.resolved_city, res.resolved_state or "India"))

        return True, resolved_list, None

