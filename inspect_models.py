import ast
from pathlib import Path

source = Path("products/models.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name in {"Order", "OrderItem", "Shipment"}:
        print("\n" + "=" * 60)
        print(node.name)
        print("=" * 60)
        print(ast.get_source_segment(source, node))
