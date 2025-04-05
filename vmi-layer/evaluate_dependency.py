import pyparsing as pp

# Define an identifier: must start with a letter or underscore and can contain alphanumerics/underscores.
identifier = pp.Word(pp.alphas + "_", pp.alphanums + "_")
# When an identifier is parsed, wrap it in defined(...).
identifier.setParseAction(lambda t: f"defined({t[0]})")

# Define the expression grammar using infixNotation:
# '+' has higher precedence (logical AND) than ',' (logical OR)
expr = pp.infixNotation(identifier,
    [
        (pp.Literal('+'), 2, pp.opAssoc.LEFT),  # '+' is the AND operator
        (pp.Literal(','), 2, pp.opAssoc.LEFT),  # ',' is the OR operator
    ]
)

# Recursive function to convert the parse tree into a string with proper operators.
def eval_expr(parsed):
    if isinstance(parsed, str):
        return parsed
    if isinstance(parsed, list):
        # if the list has a single element, reduce it
        if len(parsed) == 1:
            return eval_expr(parsed[0])
        # Otherwise, process left-associative operators
        left = eval_expr(parsed[0])
        i = 1
        while i < len(parsed):
            op = parsed[i]
            right = eval_expr(parsed[i+1])
            if op == '+':
                left = f"({left} && {right})"
            elif op == ',':
                left = f"({left} || {right})"
            i += 2
        return left


evaluate_dependency = lambda text: eval_expr(expr.parseString(text, parseAll=True).asList())
