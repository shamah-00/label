from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from products.models import Product


PRODUCTS = [
    # ============================================================
    # TRUCK / MOTOR / CAR DECALS
    # ============================================================
    {
        "code": "DGO",
        "name": "Gasoline Only",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "320",
        "name": "Diesel Only",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "DMO",
        "name": "Mixed Fuel Only",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "DHO",
        "name": "Hydraulics Only",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "I711",
        "name": "DOT C2 Reflective / Conspicuity Tape",
        "industry": "truck_motor_car",
        "category": "reflective",
        "product_type": "reflective_label",
    },
    {
        "code": "312",
        "name": "Caution - Vehicle Stops & Backs Frequently / Wide Right Turns",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "333",
        "name": "Stay Back 200 Feet",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "362",
        "name": "If You Can't See My Mirrors, I Can't See You",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "NCU",
        "name": "No Personal Cell Phone Usage",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "T010",
        "name": "USDOT Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T011",
        "name": "MC Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T012",
        "name": "Company Name",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T013",
        "name": "City / State",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T014",
        "name": "GVWR",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T015",
        "name": "Unit / Truck Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T016",
        "name": "Fleet Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T017",
        "name": "CA / State Carrier Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T018",
        "name": "KYU / State Registration Number",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "T019",
        "name": "Slow Down / Give Trucks Space",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },
    {
        "code": "T020",
        "name": "Oversize / Wide Load",
        "industry": "truck_motor_car",
        "category": "stickers",
        "product_type": "truck_decal",
    },

    # ============================================================
    # WASTE COMPANY DECALS
    # ============================================================
    {
        "code": "042R",
        "name": "Keep Off / Do Not Play on or Around Container",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "032",
        "name": "Keep Off Container / Load Evenly",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "072",
        "name": "Multi-Message Container Safety",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "071",
        "name": "Multi-Message Waste Safety",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "066",
        "name": "Garbage Only",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "089",
        "name": "Danger - Do Not Park in Front of Container",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "305",
        "name": "Danger - Striking Hazard",
        "industry": "waste",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "306",
        "name": "Danger - Crushing Hazard",
        "industry": "waste",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "301",
        "name": "Danger - Pinch Point",
        "industry": "waste",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "310",
        "name": "Ladder Safety",
        "industry": "waste",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "062",
        "name": "Watch Overhead Wires",
        "industry": "waste",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "337",
        "name": "No Parking / Tow Away Zone",
        "industry": "waste",
        "category": "stickers",
        "product_type": "container_decal",
    },
    {
        "code": "043",
        "name": "Cardboard Only Recycling",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "074",
        "name": "Paper & Cardboard Recycling",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "031A",
        "name": "Commingled Recyclables Only",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "343",
        "name": "Single Stream Recycling",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "338",
        "name": "Full-Color Single Stream Recycling",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "335",
        "name": "Single Stream - No Glass",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "344",
        "name": "No Plastic Bags",
        "industry": "waste",
        "category": "stickers",
        "product_type": "recycling_label",
    },
    {
        "code": "315",
        "name": "Yard Waste Only",
        "industry": "waste",
        "category": "stickers",
        "product_type": "yard_waste_label",
    },

    # ============================================================
    # CONSTRUCTION DECALS
    # ============================================================
    {
        "code": "C001",
        "name": "Danger - Electrocution Hazard / Crane Not Insulated",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C002",
        "name": "Standard Crane & Derrick Signals",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C003",
        "name": "Check Fluid Levels",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C004",
        "name": "This Machine Pays Your Salary",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C005",
        "name": "DEF Fluid Only",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C006",
        "name": "Diesel",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C007",
        "name": "Warning - Rotating Shafts",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C008",
        "name": "Warning - Operator Stay Clear",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C009",
        "name": "Hydraulic Oil",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C010",
        "name": "Attention - Operators Are Responsible",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C011",
        "name": "Danger - Stand Clear of Swing Area",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C012",
        "name": "Danger - Outrigger Contact",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C013",
        "name": "Danger - Electrocution Hazard",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C014",
        "name": "Danger - Collapsing Boom Hazard",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C015",
        "name": "No Step",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C016",
        "name": "Danger - Crushing Hazard",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C017",
        "name": "Battery Disconnect Switch",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C018",
        "name": "Gasoline Only",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C019",
        "name": "Fire Extinguisher Inside",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "C020",
        "name": "First Aid / Fire Extinguisher",
        "industry": "construction",
        "category": "stickers",
        "product_type": "safety_decal",
    },

    # ============================================================
    # POOL DECALS
    # ============================================================
    {
        "code": "P001",
        "name": "Chlorine Danger",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P002",
        "name": "Muriatic Acid Danger",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P003",
        "name": "Sodium Hypochlorite Danger",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P004",
        "name": "Danger - Hazardous Chemicals",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P005",
        "name": "Corrosion / Hydrochloric Acid",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P006",
        "name": "Danger - Do Not Mix Chemicals",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P007",
        "name": "Authorized Personnel Only",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P008",
        "name": "Pool Chemical Storage - Caution",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P009",
        "name": "Calcium Hypochlorite / Oxidizer",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P010",
        "name": "Pool Service",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P011",
        "name": "Weekly Pool Service By",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P012",
        "name": "Pool Equipment Service",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P013",
        "name": "Pool Filter Service Record",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P014",
        "name": "Date Cleaned",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P015",
        "name": "Starting Filter Pressure",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P016",
        "name": "Pool Pump Service",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P017",
        "name": "Pool Heater Service",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P018",
        "name": "Pool Technician / Company Contact",
        "industry": "pool",
        "category": "stickers",
        "product_type": "facility_sign",
    },
    {
        "code": "P019",
        "name": "No Diving",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },
    {
        "code": "P020",
        "name": "Slippery",
        "industry": "pool",
        "category": "stickers",
        "product_type": "safety_decal",
    },

    # ============================================================
    # GOVERNMENT CONTRACTOR DECALS
    # ============================================================
    {
        "code": "G001",
        "name": "PROPERTY OF U.S. GOVERNMENT",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G002",
        "name": "GOVERNMENT PROPERTY",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G003",
        "name": "GOVERNMENT-FURNISHED PROPERTY (GFP)",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G004",
        "name": "CONTRACTOR-ACQUIRED PROPERTY (CAP)",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G005",
        "name": "U.S. GOVERNMENT PROPERTY - DO NOT REMOVE",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G006",
        "name": "Government Asset / Property Number",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G007",
        "name": "Contract Number / PIID",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G008",
        "name": "Task Order Number",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G009",
        "name": "Unique Item Identifier (UII)",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G010",
        "name": "IUID / 2D Data Matrix",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G011",
        "name": "Serial Number",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G012",
        "name": "National Stock Number (NSN)",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G013",
        "name": "Manufacturer / CAGE Code",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G014",
        "name": "Part Number",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G015",
        "name": "Model Number",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G016",
        "name": "Government Property - Accountable Contract",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G017",
        "name": "Government Asset Location",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G018",
        "name": "Sensitive Government Property",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G019",
        "name": "CUI / Controlled Unclassified Information",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
    {
        "code": "G020",
        "name": "Government Contractor Equipment Identification",
        "industry": "government",
        "category": "stickers",
        "product_type": "fleet_decal",
    },
]


class Command(BaseCommand):
    help = "Load THE LABEL GROUP's initial 100 sticker products."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Loading THE LABEL GROUP sticker catalogue..."
            )
        )
        self.stdout.write("")

        for item in PRODUCTS:
            code = item["code"]

            existing = Product.objects.filter(
                product_code__iexact=code
            ).first()

            if existing:
                skipped_count += 1
                self.stdout.write(
                    f"SKIPPED: {code} - {existing.name}"
                )
                continue

            base_slug = slugify(
                f"{code}-{item['name']}"
            )

            slug = base_slug
            counter = 2

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            description = (
                f"{item['name']}. "
                "Professional industrial decal or sticker from "
                "THE LABEL GROUP."
            )

            Product.objects.create(
                name=item["name"],
                product_code=code,
                product_type=item["product_type"],
                slug=slug,
                description=description,
                category=item["category"],
                industry=item["industry"],
                brand="THE LABEL GROUP",
                price=None,
                discount_price=None,
                stock=0,
                is_custom=False,
                is_available=True,
                is_featured=False,
            )

            created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"CREATED: {code} - {item['name']}"
                )
            )

        total_count = Product.objects.count()

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {created_count}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Skipped existing: {skipped_count}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Total products now in database: {total_count}"
            )
        )
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Sticker catalogue loading complete."
            )
        )
        self.stdout.write(
            "Images and prices can now be added from the Staff Dashboard."
        )
        self.stdout.write("")