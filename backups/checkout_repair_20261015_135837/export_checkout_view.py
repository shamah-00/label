import ast
from pathlib import Path

source_path = Path(r"products/views.py")
source = source_path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)

function = next(
    (
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "checkout"
    ),
    None,
)

if function is None:
    raise SystemExit("Could not find checkout() in products/views.py")

lines = source.splitlines()
result = "\n".join(lines[function.lineno - 1:function.end_lineno])
Path("checkout_view_review.txt").write_text(result, encoding="utf-8")
print(f"Checkout view exported: checkout_view_review.txt")
print(f"Lines: {function.lineno}-{function.end_lineno}")
print("No website files or database records were changed.")
