import ast
from pathlib import Path

for filename in ["products/urls.py", "products/models.py"]:
    path = Path(filename)
    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)
    source = path.read_text(encoding="utf-8-sig")
    if filename.endswith("urls.py"):
        print(source)
    else:
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in {
                "Order", "OrderItem", "Shipment"
            }:
                print(ast.get_source_segment(source, node))
