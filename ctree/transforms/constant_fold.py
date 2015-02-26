import ctree.c.nodes as C
import ast


op_map = {
    C.Op.Add: lambda x, y: x + y,
    C.Op.Div: lambda x, y: x / y,
    C.Op.Mul: lambda x, y: x * y,
    C.Op.Lt: lambda x, y: x < y,
    C.Op.Sub: lambda x, y: x - y,
}


class ConstantFold(ast.NodeTransformer):
    """ TODO: Support all folding situations """
    def fold_add(self, node):
        if isinstance(node.left, C.Constant) and node.left.value == 0:
            return node.right
        elif isinstance(node.right, C.Constant) and node.right.value == 0:
            return node.left
        return node

    def fold_sub(self, node):
        if isinstance(node.left, C.Constant) and node.left.value == 0:
            return C.Sub(node.right)
        elif isinstance(node.right, C.Constant) and node.right.value == 0:
            return node.left
        return node

    def fold_mul(self, node):
        if isinstance(node.left, C.Constant) and node.left.value == 1:
            return node.right
        elif isinstance(node.right, C.Constant) and node.right.value == 1:
            return node.left
        elif isinstance(node.left, C.Constant) and node.left.value == 0:
            return node.left
        elif isinstance(node.right, C.Constant) and node.right.value == 0:
            return node.right
        return node

    def visit_BinaryOp(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        if isinstance(node.left, C.Constant) and \
                isinstance(node.right, C.Constant):
            return C.Constant(op_map[node.op.__class__](
                node.left.value, node.right.value))
        elif isinstance(node.op, C.Op.Add):
            return self.fold_add(node)
        elif isinstance(node.op, C.Op.Sub):
            return self.fold_sub(node)
        elif isinstance(node.op, C.Op.Mul):
            return self.fold_mul(node)
        return node
