TRIGGERS = ["calculate", "calc", "math", "/calc"]
DESCRIPTION = "Simple math calculator — try: calc 2 + 2"

import ast
import operator as _op

# Whitelist of safe AST node types and operators
_SAFE_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow, ast.USub, ast.UAdd,
)
_BINARY_OPS = {
    ast.Add:      _op.add,
    ast.Sub:      _op.sub,
    ast.Mult:     _op.mul,
    ast.Div:      _op.truediv,
    ast.FloorDiv: _op.floordiv,
    ast.Mod:      _op.mod,
    ast.Pow:      _op.pow,
}
_UNARY_OPS = {
    ast.USub: _op.neg,
    ast.UAdd: _op.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left  = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _BINARY_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def handle(message: str) -> str:
    try:
        expr = message.lower()
        for word in ["calculate", "calc", "math", "/calc"]:
            expr = expr.replace(word, "")
        expr = expr.strip()
        if not expr:
            return "Usage: calc 2 + 2"
        tree = ast.parse(expr, mode="eval")
        # Reject any node types not in the safe whitelist
        for node in ast.walk(tree):
            if not isinstance(node, _SAFE_NODES):
                return "❌  Only basic arithmetic is supported. Try: calc 10 * 5"
        result = _safe_eval(tree)
        return f"✅  {expr} = {result}"
    except ZeroDivisionError:
        return "❌  Division by zero."
    except Exception:
        return "❌  Invalid math expression. Try: calc 10 * 5"
