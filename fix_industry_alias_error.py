from pathlib import Path
import re

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")

pattern = re.compile(
    r"(?m)^([ \t]*)matching_industries = industry_aliases\.get\(\n"
    r"[\s\S]*?^\1\)"
)

def replace_alias_block(match):
    indent = match.group(1)
    inner = indent + "    "
    lines = [
        indent + "industry_alias_map = {",
        inner + "'waste': ['waste', 'waste_company', 'waste_companies'],",
        inner + "'waste_companies': ['waste', 'waste_company', 'waste_companies'],",
        inner + "'government': ['government', 'government_contractor', 'government_contractors'],",
        inner + "'government_contractor': ['government', 'government_contractor', 'government_contractors'],",
        inner + "'government_contractors': ['government', 'government_contractor', 'government_contractors'],",
        inner + "'construction': ['construction', 'construction_contractor', 'construction_contractors'],",
        inner + "'construction_contractors': ['construction', 'construction_contractor', 'construction_contractors'],",
        inner + "'pool': ['pool', 'pools', 'pool_company', 'pool_companies'],",
        inner + "'pools': ['pool', 'pools', 'pool_company', 'pool_companies'],",
        inner + "'pool_companies': ['pool', 'pools', 'pool_company', 'pool_companies'],",
        inner + "'motor': ['motor', 'truck', 'truck_motor_car', 'truck_motor', 'car'],",
        inner + "'truck': ['motor', 'truck', 'truck_motor_car', 'truck_motor', 'car'],",
        inner + "'truck_motor_car': ['motor', 'truck', 'truck_motor_car', 'truck_motor', 'car'],",
        indent + "}",
        indent + "matching_industries = industry_alias_map.get(",
        inner + "filter_key, [industry_filter]",
        indent + ")",
    ]
    return "\n".join(lines)

updated, count = pattern.subn(replace_alias_block, source, count=1)

if count != 1:
    raise RuntimeError(
        f"Expected one undefined industry_aliases lookup; found {count}. "
        "The file was not modified."
    )

compile(updated, str(path), "exec")

if "industry_aliases.get(" in updated:
    raise RuntimeError("An unresolved industry_aliases lookup remains.")

path.write_text(updated, encoding="utf-8")
print("Fixed the undefined industry_aliases reference.")
