from main import (
    Stack,
    LexToken,
    lex_expression,
    PrecedenceClimbingParser,
    evaluate_expression,
    perform_arithmetic,
    weight_of,
)


def header(title):
    print()
    print("=" * 66)
    print(f"  {title}")
    print("=" * 66)


def case(label, expression, expected):
    try:
        actual = evaluate_expression(expression)
        if actual == expected:
            print(f"  [PASS] {label}: {expression} -> {actual}")
            return True
        else:
            print(f"  [FAIL] {label}: {expression} -> got {actual}, expected {expected}")
            return False
    except Exception as ex:
        print(f"  [FAIL] {label}: {expression} -> EXCEPTION {type(ex).__name__}: {ex}")
        return False


def err_case(label, expression):
    try:
        val = evaluate_expression(expression)
        print(f"  [FAIL] {label}: {expression} -> should have errored, got {val}")
        return False
    except (ValueError, ZeroDivisionError, IndexError):
        print(f"  [PASS] {label}: {expression} -> correctly raised error")
        return True
    except Exception as ex:
        print(f"  [FAIL] {label}: {expression} -> unexpected {type(ex).__name__}: {ex}")
        return False


def test_stack():
    header("DYNAMIC-ARRAY STACK (v3) UNIT TESTS — INCLUDING CAPACITY")
    ok = 0
    bad = 0

    s = Stack()
    try:
        assert s.is_empty() is True and s.size() == 0
        print("  [PASS] new Stack: is_empty() True, size() 0")
        ok += 1
    except AssertionError:
        print("  [FAIL] empty stack invariants")
        bad += 1

    try:
        assert s.capacity() == Stack._DEFAULT_CAPACITY
        print("  [PASS] new Stack initial capacity == _DEFAULT_CAPACITY")
        ok += 1
    except AssertionError:
        print("  [FAIL] initial capacity value")
        bad += 1

    try:
        s.push(10)
        assert s.peek() == 10 and s.size() == 1 and s.is_empty() is False
        print("  [PASS] push(10): peek == 10, size 1")
        ok += 1
    except AssertionError:
        print("  [FAIL] push + peek")
        bad += 1

    try:
        for i in range(20, 25):
            s.push(i)
        assert s.size() == 6
        assert s.capacity() >= 6 and s.capacity() > Stack._DEFAULT_CAPACITY
        print("  [PASS] capacity doubled (manual _double_capacity triggered)")
        ok += 1
    except AssertionError:
        print("  [FAIL] capacity doubling behaviour")
        bad += 1

    try:
        top = s.pop()
        assert top == 24 and s.size() == 5 and s.peek() == 23
        print("  [PASS] pop returns top value, LIFO order correct")
        ok += 1
    except AssertionError:
        print("  [FAIL] pop order")
        bad += 1

    try:
        while not s.is_empty():
            s.pop()
        assert s.size() == 0 and s.is_empty()
        print("  [PASS] all elements popped -> stack empty")
        ok += 1
    except AssertionError:
        print("  [FAIL] complete drain empty check")
        bad += 1

    try:
        s.pop()
        print("  [FAIL] pop empty -> should have raised IndexError")
        bad += 1
    except IndexError:
        print("  [PASS] pop on empty raises IndexError")
        ok += 1

    try:
        s.peek()
        print("  [FAIL] peek empty -> should have raised IndexError")
        bad += 1
    except IndexError:
        print("  [PASS] peek on empty raises IndexError")
        ok += 1

    try:
        big = Stack()
        for i in range(512):
            big.push(i)
        for i in range(512):
            assert big.size() == 512 - i
            assert big.pop() == 511 - i
        print("  [PASS] 512-item stress push+pop: correct LIFO order + half-shrinking")
        ok += 1
    except AssertionError:
        print("  [FAIL] stress push/pop LIFO order")
        bad += 1

    print(f"  Stack: {ok} passed, {bad} failed")
    return bad == 0


def test_lexer_and_parser_structure():
    header("LEXER + PARSER VALIDATION TESTS")
    ok = 0
    bad = 0

    try:
        toks = lex_expression("3+5*2")
        kinds = [t.kind for t in toks]
        # NUM, PLUS, NUM, STAR, NUM, EOF
        assert kinds == [LexToken.NUM, LexToken.PLUS, LexToken.NUM, LexToken.STAR, LexToken.NUM, LexToken.EOF]
        print("  [PASS] lex '3+5*2' kind order correct (NUM, PLUS, NUM, STAR, NUM, EOF)")
        ok += 1
    except AssertionError as ex:
        print(f"  [FAIL] lex kind order: {ex}")
        bad += 1

    try:
        toks = lex_expression("(3+5)")
        kinds = [t.kind for t in toks]
        assert kinds == [LexToken.LPAREN, LexToken.NUM, LexToken.PLUS, LexToken.NUM, LexToken.RPAREN, LexToken.EOF]
        print("  [PASS] lex '(3+5)' includes LP and RP tokens at correct positions")
        ok += 1
    except AssertionError:
        print("  [FAIL] lex paren tokens")
        bad += 1

    try:
        assert weight_of(LexToken.STAR) == 2 and weight_of(LexToken.PLUS) == 1
        assert weight_of(LexToken.STAR) > weight_of(LexToken.MINUS)
        print("  [PASS] operator weights: */ priority 2, +- priority 1")
        ok += 1
    except AssertionError:
        print("  [FAIL] operator weight values")
        bad += 1

    try:
        # Correct operand order for subtraction -> (10 - 3) - 2 = 5
        p = PrecedenceClimbingParser(lex_expression("10-3-2"))
        assert p.parse_and_evaluate() == 5
        # Correct operand order for division -> (8 / 2) / 2 = 2
        p2 = PrecedenceClimbingParser(lex_expression("8/2/2"))
        assert p2.parse_and_evaluate() == 2
        print("  [PASS] parser: left-associative subtraction + division produce correct numeric order")
        ok += 1
    except AssertionError:
        print("  [FAIL] operand order / associativity")
        bad += 1

    try:
        assert perform_arithmetic(LexToken.MINUS, 3, 10) == 7  # rhs=3, lhs=10 -> 10 - 3
        assert perform_arithmetic(LexToken.SLASH, 2, 8) == 4    # rhs=2, lhs=8 -> 8 / 2
        print("  [PASS] perform_arithmetic(rhs,lhs): correct lhs/rhs parameter order")
        ok += 1
    except AssertionError:
        print("  [FAIL] perform_arithmetic parameter order")
        bad += 1

    print(f"  Lexer/parser structural: {ok} passed, {bad} failed")
    return bad == 0


def test_mandatory_and_expressions():
    header("MANDATORY 7 TEST CASES (per brief)")
    total_ok = 0
    total_fail = 0

    mandatory = [
        ("M1 Basic add",          "3+5",          8),
        ("M2 Basic multiply",     "5*4",          20),
        ("M3 Precedence * over +","3+5*2",        13),
        ("M4 Parens override",    "(3+5)*2",      16),
        ("M5 Int division",       "10/2",         5),
        ("M6 Decimal division",   "3/4",          0.75),
        ("M7 Complex mix",        "10-(2+3)*4",   -10),
    ]
    for lbl, expr, want in mandatory:
        if case(lbl, expr, want):
            total_ok += 1
        else:
            total_fail += 1

    header("EXTENDED VALIDATION TESTS")
    extra = [
        ("A1 Spaced addition",    "100 + 200",             300),
        ("A2 Decimal sum",        "12.5 + 7.5",            20),
        ("A3 L-assoc subtraction","10 - 3 - 2",            5),
        ("A4 L-assoc division",   "8 / 2 / 2",             2),
        ("A5 Mixed precedence",   "2 * 3 + 4 * 5",         26),
        ("A6 Nested parens",      "((2+3)*(4-1))",         15),
        ("A7 Parens with div",    "(10 + 5) / (3 - 0)",    5),
        ("A8 Mixed operators",    "5 * (2 + 3) / 5",       5),
        ("A9 Decimal multiply",   "2.5 * 4",               10),
        ("A10 Repeat decimal",    "100 / 3",               100 / 3),
        ("A11 Unary minus",       "-5+3",                  -2),
        ("A12 Unary plus",        "+7-2",                  5),
    ]
    for lbl, expr, want in extra:
        if case(lbl, expr, want):
            total_ok += 1
        else:
            total_fail += 1

    header("ERROR HANDLING TESTS")
    errors = [
        ("E1 Division by zero",      "10/0"),
        ("E2 Missing close paren",   "(3+5"),
        ("E3 Missing open paren",    "3+5)"),
        ("E4 Letter characters",     "abc"),
        ("E5 Bad symbol",            "5*@3"),
        ("E6 Double decimal",        "..5"),
        ("E7 Multiple decimals",     "3..2"),
        ("E8 Empty expression",      ""),
    ]
    for lbl, expr in errors:
        if err_case(lbl, expr):
            total_ok += 1
        else:
            total_fail += 1

    print()
    print(f"  Expression evaluator: {total_ok} passed, {total_fail} failed")
    return total_fail == 0


def main():
    print()
    print("*" * 66)
    print("   DCOMP320 ASSIGNMENT 1 — VERSION 3.0  OFFICIAL TEST SUITE")
    print("   Dynamic-Array Stack + Recursive-Descent Precedence Climbing")
    print("*" * 66)

    s_ok = test_stack()
    lp_ok = test_lexer_and_parser_structure()
    e_ok = test_mandatory_and_expressions()

    print()
    print("=" * 66)
    print("  FINAL SUMMARY")
    print("=" * 66)
    if s_ok and lp_ok and e_ok:
        print("  ALL TESTS PASSED — Submission ready.")
        print("=" * 66)
        return 0
    else:
        if not s_ok:   print("  ISSUE: Stack unit tests have failures")
        if not lp_ok:  print("  ISSUE: Lexer/parser structural tests have failures")
        if not e_ok:   print("  ISSUE: Evaluator tests have failures")
        print("  Correct failures before final submission.")
        print("=" * 66)
        return 1


if __name__ == "__main__":
    exit(main())
