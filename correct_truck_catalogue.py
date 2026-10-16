from django.db import transaction
from products.models import Product

# code: (name, description, size, material, finish, application, buyer notes)
items = {
"DGO": ("Gasoline Only", "Fuel identification decal for clearly marking gasoline-only fill points on commercial trucks and equipment.", '5" × 3"', "4 mil high-tack outdoor vinyl", "Gloss", "Truck fuel tanks, fuel-fill points, and equipment", "Permanent outdoor adhesive. Confirm the intended fuel-fill location and application surface before ordering."),
"320": ("Diesel Only", "Durable fuel identification decal for diesel-only tanks, fill points, and commercial equipment.", '5" × 3"', "4 mil high-tack outdoor vinyl", "Gloss", "Truck fuel tanks, diesel fill points, and heavy equipment", "Permanent outdoor adhesive. Confirm the intended fuel-fill location before ordering."),
"DMO": ("Mixed Fuel Only", "Clear fuel identification decal marking equipment designated for mixed-fuel use.", '5" × 3"', "4 mil high-tack outdoor vinyl", "Gloss", "Commercial trucks, equipment, and fuel compartments", "Permanent outdoor adhesive. Verify the intended fuel application before installation."),
"DHO": ("Hydraulics Only", "Hydraulic-fluid identification decal designed to clearly identify hydraulic fill and service points.", '5" × 3"', "4 mil high-tack chemical-resistant outdoor vinyl", "Gloss", "Hydraulic tanks, construction trucks, and heavy equipment", "Permanent adhesive. Chemical-resistant material is recommended for areas exposed to hydraulic oil and fluids."),
"I711": ("DOT C2 Reflective / Conspicuity Tape", "Red-and-white retroreflective tape designed to improve the visibility of commercial trucks and trailers in low-light conditions.", '2" × 150 ft roll', "DOT C2-compliant retroreflective sheeting", "Reflective", "Commercial trucks, trailers, and vehicle conspicuity marking", "Sold by roll. Confirm required placement and applicable vehicle-marking requirements before installation."),
"312": ("Caution — Vehicle Stops & Backs Frequently / Wide Right Turns", "Large high-visibility warning decal alerting motorists and pedestrians that the vehicle may stop, back up, and make wide right turns.", '24" × 75"', "4 mil high-tack outdoor vinyl", "High-visibility gloss", "Commercial waste trucks, service trucks, and heavy vehicles", "Large-format decal. Measure the intended mounting area carefully before ordering."),
"333": ("Stay Back 200 Feet", "Heavy-duty truck safety decal warning motorists and pedestrians to maintain a safe distance behind the vehicle.", '14" × 12"', "4 mil high-tack outdoor vinyl", "Gloss", "Rear of commercial trucks, waste vehicles, and heavy equipment", "Permanent outdoor adhesive. Apply to a clean, smooth, dry surface."),
"362": ("If You Can't See My Mirrors, I Can't See You", "High-visibility blind-spot warning decal designed to alert motorists about commercial truck visibility limitations.", '12" × 12"', "4 mil high-tack outdoor vinyl", "Gloss", "Truck rear, side panels, and fleet vehicles", "Best applied to a clean, smooth vehicle surface. Suitable for long-term outdoor exposure."),
"NCU": ("No Personal Cell Phone Usage", "Fleet-safety decal communicating that personal cell-phone use is prohibited during vehicle operation or designated work activities.", '2.75" × 5.25"', "4 mil high-tack outdoor vinyl", "Matte or Gloss", "Truck cabs, fleet vehicles, and equipment", "Permanent adhesive. Matte finish is recommended where reduced glare is preferred."),
"T010": ("USDOT Number", "Professional vehicle-identification decal intended for displaying a carrier's USDOT number in a clear, readable format.", '2" × 10"', "Premium outdoor vinyl lettering", "Gloss", "Commercial truck doors and vehicle sides", "Customer provides the exact USDOT number. Verify applicable federal and state display requirements before ordering."),
"T011": ("MC Number", "Commercial carrier identification decal for displaying the applicable motor carrier number.", '2" × 6"', "Premium outdoor vinyl lettering", "Gloss", "Commercial truck doors and fleet vehicles", "Customer provides the exact MC number. Verify required placement and lettering requirements before installation."),
"T012": ("Company Name", "Custom truck-door lettering designed to prominently display the legal or operating name of the transportation company.", '3" × 18"', "Premium outdoor vinyl lettering", "Gloss", "Truck doors, fleet vehicles, vans, and service vehicles", "Customer provides the exact company name. Confirm spelling and measure the available door area before ordering."),
"T013": ("City / State", "Compact vehicle-identification decal for displaying the carrier's operating city and state.", '2" × 12"', "Premium outdoor vinyl lettering", "Gloss", "Commercial truck doors and fleet vehicles", "Customer provides the exact city and state. Verify applicable carrier-marking requirements."),
"T014": ("GVWR", "Commercial vehicle identification decal used for displaying the Gross Vehicle Weight Rating.", '2" × 8"', "Premium outdoor vinyl", "Gloss", "Truck bodies, commercial vehicles, and equipment", "Customer supplies the correct GVWR value. Confirm applicable regulatory display requirements."),
"T015": ("Unit / Truck Number", "Fleet identification decal used to assign and clearly display an individual truck or equipment unit number.", '3" × 8"', "Premium outdoor vinyl lettering", "Gloss", "Fleet trucks, trailers, service vehicles, and equipment", "Customer provides the exact unit number. Custom numbering available."),
"T016": ("Fleet Number", "Durable fleet-management decal identifying an individual vehicle within a commercial fleet.", '3" × 8"', "Premium outdoor vinyl lettering", "Gloss", "Commercial truck and fleet identification", "Customer provides the fleet number. Suitable for long-term outdoor vehicle use."),
"T017": ("CA / State Carrier Number", "State carrier identification decal for displaying a California or applicable state carrier number in a clear, high-contrast format.", '2" × 12"', "Premium outdoor vinyl lettering", "Gloss", "Commercial truck doors and carrier vehicles", "Customer provides the exact carrier number. Confirm state-specific marking requirements before ordering."),
"T018": ("KYU / State Registration Number", "Vehicle identification decal for displaying a KYU or applicable state registration number.", '2" × 14"', "Premium outdoor vinyl lettering", "Gloss", "Commercial carrier trucks and fleet vehicles", "Customer provides the exact registration number. Verify state-specific size, placement, and display requirements."),
"T019": ("Slow Down / Give Trucks Space", "High-visibility commercial-truck safety decal encouraging motorists to reduce speed and provide heavy vehicles adequate operating space.", '5" × 18"', "4 mil high-tack outdoor vinyl", "High-visibility gloss", "Commercial trucks, waste trucks, trailers, and fleet vehicles", "Permanent outdoor adhesive. Larger custom sizes may be recommended for increased visibility."),
"T020": ("Oversize / Wide Load", "High-visibility identification decal used to clearly identify oversized or wide-load transportation equipment.", '12" × 48"', "High-visibility outdoor vinyl", "Gloss; reflective upgrade available", "Oversize-load trucks, trailers, heavy-haul equipment, and transport vehicles", "Confirm applicable state requirements before ordering. Reflective material may be required depending on the vehicle, load, and jurisdiction."),
}

truck_industry = "truck_motor_car"
updated = []
problems = []

with transaction.atomic():
    for code, data in items.items():
        name, description, size, material, finish, application, notes = data
        matches = list(Product.objects.filter(product_code=code).order_by("id"))

        if not matches:
            problems.append(f"MISSING PRODUCT CODE: {code} — {name}")
            continue

        # DGO has an older duplicate-looking Gasoline Only record.
        # Only update the intended record already carrying code DGO.
        product = matches[0]
        product.name = name
        product.industry = truck_industry
        product.description = (
            f"{description}\n\n"
            f"Standard Size: {size}\n"
            f"Ideal Material: {material}\n"
            f"Finish: {finish}\n"
            f"Primary Application: {application}\n"
            f"What to Include / Buyer's Notes: {notes}"
        )
        product.material = material
        product.finish = finish
        product.adhesive = notes
        product.save(update_fields=[
            "name", "industry", "description", "material", "finish", "adhesive"
        ])
        updated.append((code, product.pk, name))

    # Move known construction products out of Truck & Motor.
    construction_codes = ["C001", "C006", "C011", "C016", "C018"]
    for code in construction_codes:
        Product.objects.filter(product_code=code).update(industry="construction")

    # Government serial-number product belongs in Government.
    Product.objects.filter(product_code="G011").update(industry="government")

    # Keep the old duplicate Gasoline Only/C018 record in the database,
    # but hide it from the public catalogue. Do not delete it.
    old_duplicate = Product.objects.filter(pk=1, product_code="C018").first()
    if old_duplicate:
        old_duplicate.is_available = False
        old_duplicate.save(update_fields=["is_available"])

print("\n=== TRUCK CATALOGUE UPDATE RESULTS ===")
for code, pk, name in updated:
    print(f"UPDATED | {code} | ID {pk} | {name}")

print(f"\nUpdated truck products: {len(updated)} of {len(items)}")
print("\n=== PRODUCTS STILL MISSING ===")
if problems:
    for problem in problems:
        print(problem)
else:
    print("None. All 20 requested product codes were found.")

print("\n=== VERIFY INDUSTRY ASSIGNMENTS ===")
for p in Product.objects.filter(product_code__in=list(items)).order_by("id"):
    print(f"{p.product_code} | {p.name} | {p.industry} | ${p.price}")

print("\nNOTE: Existing prices, stock levels, and images were not changed.")
