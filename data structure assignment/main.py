class Stack:
    _DEFAULT_CAPACITY = 4

    def __init__(self):
        self._capacity = Stack._DEFAULT_CAPACITY
        self._buffer = [None] * self._capacity
        self._length = 0

    def _double_capacity(self):
        new_cap = self._capacity * 2
        new_buf = [None] * new_cap
        for i in range(self._length):
            new_buf[i] = self._buffer[i]
        self._buffer = new_buf
        self._capacity = new_cap

    def _half_capacity(self):
        if self._capacity <= Stack._DEFAULT_CAPACITY:
            return
        new_cap = self._capacity // 2
        new_buf = [None] * new_cap
        for i in range(self._length):
            new_buf[i] = self._buffer[i]
        self._buffer = new_buf
        self._capacity = new_cap

    def push(self, value):
        if self._length == self._capacity:
            self._double_capacity()
        self._buffer[self._length] = value
        self._length += 1

    def pop(self):
        if self._length == 0:
            raise IndexError("Stack.pop(): empty stack")
        self._length -= 1
        value = self._buffer[self._length]
        self._buffer[self._length] = None
        if self._length > 0 and self._length * 4 <= self._capacity:
            self._half_capacity()
        return value

    def peek(self):
        if self._length == 0:
            raise IndexError("Stack.peek(): empty stack")
        return self._buffer[self._length - 1]

    def is_empty(self):
        return self._length == 0

    def size(self):
        return self._length

    def capacity(self):
        return self._capacity

    def __str__(self):
        items = []
        for i in range(self._length):
            items.append(repr(self._buffer[i]))
        return '[' + ', '.join(items) + ']'


class LexToken:
    NUM = 'NUM'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    STAR = 'STAR'
    SLASH = 'SLASH'
    LPAREN = 'LP'
    RPAREN = 'RP'
    EOF = 'EOF'

    __slots__ = ('kind', 'value')

    def __init__(self, kind, value=None):
        self.kind = kind
        self.value = value

    def __repr__(self):
        if self.value is None:
            return f'LexToken({self.kind})'
        return f'LexToken({self.kind}, {self.value!r})'


OP_WEIGHT = {
    LexToken.PLUS: 1,
    LexToken.MINUS: 1,
    LexToken.STAR: 2,
    LexToken.SLASH: 2,
}


def weight_of(token_kind):
    return OP_WEIGHT.get(token_kind, 0)


def perform_arithmetic(binop_kind, right_side, left_side):
    if binop_kind == LexToken.PLUS:
        return left_side + right_side
    elif binop_kind == LexToken.MINUS:
        return left_side - right_side
    elif binop_kind == LexToken.STAR:
        return left_side * right_side
    elif binop_kind == LexToken.SLASH:
        if right_side == 0:
            raise ZeroDivisionError("division by zero encountered")
        return left_side / right_side
    else:
        raise ValueError(f"internal error: unknown binary op {binop_kind}")


def lex_expression(raw_text):
    tokens = []
    i = 0
    n = len(raw_text)
    while i < n:
        ch = raw_text[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch == '.':
            start = i
            dots = 0
            while i < n and (raw_text[i].isdigit() or raw_text[i] == '.'):
                if raw_text[i] == '.':
                    dots += 1
                    if dots > 1:
                        raise ValueError("lex error: number with multiple decimal points")
                i += 1
            chunk = raw_text[start:i]
            if chunk == '.':
                raise ValueError("lex error: number is just a decimal point")
            tokens.append(LexToken(LexToken.NUM, float(chunk)))
            continue
        if ch == '+':
            tokens.append(LexToken(LexToken.PLUS))
            i += 1
            continue
        if ch == '-':
            tokens.append(LexToken(LexToken.MINUS))
            i += 1
            continue
        if ch == '*':
            tokens.append(LexToken(LexToken.STAR))
            i += 1
            continue
        if ch == '/':
            tokens.append(LexToken(LexToken.SLASH))
            i += 1
            continue
        if ch == '(':
            tokens.append(LexToken(LexToken.LPAREN))
            i += 1
            continue
        if ch == ')':
            tokens.append(LexToken(LexToken.RPAREN))
            i += 1
            continue
        raise ValueError(f"lex error: disallowed character '{ch}'")
    tokens.append(LexToken(LexToken.EOF))
    return tokens


class PrecedenceClimbingParser:
    def __init__(self, token_stream):
        self._tokens = list(token_stream)
        self._pos = 0
        self._intermediate_ops = Stack()
        self._intermediate_vals = Stack()

    def _current(self):
        return self._tokens[self._pos]

    def _advance(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match(self, kind):
        if self._current().kind == kind:
            return self._advance()
        return None

    def _apply_top_binary(self):
        if self._intermediate_ops.is_empty():
            raise ValueError("parser error: operator stack unexpectedly empty")
        if self._intermediate_vals.size() < 2:
            raise ValueError("parser error: insufficient values for binary operator")
        op = self._intermediate_ops.pop()
        rhs = self._intermediate_vals.pop()
        lhs = self._intermediate_vals.pop()
        self._intermediate_vals.push(perform_arithmetic(op, rhs, lhs))

    def _reduce_while_ge(self, weight):
        while (not self._intermediate_ops.is_empty()) and weight_of(self._intermediate_ops.peek()) >= weight:
            self._apply_top_binary()

    def _parse_primary(self):
        tok = self._current()
        if tok.kind == LexToken.NUM:
            self._advance()
            return tok.value
        if tok.kind in (LexToken.PLUS, LexToken.MINUS):
            sign = tok.kind
            self._advance()
            nxt = self._current()
            if nxt.kind != LexToken.NUM and nxt.kind != LexToken.LPAREN:
                raise ValueError(f"parser error: expected number or '(' after unary sign")
            val = self._parse_primary()
            if sign == LexToken.MINUS:
                val = -val
            return val
        if tok.kind == LexToken.LPAREN:
            self._advance()
            value = self._parse_expr(minimum_weight=1)
            if self._match(LexToken.RPAREN) is None:
                raise ValueError("parser error: missing closing ')'")
            return value
        raise ValueError(f"parser error: unexpected token {tok!r}")

    def _parse_expr(self, minimum_weight):
        lhs_value = self._parse_primary()

        while True:
            cur_tok = self._current()
            cur_weight = weight_of(cur_tok.kind)
            if cur_weight == 0 or cur_weight < minimum_weight:
                break

            op_kind = cur_tok.kind
            self._advance()

            self._reduce_while_ge(cur_weight)

            rhs_value = self._parse_expr(minimum_weight=cur_weight + 1)

            self._intermediate_vals.push(lhs_value)
            self._intermediate_vals.push(rhs_value)
            self._intermediate_ops.push(op_kind)
            self._apply_top_binary()
            lhs_value = self._intermediate_vals.pop()

        self._reduce_while_ge(minimum_weight)
        if not self._intermediate_vals.is_empty():
            if self._intermediate_ops.is_empty():
                raise ValueError("parser error: leftover value without operator on stack")
        return lhs_value

    def parse_and_evaluate(self):
        result = self._parse_expr(minimum_weight=1)
        if self._current().kind != LexToken.EOF:
            raise ValueError(f"parser error: leftover content after expression at {self._current()!r}")
        if not self._intermediate_ops.is_empty() or not self._intermediate_vals.is_empty():
            raise ValueError("parser error: non-empty intermediate stacks at end of expression")
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result


def evaluate_expression(expression_text):
    if expression_text is None or expression_text.strip() == '':
        raise ValueError("empty expression")
    tokens = lex_expression(expression_text)
    parser = PrecedenceClimbingParser(tokens)
    return parser.parse_and_evaluate()


def read_all_lines(file_path):
    lines = []
    with open(file_path, 'r') as f:
        for ln in f:
            lines.append(ln.rstrip('\n'))
    return lines


def line_is_separator(line_text):
    s = line_text.strip()
    if not s:
        return False
    all_dash = len(s) >= 3 and all(c == '-' for c in s)
    all_eq = len(s) >= 3 and all(c == '=' for c in s)
    return all_dash or all_eq


def line_is_blank(line_text):
    return line_text.strip() == ''


def _contains_alpha(text):
    for c in text:
        if c.isalpha():
            return True
    return False


def line_is_comment(line_text):
    s = line_text.strip()
    if not s:
        return False
    if not _contains_alpha(s):
        return False
    if '---' in s:
        return True
    if s.count(' ') >= 2:
        return True
    return False


def classify_and_process(input_lines):
    out_lines = []
    for raw in input_lines:
        if line_is_blank(raw):
            out_lines.append(raw)
            continue
        if line_is_separator(raw):
            out_lines.append(raw)
            continue
        if line_is_comment(raw):
            out_lines.append(raw)
            continue
        try:
            answer = evaluate_expression(raw)
            out_lines.append(f"{raw} = {answer}")
        except ZeroDivisionError as zde:
            out_lines.append(f"{raw} = ERROR: {str(zde)}")
        except Exception as ex:
            out_lines.append(f"{raw} = ERROR: {str(ex)}")
    return out_lines


def write_output_lines(output_lines, file_path):
    with open(file_path, 'w') as f:
        for ln in output_lines:
            f.write(ln + '\n')


def main():
    INPUT = 'input.txt'
    OUTPUT = 'output.txt'
    bar = '*' * 66

    print(bar)
    print("  DCOMP320  Assignment 1  --  VERSION 3.0")
    print("  Dynamic-Array Stack + Recursive-Descent Precedence Climbing")
    print(bar)
    print()

    try:
        raw_lines = read_all_lines(INPUT)
        print(f"[OK] Read '{INPUT}'  ({len(raw_lines)} lines)")
        print()
    except FileNotFoundError:
        print(f"[ERROR] File '{INPUT}' not found in current directory.")
        print("        Please create it with one expression per line and re-run.")
        return
    except Exception as ex:
        print(f"[ERROR] Could not read input: {ex}")
        return

    print("[INFO] Lexing then recursive-descent parser (precedence climbing) for each line...")
    print()
    results = classify_and_process(raw_lines)

    try:
        write_output_lines(results, OUTPUT)
        print(f"[OK] Wrote '{OUTPUT}'")
        print()
    except Exception as ex:
        print(f"[ERROR] Could not write output: {ex}")
        return

    print(bar)
    print("  EVALUATION RESULTS")
    print(bar)
    for ln in results:
        print(ln)
    print(bar)
    print()
    print("Finished.")


if __name__ == '__main__':
    main()
