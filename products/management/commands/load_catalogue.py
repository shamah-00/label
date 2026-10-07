from django.core.management.base import BaseCommand
from products.models import Product


CATALOGUE = {
    "truck_motor_car": [
        ("DGO", "Gasoline Only"),
        ("320", "Diesel Only"),
        ("DMO", "Mixed Fuel Only"),
        ("DHO", "Hydraulics Only"),
        ("I711", "DOT C2 Reflective / Conspicuity Tape"),
        ("312", "Caution — Vehicle Stops & Backs Frequently / Wide Right Turns"),
        ("333", "Stay Back 200 Feet"),
        ("362", "If You Can't See My Mirrors, I Can't See You"),
        ("NCU", "No Personal Cell Phone Usage"),
        ("T010", "USDOT Number"),
        ("T011", "MC Number"),
        ("T012", "Company Name"),
        ("T013", "City / State"),
        ("T014", "GVWR"),
        ("T015", "Unit / Truck Number"),
        ("T016", "Fleet Number"),
        ("T017", "CA / State Carrier Number"),
        ("T018", "KYU / State Registration Number"),
        ("T019", "Slow Down / Give Trucks Space"),
        ("T020", "Oversize / Wide Load"),
    ],

    "waste": [
        ("042R", "Keep Off / Do Not Play on or Around Container"),
        ("032", "Keep Off Container / Load Evenly"),
        ("072", "Multi-Message Container Safety"),
        ("071", "Multi-Message Waste Safety"),
        ("066", "Garbage Only"),
        ("089", "Danger — Do Not Park in Front of Container"),
        ("305", "Danger — Striking Hazard"),
        ("306", "Danger — Crushing Hazard"),
        ("301", "Danger — Pinch Point"),
        ("310", "Ladder Safety"),
        ("062", "Watch Overhead Wires"),
        ("337", "No Parking / Tow Away Zone"),
        ("043", "Cardboard Only Recycling"),
        ("074", "Paper & Cardboard Recycling"),
        ("031A", "Commingled Recyclables Only"),
        ("343", "Single Stream Recycling"),
        ("338", "Full-Color Single Stream Recycling"),
        ("335", "Single Stream — No Glass"),
        ("344", "No Plastic Bags"),
        ("315", "Yard Waste Only"),
    ],

    "construction": [
        ("C001", "Danger — Electrocution Hazard / Crane Not Insulated"),
        ("C002", "Standard Crane & Derrick Signals"),
        ("C003", "Check Fluid Levels"),
        ("C004", "This Machine Pays Your Salary"),
        ("C005", "DEF Fluid Only"),
        ("C006", "Diesel"),
        ("C007", "Warning — Rotating Shafts"),
        ("C008", "Warning — Operator Stay Clear"),
        ("C009", "Hydraulic Oil"),
        ("C010", "Attention — Operators Are Responsible"),
        ("C011", "Danger — Stand Clear of Swing Area"),
        ("C012", "Danger — Outrigger Contact"),
        ("C013", "Danger — Electrocution Hazard"),
        ("C014", "Danger — Collapsing Boom Hazard"),
        ("C015", "No Step"),
        ("C016", "Danger — Crushing Hazard"),
        ("C017", "Battery Disconnect Switch"),
        ("C018", "Gasoline Only"),
        ("C019", "Fire Extinguisher Inside"),
        ("C020", "First Aid / Fire Extinguisher"),
    ],

    "pool": [
        ("P001", "Chlorine Danger"),
        ("P002", "Muriatic Acid Danger"),
        ("P003", "Sodium Hypochlorite Danger"),
        ("P004", "Danger — Hazardous Chemicals"),
        ("P005", "Corrosion / Hydrochloric Acid"),
        ("P006", "Danger — Do Not Mix Chemicals"),
        ("P007", "Authorized Personnel Only"),
        ("P008", "Pool Chemical Storage — Caution"),
        ("P009", "Calcium Hypochlorite / Oxidizer"),
        ("P010", "Pool Service"),
        ("P011", "Weekly Pool Service By"),
        ("P012", "Pool Equipment Service"),
        ("P013", "Pool Filter Service Record"),
        ("P014", "Date Cleaned"),
        ("P015", "Starting Filter Pressure"),
        ("P016", "Pool Pump Service"),
        ("P017", "Pool Heater Service"),
        ("P018", "Pool Technician / Company Contact"),
        ("P019", "No diving"),
        ("P020", "slippery"),
    ],

    "government": [
        ("G001", "PROPERTY OF U.S. GOVERNMENT"),
        ("G002", "GOVERNMENT PROPERTY"),
        ("G003", "GOVERNMENT-FURNISHED PROPERTY (GFP)"),
        ("G004", "CONTRACTOR-ACQUIRED PROPERTY (CAP)"),
        ("G005", "U.S. GOVERNMENT PROPERTY — DO NOT REMOVE"),
        ("G006", "Government Asset / Property Number"),
        ("G007", "Contract Number / PIID"),
        ("G008", "Task Order Number"),
        ("G009", "Unique Item Identifier (UII)"),
        ("G010", "IUID / 2D Data Matrix"),
        ("G011", "Serial Number"),
        ("G012", "National Stock Number (NSN)"),
        ("G013", "Manufacturer / CAGE Code"),
        ("G014", "Part Number"),
        ("G015", "Model Number"),
        ("G016", "Government Property — Accountable Contract"),
        ("G017", "Government Asset Location"),
        ("G018", "Sensitive Government Property"),
        ("G019", "CUI / Controlled Unclassified Information"),
        ("G020", "Government Contractor Equipment Identification"),
    ],
}


class Command(BaseCommand):
    help = "Load The Label Group's 100-sticker catalogue."


    def get_product_type(self, industry, code, name):
        text = f"{code} {name}".lower()

        if industry == "truck_motor_car":
            if "reflective" in text or code == "I711":
                return "reflective_label"
            if any(word in text for word in ["fuel", "gasoline", "diesel", "hydraulic"]):
                return "fleet_decal"
            if any(word in text for word in ["truck", "vehicle", "mirror", "back", "parking", "load", "dot", "usdot", "gvwr", "number", "carrier"]):
                return "truck_decal"
            return "truck_decal"

        if industry == "government":
            return "safety_decal"

        if industry == "pool":
            if any(word in text for word in ["service", "pressure", "cleaned", "technician", "pump", "heater", "filter"]):
                return "facility_sign"
            return "safety_decal"

        if industry == "construction":
            if any(word in text for word in ["crane", "boom", "shaft", "outrigger", "machine", "operator"]):
                return "safety_decal"
            if any(word in text for word in ["diesel", "gasoline", "hydraulic", "fluid", "def", "battery"]):
                return "fleet_decal"
            return "safety_decal"

        if industry == "waste":
            if any(word in text for word in ["recycling", "cardboard", "paper", "plastic", "yard waste"]):
                return "recycling_label"
            if any(word in text for word in ["container", "dumpster", "garbage", "parking", "overhead", "ladder"]):
                return "container_decal"
            return "safety_decal"

        return "other"
    def handle(self, *args, **options):
        created = 0
        updated = 0

        industry_names = {
            "truck_motor_car": "Truck / Motor / Car Decals",
            "government": "Government Contractor Decals",
            "pool": "Pool Decals",
            "construction": "Construction Decals",
            "waste": "Waste Company Decals",
        }

        for industry, products in CATALOGUE.items():
            for code, name in products:
                slug = f"{code.lower()}-{name.lower()}"
                slug = "".join(
                    char if char.isalnum() else "-"
                    for char in slug
                )
                while "--" in slug:
                    slug = slug.replace("--", "-")
                slug = slug.strip("-")

                product, was_created = Product.objects.update_or_create(
                    product_code=code,
                    defaults={
                        "name": name,
                        "slug": slug,
                        "description": (
                            f"{name}. "
                            f"Professional industrial decal or sticker "
                            f"from The Label Group."
                        ),
                        "category": "stickers",
                        "industry": industry,
                        "product_type": self.get_product_type(industry, code, name),
                        "price": None,
                        "discount_price": None,
                        "stock": 0,
                        "is_custom": False,
                        "is_available": True,
                        "is_featured": False,
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogue complete. Created: {created}. Updated: {updated}. "
                f"Total products: {Product.objects.count()}."
            )
        )


