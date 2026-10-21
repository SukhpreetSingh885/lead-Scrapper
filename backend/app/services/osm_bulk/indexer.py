"""
Local OpenStreetMap / Geofabrik Bulk Extract Indexer Service.
Provides offline indexing of official Geofabrik India OSM extracts.
Strictly respects OpenStreetMap ODbL 1.0 license attribution.
"""
import os
import math
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.core.config import settings
from app.services.discovery.taxonomy import CategoryTaxonomyResolver, TAXONOMY
from app.services.deduplication.normalizer import DataNormalizer
from app.services.discovery.overpass_provider import INDIAN_CITY_COORDINATES

logger = logging.getLogger(__name__)

# Official Geofabrik OpenStreetMap extract mirrors for India
GEOFABRIK_EXTRACTS_METADATA = {
    "india_full": {
        "name": "India (Entire Nation)",
        "region_code": "IN",
        "pbf_url": "https://download.geofabrik.de/asia/india-latest.osm.pbf",
        "download_size_approx": "1.45 GB",
        "disk_required_approx": "5.5 GB",
        "ram_required_approx": "4.0 GB",
        "coverage": "All 28 Indian States & 8 Union Territories"
    },
    "north_zone": {
        "name": "Northern India Zone (Chandigarh, Punjab, Haryana, Delhi, HP, J&K, Rajasthan, UP, Uttarakhand)",
        "region_code": "IN-NORTH",
        "pbf_url": "https://download.geofabrik.de/asia/india/north-zone-latest.osm.pbf",
        "download_size_approx": "385 MB",
        "disk_required_approx": "1.6 GB",
        "ram_required_approx": "2.0 GB",
        "coverage": "Chandigarh Tricity, Punjab, Haryana, Delhi NCR, Rajasthan, Uttar Pradesh, Himachal"
    },
    "south_zone": {
        "name": "Southern India Zone (Karnataka, Tamil Nadu, Kerala, Andhra Pradesh, Telangana)",
        "region_code": "IN-SOUTH",
        "pbf_url": "https://download.geofabrik.de/asia/india/south-zone-latest.osm.pbf",
        "download_size_approx": "420 MB",
        "disk_required_approx": "1.8 GB",
        "ram_required_approx": "2.0 GB",
        "coverage": "Bengaluru, Chennai, Hyderabad, Kochi, Coimbatore, Mysuru, Visakhapatnam"
    },
    "west_zone": {
        "name": "Western India Zone (Maharashtra, Gujarat, Goa)",
        "region_code": "IN-WEST",
        "pbf_url": "https://download.geofabrik.de/asia/india/west-zone-latest.osm.pbf",
        "download_size_approx": "390 MB",
        "disk_required_approx": "1.7 GB",
        "ram_required_approx": "2.0 GB",
        "coverage": "Mumbai, Pune, Ahmedabad, Surat, Vadodara, Panaji, Nagpur, Nashik"
    },
    "east_zone": {
        "name": "Eastern India Zone (West Bengal, Bihar, Odisha, Jharkhand)",
        "region_code": "IN-EAST",
        "pbf_url": "https://download.geofabrik.de/asia/india/east-zone-latest.osm.pbf",
        "download_size_approx": "315 MB",
        "disk_required_approx": "1.3 GB",
        "ram_required_approx": "2.0 GB",
        "coverage": "Kolkata, Patna, Bhubaneswar, Ranchi, Cuttack, Siliguri"
    }
}

DATA_DISCLAIMER = (
    "HONEST DATA NOTICE: Local OSM extracts (such as Geofabrik .osm.pbf files) contain the exact same "
    "community-mapped OpenStreetMap database elements as queried via live Overpass API. "
    "A local extract does not magically invent or contain more businesses than OpenStreetMap itself. "
    "The primary benefits of an indexed local extract are zero external API rate limits, ultra-fast "
    "sub-millisecond queries, complete offline discovery capability, and freedom from third-party server downtime."
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class OsmBulkIndexService:
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.storage_dir = base_dir / "osm_bulk_data"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path or (self.storage_dir / "osm_local_index.db"))
        self._init_sqlite_schema()

    def _init_sqlite_schema(self):
        """Initializes SQLite schema for locally indexed OSM commercial entities."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS local_osm_businesses (
                    id TEXT PRIMARY KEY,
                    osm_type TEXT NOT NULL,
                    osm_id INTEGER NOT NULL,
                    business_name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tag_key TEXT NOT NULL,
                    tag_value TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    city TEXT,
                    state TEXT,
                    pincode TEXT,
                    address_line TEXT,
                    phone TEXT,
                    mobile TEXT,
                    whatsapp TEXT,
                    email TEXT,
                    website TEXT,
                    source TEXT DEFAULT 'geofabrik_osm_extract',
                    license TEXT DEFAULT 'ODbL 1.0',
                    indexed_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_osm_cat_city ON local_osm_businesses(category, city)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_osm_coords ON local_osm_businesses(latitude, longitude)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_osm_normname ON local_osm_businesses(normalized_name)")
            conn.commit()

    def get_bulk_index_info(self) -> Dict[str, Any]:
        """Returns disk, RAM requirements, download mirrors, and index status."""
        total_indexed = 0
        categories_indexed = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM local_osm_businesses")
                total_indexed = cur.fetchone()[0]

                cur.execute("SELECT category, COUNT(*) FROM local_osm_businesses GROUP BY category ORDER BY 2 DESC")
                categories_indexed = [{"category": row[0], "count": row[1]} for row in cur.fetchall()]
        except Exception:
            pass

        # Check existing downloaded extract files in osm_bulk_data
        downloaded_files = []
        if self.storage_dir.exists():
            for f in self.storage_dir.glob("*.pbf"):
                downloaded_files.append({
                    "filename": f.name,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                })

        db_file = Path(self.db_path)
        index_db_size_mb = round(db_file.stat().st_size / (1024 * 1024), 2) if db_file.exists() else 0

        return {
            "status": "ready",
            "disclaimer": DATA_DISCLAIMER,
            "system_requirements": {
                "recommended_ram": "4 GB or higher",
                "recommended_disk_space": "5 GB SSD for full India extract, 1.5 GB for Northern Zone",
                "free_and_offline": True,
                "api_rate_limits": "None (completely local queries)"
            },
            "available_extract_mirrors": GEOFABRIK_EXTRACTS_METADATA,
            "local_storage_directory": str(self.storage_dir),
            "downloaded_extract_files": downloaded_files,
            "index_database": {
                "path": self.db_path,
                "size_mb": index_db_size_mb,
                "total_indexed_records": total_indexed,
                "category_breakdown": categories_indexed
            }
        }

    def index_lead_items(self, items: List[Dict[str, Any]]) -> int:
        """
        Inserts or replaces pre-extracted or parsed business items into local SQLite index.
        Preserves complete OSM provenance and ODbL license metadata.
        """
        if not items:
            return 0

        normalizer = DataNormalizer()
        now_iso = datetime.now(timezone.utc).isoformat()
        records_to_insert = []

        for it in items:
            osm_id_val = it.get("osm_id") or it.get("id") or 0
            osm_type = it.get("osm_type", "node")
            ext_id = f"osm-{osm_type}-{osm_id_val}"

            name = it.get("business_name") or it.get("name")
            if not name:
                continue

            category = it.get("category", "General Commercial")
            norm_name = normalizer.normalize_company_name(name)

            lat = float(it.get("latitude", 0.0))
            lon = float(it.get("longitude", 0.0))

            records_to_insert.append((
                ext_id,
                osm_type,
                int(osm_id_val) if isinstance(osm_id_val, (int, str)) and str(osm_id_val).isdigit() else 0,
                name.strip(),
                norm_name,
                category,
                it.get("tag_key", "amenity"),
                it.get("tag_value", "commercial"),
                lat,
                lon,
                it.get("city"),
                it.get("state"),
                it.get("pincode"),
                it.get("address_line") or it.get("address"),
                it.get("phone"),
                it.get("mobile"),
                it.get("whatsapp"),
                it.get("email"),
                it.get("website") or it.get("website_url"),
                "geofabrik_osm_extract",
                "ODbL 1.0",
                now_iso
            ))

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO local_osm_businesses (
                    id, osm_type, osm_id, business_name, normalized_name, category,
                    tag_key, tag_value, latitude, longitude, city, state, pincode,
                    address_line, phone, mobile, whatsapp, email, website,
                    source, license, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records_to_insert)
            conn.commit()

        return len(records_to_insert)

    def search_local_index(
        self,
        city: str,
        category: str,
        radius_km: float = 15.0,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Queries the local OSM index by category and geographic distance from resolved city center.
        Zero network latency, zero API rate limits, 100% offline.
        """
        resolved_cat_def, _ = CategoryTaxonomyResolver.resolve(category)
        canonical_cat = resolved_cat_def.canonical_name

        # Resolve center coordinates for city
        clean_city = city.strip().lower()
        center_lat, center_lon = 30.7046, 76.7179  # Default Tricity
        for c_key, (c_lat, c_lon, _) in INDIAN_CITY_COORDINATES.items():
            if c_key in clean_city or clean_city in c_key:
                center_lat, center_lon = c_lat, c_lon
                break

        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Query all candidates matching category
            cur.execute("""
                SELECT * FROM local_osm_businesses
                WHERE category = ? OR category LIKE ?
            """, (canonical_cat, f"%{canonical_cat}%"))

            rows = cur.fetchall()
            for r in rows:
                lat = r["latitude"]
                lon = r["longitude"]
                dist = haversine_km(center_lat, center_lon, lat, lon)
                if dist <= radius_km:
                    row_dict = dict(r)
                    row_dict["distance_km"] = round(dist, 2)
                    results.append(row_dict)

        results.sort(key=lambda x: x["distance_km"])
        return results[:max_results]

