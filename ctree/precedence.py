"""
Utilities for determining precedence in C, with the goal of minimizing the
number of parentheses in the generated code.
"""

from ctree.c.nodes import UnaryOp, BinaryOp, TernaryOp, Cast

# ---------------------------------------------------------------------------
# dictionary of node class -> precedence ids, where 1 denotes the highest-
# precedence operator and 18 is the lowest. This is how the table on
# wikipedia does it, but we flip it later so larger numbers mean higher
# precedence. For the origin of this table see
# http://en.wikipedia.org/wiki/Operators_in_C_and_C%2B%2B#Operator_precedence
_EXPR_TO_PRECEDENCE = {
    'PostInc': 2,
    'PostDec': 2,
    'FunctionCall': 2,
    'ArrayRef': 2,
    'Dot': 2,
    'Arrow': 2,

    'PreInc': 3,
    'PreDec': 3,
    #'Plus': 3,
    # TODO: work out naming schemes for add/sub unary
    'AddUnary': 3,
    #'Minus': 3,
    'SubUnary': 3,
    'Not': 3,
    'BitNot': 3,
    'Cast': 3,
    'Deref': 3,
    'Ref': 3,
    'SizeOf': 3,

    'Mul': 5,
    'Div': 5,
    'Mod': 5,

    'Add': 6,
    'Sub': 6,

    'BitShL': 7,
    'BitShR': 7,

    'Lt': 8,
    'LtE': 8,
    'Gt': 8,
    'GtE': 8,

    'Eq': 9,
    'NotEq': 9,

    'BitAnd': 10,

    'BitXor': 11,

    'BitOr': 12,

    'And': 13,

    'Or': 14,

    'TernaryOp': 15,

    'Assign': 16,
    'AddAssign': 16,
    'SubAssign': 16,
    'MulAssign': 16,
    'DivAssign': 16,
    'ModAssign': 16,
    'BitShLAssign': 16,
    'BitShRAssign': 16,
    'BitAndAssign': 16,
    'BitXorAssign': 16,
    # 'BitNotAssign': 16,

    'Comma': 18,
}


def get_precedence(node):
    try:
        if isinstance(node, (UnaryOp, BinaryOp)):
            op = type(node.op)
        elif isinstance(node, TernaryOp):
            op = TernaryOp
        elif isinstance(node, Cast):
            op = Cast
        else:
            raise Exception("Cannot determine operator for node %d.\n", node)

        pred = _EXPR_TO_PRECEDENCE[op.__name__]
        # flip precedence so higher numbers mean higher precedence
        return 20 - pred
    except KeyError:
        pass
    raise Exception("Unable to determine precedence for %s." % type(node).__name__)


_PRECEDENCE_ASSOCIATES_LTR = {
    2: True,
    3: False,
    5: True,
    6: True,
    7: True,
    8: True,
    9: True,
    10: True,
    11: True,
    12: True,
    13: True,
    14: True,
    15: False,
    16: False,
    18: True
}


def is_left_associative(node):
    try:
        pred = get_precedence(node)
        return _PRECEDENCE_ASSOCIATES_LTR[20 - pred]
    except (Exception, KeyError):
        pass
    raise Exception("Cannot determine if operator %s is left- or right-associative." % type(node).__name__)
