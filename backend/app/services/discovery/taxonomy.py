"""
Extensible Category Taxonomy for India Leads Platform.
Provides canonical categories, synonyms/aliases, keywords, OSM tags,
validation rules, and documentation for OpenStreetMap Overpass discovery.
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import re
from rapidfuzz import fuzz


@dataclass
class CategoryDefinition:
    canonical_name: str
    slug: str
    osm_tags: List[Tuple[str, str]]
    aliases: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    negative_tags: Dict[str, List[str]] = field(default_factory=dict)
    ambiguous_alternatives: List[str] = field(default_factory=list)
    description: str = ""
    is_reliable_osm: bool = True
    reliability_notes: str = ""


# Comprehensive Taxonomy of Supported Indian Business Categories
TAXONOMY: Dict[str, CategoryDefinition] = {
    "pet_shop": CategoryDefinition(
        canonical_name="Pet Shop",
        slug="pet-shop",
        osm_tags=[("shop", "pet"), ("shop", "aquarium")],
        aliases=[
            "pet shop", "pet shops", "pet store", "pet stores", "pet house",
            "pet food", "pet supplies", "aquarium shop", "aquarium store",
            "pet accessories", "pet products"
        ],
        keywords=["pet", "pets", "aquarium", "dog food", "cat food", "bird", "fish"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "fast_food", "bar", "bank", "pharmacy", "hospital"],
            "leisure": ["fitness_centre", "sports_centre"]
        },
        ambiguous_alternatives=["Pet Boarding / Pet Care", "Veterinary Clinic"],
        description="Retail stores selling pets, pet food, accessories, and aquariums.",
        is_reliable_osm=True,
        reliability_notes="Mapped reliably under shop=pet and shop=aquarium."
    ),

    "pet_care": CategoryDefinition(
        canonical_name="Pet Boarding / Pet Care",
        slug="pet-care",
        osm_tags=[
            ("amenity", "animal_boarding"),
            ("amenity", "animal_shelter"),
            ("leisure", "dog_park")
        ],
        aliases=[
            "pet boarding", "pet care", "pet daycare", "pet resort",
            "dog boarding", "kennel", "cattery", "pet hostel", "dog daycare",
            "pet grooming", "dog grooming"
        ],
        keywords=["boarding", "shelter", "kennel", "hostel", "daycare", "grooming"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bank"]
        },
        ambiguous_alternatives=["Pet Shop", "Veterinary Clinic"],
        description="Pet boarding, daycare facilities, kennels, and grooming salons.",
        is_reliable_osm=True,
        reliability_notes="Good coverage for dedicated boarding and daycare facilities."
    ),

    "veterinary": CategoryDefinition(
        canonical_name="Veterinary Clinic",
        slug="veterinary-clinic",
        osm_tags=[("amenity", "veterinary")],
        aliases=[
            "veterinary clinic", "veterinary", "vet", "vets", "vet clinic",
            "pet clinic", "animal hospital", "veterinary hospital",
            "vet doctor", "animal clinic"
        ],
        keywords=["vet", "veterinary", "animal hospital", "pet hospital", "pet clinic"],
        negative_tags={
            "shop": ["clothes", "hairdresser", "beauty", "supermarket"],
            "leisure": ["fitness_centre"]
        },
        ambiguous_alternatives=["Pet Shop", "Clinic"],
        description="Veterinary clinics, animal hospitals, and pet health services.",
        is_reliable_osm=True,
        reliability_notes="OSM tag amenity=veterinary is standard worldwide."
    ),

    "clinic": CategoryDefinition(
        canonical_name="Clinic",
        slug="clinic",
        osm_tags=[
            ("amenity", "clinic"),
            ("healthcare", "clinic"),
            ("amenity", "doctors")
        ],
        aliases=[
            "clinic", "clinics", "polyclinic", "medical clinic",
            "health clinic", "dispensary", "doctor", "doctors",
            "medical centre", "consultant doctor"
        ],
        keywords=["clinic", "polyclinic", "dispensary", "doctor", "dr.", "health care"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bar", "bank"],
            "shop": ["hairdresser", "beauty", "clothes", "pet"],
            "leisure": ["fitness_centre", "sports_centre"]
        },
        ambiguous_alternatives=["Hospital", "Dental Clinic", "Veterinary Clinic"],
        description="General and specialist outpatient medical clinics and doctor offices.",
        is_reliable_osm=True,
        reliability_notes="Extensively mapped across urban India."
    ),

    "dental_clinic": CategoryDefinition(
        canonical_name="Dental Clinic",
        slug="dental-clinic",
        osm_tags=[
            ("amenity", "dentist"),
            ("healthcare", "dentist")
        ],
        aliases=[
            "dental clinic", "dental clinics", "dentist", "dentists",
            "dental hospital", "dental care", "orthodontist", "teeth clinic",
            "dental centre", "dental surgery"
        ],
        keywords=["dental", "dentist", "teeth", "orthodontic", "smile"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bank"],
            "shop": ["clothes", "supermarket"]
        },
        ambiguous_alternatives=["Clinic", "Hospital"],
        description="Dental clinics, dentists, orthodontists, and dental care centres.",
        is_reliable_osm=True,
        reliability_notes="Strong mapping accuracy under amenity=dentist."
    ),

    "hospital": CategoryDefinition(
        canonical_name="Hospital",
        slug="hospital",
        osm_tags=[
            ("amenity", "hospital"),
            ("healthcare", "hospital")
        ],
        aliases=[
            "hospital", "hospitals", "medical hospital", "nursing home",
            "multispeciality hospital", "super speciality hospital",
            "children hospital", "maternity hospital", "eye hospital"
        ],
        keywords=["hospital", "nursing home", "healthcare", "medical research"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bank"],
            "shop": ["clothes", "hairdresser"]
        },
        ambiguous_alternatives=["Clinic", "Dental Clinic"],
        description="Inpatient hospitals, nursing homes, and major healthcare centres.",
        is_reliable_osm=True,
        reliability_notes="High OSM mapping quality due to public emergency relevance."
    ),

    "salon": CategoryDefinition(
        canonical_name="Salon",
        slug="salon",
        osm_tags=[
            ("shop", "hairdresser"),
            ("shop", "beauty")
        ],
        aliases=[
            "salon", "salons", "beauty parlour", "hairdresser", "hair salon",
            "barber", "barbershop", "beauty salon", "spa", "unisex salon",
            "makeover", "nail salon", "hair studio"
        ],
        keywords=["salon", "hair", "beauty", "parlour", "barber", "spa"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bar", "bank", "pharmacy", "hospital"],
            "leisure": ["fitness_centre", "sports_centre"]
        },
        ambiguous_alternatives=["Beauty"],
        description="Hairdressers, beauty salons, barbershops, and day spas.",
        is_reliable_osm=True,
        reliability_notes="Commonly mapped under shop=hairdresser and shop=beauty."
    ),

    "gym": CategoryDefinition(
        canonical_name="Gym",
        slug="gym",
        osm_tags=[
            ("leisure", "fitness_centre"),
            ("sport", "fitness"),
            ("leisure", "gym"),
            ("amenity", "gym"),
            ("amenity", "fitness_centre"),
            ("sport", "bodybuilding"),
            ("sport", "weightlifting"),
            ("sport", "crossfit")
        ],
        aliases=[
            "gym", "gyms", "fitness centre", "fitness center", "fitness",
            "health club", "crossfit", "gymnasium", "workout studio",
            "bodybuilding", "powerlifting"
        ],
        keywords=["gym", "fitness", "crossfit", "workout", "bodybuilding", "gymnasium", "health club", "powerlifting"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bar", "pub", "fast_food", "bank", "pharmacy", "hospital"],
            "shop": ["hairdresser", "beauty", "massage", "clothes", "supermarket", "bakery"],
            "leisure": ["fitness_station", "playground", "park", "pitch", "swimming_pool"]
        },
        description="Fitness centres, workout gyms, health clubs, and bodybuilding studios.",
        is_reliable_osm=True,
        reliability_notes="Mapped reliably under leisure=fitness_centre, sport=fitness, and leisure=gym."
    ),

    "cafe": CategoryDefinition(
        canonical_name="Cafe",
        slug="cafe",
        osm_tags=[("amenity", "cafe")],
        aliases=[
            "cafe", "cafes", "coffee shop", "coffee", "cafeteria",
            "espresso bar", "tea house", "chai shop", "tea cafe", "bakery cafe"
        ],
        keywords=["cafe", "coffee", "tea", "espresso", "latte", "cappuccino"],
        negative_tags={
            "shop": ["hairdresser", "beauty", "clothes"],
            "leisure": ["fitness_centre", "sports_centre"]
        },
        ambiguous_alternatives=["Restaurant", "Bakery"],
        description="Cafes, coffee houses, tea bars, and casual beverage lounges.",
        is_reliable_osm=True,
        reliability_notes="Extensively mapped across urban Indian markets."
    ),

    "restaurant": CategoryDefinition(
        canonical_name="Restaurant",
        slug="restaurant",
        osm_tags=[("amenity", "restaurant")],
        aliases=[
            "restaurant", "restaurants", "dining", "eatery", "bistro",
            "dhaba", "family restaurant", "food court", "fast food",
            "pizzeria", "fine dining", "multi cuisine"
        ],
        keywords=["restaurant", "dining", "eatery", "dhaba", "food", "kitchen"],
        negative_tags={
            "shop": ["hairdresser", "beauty", "clothes", "pet"],
            "leisure": ["fitness_centre"]
        },
        ambiguous_alternatives=["Cafe"],
        description="Restaurants, eateries, dhabas, family dining, and bistros.",
        is_reliable_osm=True,
        reliability_notes="Extremely high density of OSM records."
    ),

    "fashion": CategoryDefinition(
        canonical_name="Fashion",
        slug="fashion",
        osm_tags=[
            ("shop", "clothes"),
            ("shop", "boutique")
        ],
        aliases=[
            "fashion", "clothing store", "clothing shop", "clothes",
            "garments", "apparel", "boutique", "textiles", "tailor",
            "menswear", "womenswear", "kids wear", "ethnic wear", "clothing"
        ],
        keywords=["fashion", "clothes", "clothing", "garments", "apparel", "wear", "suit", "saree"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "pharmacy", "hospital"],
            "leisure": ["fitness_centre"]
        },
        ambiguous_alternatives=["Boutique"],
        description="Clothing stores, garment shops, apparel retailers, and fashion boutiques.",
        is_reliable_osm=True,
        reliability_notes="Standardized mapping under shop=clothes and shop=boutique."
    ),

    "boutique": CategoryDefinition(
        canonical_name="Boutique",
        slug="boutique",
        osm_tags=[
            ("shop", "boutique"),
            ("shop", "clothes")
        ],
        aliases=[
            "boutique", "boutiques", "designer boutique", "fashion boutique",
            "ladies boutique", "couture", "bridal boutique"
        ],
        keywords=["boutique", "designer", "couture", "tailoring", "dresses"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "hospital"],
            "leisure": ["fitness_centre"]
        },
        ambiguous_alternatives=["Fashion"],
        description="Designer boutiques, custom apparel, and specialty fashion studios.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=boutique and shop=clothes."
    ),

    "electronics": CategoryDefinition(
        canonical_name="Electronics",
        slug="electronics",
        osm_tags=[
            ("shop", "electronics"),
            ("shop", "mobile_phone"),
            ("shop", "electrical")
        ],
        aliases=[
            "electronics", "electronic store", "computer shop", "mobile store",
            "phone shop", "mobile phone shop", "electricals", "appliances",
            "gadgets", "laptop store", "it hardware store"
        ],
        keywords=["electronics", "mobile", "computer", "laptop", "appliances", "phone"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "hospital"]
        },
        description="Electronics retailers, mobile phone stores, and home appliance outlets.",
        is_reliable_osm=True,
        reliability_notes="Solid coverage for mobile stores and consumer electronics."
    ),

    "grocery": CategoryDefinition(
        canonical_name="Grocery",
        slug="grocery",
        osm_tags=[
            ("shop", "supermarket"),
            ("shop", "convenience"),
            ("shop", "grocery"),
            ("shop", "greengrocer")
        ],
        aliases=[
            "grocery", "groceries", "supermarket", "supermarkets",
            "kirana", "provision store", "department store", "convenience store",
            "hypermarket", "organic store", "greengrocer"
        ],
        keywords=["grocery", "supermarket", "kirana", "provisions", "daily needs", "mart"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "hospital"]
        },
        description="Supermarkets, grocery stores, local kirana provisions, and department stores.",
        is_reliable_osm=True,
        reliability_notes="High density under shop=supermarket and shop=convenience."
    ),

    "pharmacy": CategoryDefinition(
        canonical_name="Pharmacy",
        slug="pharmacy",
        osm_tags=[
            ("amenity", "pharmacy"),
            ("shop", "chemist")
        ],
        aliases=[
            "pharmacy", "pharmacies", "chemist", "chemists", "medical store",
            "drugstore", "druggist", "medicine shop", "ayurvedic pharmacy"
        ],
        keywords=["pharmacy", "chemist", "medical store", "medicos", "druggist"],
        negative_tags={
            "amenity": ["cafe", "restaurant"],
            "shop": ["clothes", "hairdresser"]
        },
        description="Pharmacies, chemists, and retail medical dispensaries.",
        is_reliable_osm=True,
        reliability_notes="Standardized globally under amenity=pharmacy."
    ),

    "hotel": CategoryDefinition(
        canonical_name="Hotel",
        slug="hotel",
        osm_tags=[
            ("tourism", "hotel"),
            ("tourism", "guest_house"),
            ("tourism", "resort")
        ],
        aliases=[
            "hotel", "hotels", "resort", "resorts", "guest house",
            "lodge", "motel", "inn", "homestay", "service apartment"
        ],
        keywords=["hotel", "resort", "inn", "stay", "guest house", "lodge"],
        negative_tags={
            "shop": ["clothes", "hairdresser", "supermarket"]
        },
        description="Hotels, luxury resorts, guest houses, lodges, and tourist accommodation.",
        is_reliable_osm=True,
        reliability_notes="High completeness under tourism=hotel."
    ),

    "education": CategoryDefinition(
        canonical_name="Education",
        slug="education",
        osm_tags=[
            ("amenity", "school"),
            ("amenity", "college"),
            ("amenity", "university")
        ],
        aliases=[
            "education", "school", "schools", "college", "colleges",
            "university", "universities", "coaching", "academy", "training institute"
        ],
        keywords=["school", "college", "institute", "academy", "university", "education"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "bar"]
        },
        description="Educational institutions, schools, colleges, and training academies.",
        is_reliable_osm=True,
        reliability_notes="Consistently mapped educational facilities."
    ),

    "real_estate": CategoryDefinition(
        canonical_name="Real Estate",
        slug="real-estate",
        osm_tags=[("office", "estate_agent")],
        aliases=[
            "real estate", "real estate agents", "real estate agent", "realtor",
            "realtors", "property dealer", "property consultant", "realty",
            "property advisory", "builders office"
        ],
        keywords=["estate", "property", "realty", "realtor", "builders", "housing"],
        negative_tags={
            "amenity": ["cafe", "restaurant"]
        },
        description="Real estate agents, property consultants, and advisory firms.",
        is_reliable_osm=True,
        reliability_notes="Mapped under office=estate_agent."
    ),

    "automotive": CategoryDefinition(
        canonical_name="Automotive",
        slug="automotive",
        osm_tags=[
            ("shop", "car_repair"),
            ("shop", "car"),
            ("shop", "motorcycle"),
            ("amenity", "car_wash")
        ],
        aliases=[
            "automotive", "car repair", "auto repair", "garage", "car service",
            "bike service", "motorcycle repair", "car dealer", "car wash",
            "automobile", "mechanic"
        ],
        keywords=["auto", "car", "motorcycle", "garage", "mechanic", "tyre", "wash"],
        negative_tags={
            "amenity": ["cafe", "restaurant", "hospital"]
        },
        description="Auto repair garages, service centres, car dealers, and car wash outlets.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=car_repair, shop=car, and amenity=car_wash."
    ),

    "hardware": CategoryDefinition(
        canonical_name="Hardware",
        slug="hardware",
        osm_tags=[
            ("shop", "hardware"),
            ("shop", "doityourself")
        ],
        aliases=[
            "hardware", "hardware store", "paint shop", "sanitary",
            "sanitary store", "plywood", "building materials", "tools store",
            "electrical and hardware", "iron store"
        ],
        keywords=["hardware", "paint", "sanitary", "tools", "plywood", "steel"],
        negative_tags={
            "amenity": ["cafe", "restaurant"]
        },
        description="Hardware stores, building materials, paints, and sanitary fixture retailers.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=hardware and shop=doityourself."
    ),

    "beauty": CategoryDefinition(
        canonical_name="Beauty",
        slug="beauty",
        osm_tags=[
            ("shop", "beauty"),
            ("shop", "cosmetics")
        ],
        aliases=[
            "beauty", "cosmetics", "skincare", "beauty products",
            "cosmetic store", "makeup store", "fragrance store"
        ],
        keywords=["cosmetics", "skincare", "beauty", "makeup", "perfume"],
        negative_tags={
            "amenity": ["cafe", "restaurant"]
        },
        ambiguous_alternatives=["Salon"],
        description="Cosmetics retailers, skincare outlets, and beauty supply stores.",
        is_reliable_osm=True,
        reliability_notes="Covered under shop=cosmetics and shop=beauty."
    ),

    "furniture": CategoryDefinition(
        canonical_name="Furniture",
        slug="furniture",
        osm_tags=[
            ("shop", "furniture"),
            ("shop", "interior_decoration")
        ],
        aliases=[
            "furniture", "furniture store", "home decor", "furnishing",
            "interior decor", "mattress store", "sofa store", "woodcraft"
        ],
        keywords=["furniture", "decor", "furnishings", "mattress", "interior"],
        negative_tags={
            "amenity": ["cafe", "restaurant"]
        },
        description="Furniture showrooms, home decor retailers, and furnishing stores.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=furniture."
    ),

    "professional_services": CategoryDefinition(
        canonical_name="Professional Services",
        slug="professional-services",
        osm_tags=[
            ("office", "lawyer"),
            ("office", "accountant"),
            ("office", "consulting"),
            ("office", "financial")
        ],
        aliases=[
            "professional services", "lawyer", "advocate", "chartered accountant",
            "ca firm", "tax consultant", "legal services", "consulting firm",
            "notary", "audit firm"
        ],
        keywords=["lawyer", "advocate", "accountant", "consulting", "legal", "ca"],
        negative_tags={
            "amenity": ["cafe", "restaurant"]
        },
        description="Lawyers, chartered accountants, tax advisors, and management consultants.",
        is_reliable_osm=True,
        reliability_notes="Mapped under office=lawyer, office=accountant, office=consulting."
    ),

    # Additional standard retail & commercial categories
    "bakery": CategoryDefinition(
        canonical_name="Bakery",
        slug="bakery",
        osm_tags=[("shop", "bakery")],
        aliases=["bakery", "bakeries", "cake shop", "pastry shop", "bakehouse"],
        keywords=["bakery", "cake", "bread", "pastry", "confectionery"],
        negative_tags={"leisure": ["fitness_centre"]},
        description="Bakeries, cake shops, and confectionery stores.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=bakery."
    ),

    "jewelry": CategoryDefinition(
        canonical_name="Jewelry",
        slug="jewelry",
        osm_tags=[("shop", "jewelry")],
        aliases=["jewelry", "jewellery", "jeweler", "jewellers", "gold shop", "diamond store"],
        keywords=["jewelry", "jewellers", "gold", "diamond", "silver"],
        description="Jewelry stores, goldsmiths, and diamond retailers.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=jewelry."
    ),

    "optician": CategoryDefinition(
        canonical_name="Optician",
        slug="optician",
        osm_tags=[("shop", "optician")],
        aliases=["optician", "opticians", "optical", "optical store", "eyewear", "spectacles"],
        keywords=["optician", "optical", "glasses", "eyewear", "lens"],
        description="Opticians, optical stores, and eyewear retailers.",
        is_reliable_osm=True,
        reliability_notes="Mapped under shop=optician."
    ),

    "bank": CategoryDefinition(
        canonical_name="Bank",
        slug="bank",
        osm_tags=[("amenity", "bank")],
        aliases=["bank", "banks", "commercial bank"],
        keywords=["bank", "banking", "finance"],
        description="Commercial bank branches and financial institutions.",
        is_reliable_osm=True,
        reliability_notes="Mapped under amenity=bank."
    ),

    "it_company": CategoryDefinition(
        canonical_name="IT / Software Company",
        slug="it-company",
        osm_tags=[("office", "it")],
        aliases=["it company", "it companies", "software company", "software companies", "tech company"],
        keywords=["software", "technology", "tech", "it solutions", "systems"],
        description="Information technology, software development, and tech offices.",
        is_reliable_osm=True,
        reliability_notes="Mapped under office=it."
    ),

    "digital_marketing": CategoryDefinition(
        canonical_name="Digital Marketing Agency",
        slug="digital-marketing",
        osm_tags=[("office", "advertising_agency")],
        aliases=["digital marketing", "digital marketing agency", "advertising agency", "media agency"],
        keywords=["marketing", "advertising", "media", "seo", "branding"],
        description="Advertising agencies and digital marketing firms.",
        is_reliable_osm=True,
        reliability_notes="Mapped under office=advertising_agency."
    ),

    "manufacturers": CategoryDefinition(
        canonical_name="Manufacturers",
        slug="manufacturers",
        osm_tags=[("industrial", "factory"), ("craft", "metal_construction")],
        aliases=["manufacturers", "manufacturer", "factory", "industrial unit", "fabrication"],
        keywords=["manufacturing", "factory", "industry", "industrial", "works"],
        description="Manufacturing facilities, industrial units, and fabrication works.",
        is_reliable_osm=True,
        reliability_notes="Mapped under industrial=factory."
    )
}


class CategoryTaxonomyResolver:
    """
    Intelligent category resolver that parses natural language inputs,
    matches synonyms/aliases, handles ambiguous terms, and generates accurate OSM tags.
    """

    @classmethod
    def resolve(cls, query: str) -> Tuple[CategoryDefinition, Optional[List[str]]]:
        """
        Resolves query string to CategoryDefinition.
        Returns (CategoryDefinition, suggestions_if_ambiguous) or raises ValueError.
        """
        clean = query.strip().lower()
        if not clean:
            raise ValueError("Business category cannot be empty.")

        # 1. Exact alias match
        for cat_def in TAXONOMY.values():
            if clean in [a.lower() for a in cat_def.aliases]:
                suggestions = cat_def.ambiguous_alternatives if cat_def.ambiguous_alternatives else None
                return cat_def, suggestions

        # 2. Canonical name exact match
        for cat_def in TAXONOMY.values():
            if clean == cat_def.canonical_name.lower():
                return cat_def, None

        # 3. Whole-phrase match across aliases (only if alias covers major part of query)
        for cat_def in TAXONOMY.values():
            for alias in sorted(cat_def.aliases, key=len, reverse=True):
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, clean):
                    # Only accept if alias length is at least 65% of query length
                    if len(alias) >= len(clean) * 0.65:
                        suggestions = cat_def.ambiguous_alternatives if cat_def.ambiguous_alternatives else None
                        return cat_def, suggestions

        # 4. High-threshold fuzzy match on aliases and canonical names (>= 80)
        best_cat = None
        best_score = 0
        for cat_def in TAXONOMY.values():
            score = fuzz.ratio(clean, cat_def.canonical_name.lower())
            if score > best_score:
                best_score = score
                best_cat = cat_def
            for alias in cat_def.aliases:
                a_score = fuzz.ratio(clean, alias.lower())
                if a_score > best_score:
                    best_score = a_score
                    best_cat = cat_def

        if best_cat and best_score >= 80:
            suggestions = best_cat.ambiguous_alternatives if best_cat.ambiguous_alternatives else None
            return best_cat, suggestions

        # Not supported
        supported = [c.canonical_name for c in TAXONOMY.values()]
        raise ValueError(
            f"This business category is not yet supported by the configured discovery provider. "
            f"Supported categories include: {', '.join(sorted(supported))}."
        )

    @classmethod
    def get_suggestions_for_input(cls, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Returns dynamic category suggestions for autocomplete / search dropdown.
        """
        clean = query.strip().lower()
        if not clean:
            # Return top popular categories
            popular = ["Pet Shop", "Clinic", "Hospital", "Salon", "Gym", "Cafe", "Restaurant", "Fashion", "Pharmacy", "Real Estate"]
            return [
                {
                    "canonical_name": c.canonical_name,
                    "slug": c.slug,
                    "description": c.description,
                    "sample_aliases": c.aliases[:3]
                }
                for c in TAXONOMY.values() if c.canonical_name in popular
            ]

        results = []
        for cat_def in TAXONOMY.values():
            match_score = 0
            if clean in cat_def.canonical_name.lower():
                match_score = 100
            else:
                for alias in cat_def.aliases:
                    if clean in alias.lower():
                        match_score = max(match_score, 90)
                    else:
                        score = fuzz.partial_ratio(clean, alias.lower())
                        if score > match_score:
                            match_score = score

            if match_score >= 60:
                results.append((match_score, {
                    "canonical_name": cat_def.canonical_name,
                    "slug": cat_def.slug,
                    "description": cat_def.description,
                    "sample_aliases": cat_def.aliases[:3],
                    "ambiguous_alternatives": cat_def.ambiguous_alternatives
                }))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    @classmethod
    def list_all_categories(cls) -> List[Dict[str, Any]]:
        """
        Returns full category directory with reliability metadata.
        """
        return [
            {
                "canonical_name": c.canonical_name,
                "slug": c.slug,
                "description": c.description,
                "aliases": c.aliases,
                "osm_tags": [f"{k}={v}" for k, v in c.osm_tags],
                "is_reliable_osm": c.is_reliable_osm,
                "reliability_notes": c.reliability_notes,
                "ambiguous_alternatives": c.ambiguous_alternatives
            }
            for c in TAXONOMY.values()
        ]
