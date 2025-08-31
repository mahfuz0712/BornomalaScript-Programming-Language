import re
import argparse

# ------------------------------
# Reserved words (for assignment detection)
# ------------------------------
reserved_words = {"jodi", "othoba", "nahole", "jokhon", "dhoro", "lekho", "kaj", "ferotDao"}

# ------------------------------
# Exceptions
# ------------------------------
class BanglaScriptError(Exception):
    pass

class FerotDaoValue(Exception):
    def __init__(self, value):
        self.value = value

# ------------------------------
# Helpers: strings & operators
# ------------------------------
def unescape_string(s: str) -> str:
    return bytes(s, "utf-8").decode("unicode_escape")

def replace_logical_ops_outside_strings(expr: str) -> str:
    """
    Replace && -> and, || -> or, ! -> not (but keep '!=') outside of quotes.
    """
    out = []
    i, n = 0, len(expr)
    in_single = False
    in_double = False
    while i < n:
        ch = expr[i]

        # Toggle string states
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            i += 1
            continue

        if (in_single or in_double):
            out.append(ch)
            i += 1
            continue

        # Outside strings
        if ch == '&' and i + 1 < n and expr[i+1] == '&':
            out.append(' and ')
            i += 2
            continue
        if ch == '|' and i + 1 < n and expr[i+1] == '|':
            out.append(' or ')
            i += 2
            continue
        if ch == '!':
            if i + 1 < n and expr[i+1] == '=':
                out.append('!=')
                i += 2
            else:
                out.append(' not ')
                i += 1
            continue

        out.append(ch)
        i += 1

    return ''.join(out)

def interpolate_string(s: str, variables, functions):
    """
    Replace ${...} with evaluated result using our evaluator
    """
    def replacer(match):
        inner = match.group(1)
        try:
            return str(eval_expression(inner, variables, functions))
        except BanglaScriptError as e:
            raise BanglaScriptError(f"Error in string interpolation '{inner}': {e}")
    return re.sub(r"\$\{(.+?)\}", replacer, s)

# ------------------------------
# Blocks & parsing
# ------------------------------
def extract_block(lines, start_index):
    """
    Capture a { ... } block starting on lines[start_index]
    Returns (block_lines, end_index)
    """
    block = []
    open_braces = 0
    i = start_index

    line = lines[i].rstrip()
    if '{' in line:
        open_braces += line.count('{')
        line = line[line.find("{")+1:]
    block.append(line)
    i += 1

    while i < len(lines):
        line = lines[i].rstrip()
        open_braces += line.count('{')
        open_braces -= line.count('}')
        block.append(line)
        if open_braces == 0:
            # remove first closing brace on the last line
            block[-1] = block[-1].replace('}', '', 1)
            break
        i += 1

    if open_braces != 0:
        raise BanglaScriptError("Block braces '{' were not closed")
    return block, i

def is_assignment(line: str) -> bool:
    """
    Detect a = not inside quotes and not starting with reserved keyword.
    """
    if any(line.startswith(k) for k in reserved_words):
        return False
    in_string = False
    quote = None
    for ch in line:
        if ch in ('"', "'"):
            if not in_string:
                in_string = True
                quote = ch
            elif quote == ch:
                in_string = False
                quote = None
        elif ch == "=" and not in_string:
            return True
    return False

def smart_split_args(arg_str: str) -> list:
    """
    Split comma-separated arguments while respecting nested parentheses and quotes.
    """
    args = []
    buf = []
    depth = 0
    in_single = False
    in_double = False
    i = 0
    while i < len(arg_str):
        ch = arg_str[i]

        # quote toggles
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            i += 1
            continue

        if in_single or in_double:
            buf.append(ch)
            i += 1
            continue

        if ch == '(':
            depth += 1
            buf.append(ch)
            i += 1
            continue
        if ch == ')':
            depth -= 1
            buf.append(ch)
            i += 1
            continue

        if ch == ',' and depth == 0:
            args.append(''.join(buf).strip())
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    last = ''.join(buf).strip()
    if last:
        args.append(last)
    return args

# ------------------------------
# Safe eval
# ------------------------------
def safe_eval(expr: str, env: dict):
    try:
        return eval(expr, {}, env)
    except NameError as e:
        # Try to extract missing name
        msg = str(e)
        missing = None
        m = re.search(r"name '(.+?)' is not defined", msg)
        if m:
            missing = m.group(1)
        if missing:
            # If looks like a function (identifier), phrase accordingly
            if missing.isidentifier() and missing in env.get('__known_functions__', set()):
                raise BanglaScriptError(f"Unknown function '{missing}'")
            raise BanglaScriptError(f"Variable '{missing}' is not defined")
        raise BanglaScriptError(f"Unknown name error: {msg}")
    except SyntaxError as e:
        raise BanglaScriptError(f"Invalid syntax in expression '{expr}': {e.msg}")
    except Exception as e:
        raise BanglaScriptError(f"Error evaluating expression '{expr}': {e}")

def make_callable(func_name, functions, outer_vars):
    """
    Create a Python callable that runs a BanglaScript function and returns its ferotDao value (or None).
    It captures the *current* outer_vars snapshot each time eval_expression is called.
    """
    def _callable(*py_args):
        params, func_lines = functions[func_name]
        if len(py_args) != len(params):
            raise BanglaScriptError(f"Function '{func_name}' expects {len(params)} arguments, got {len(py_args)}")
        local_vars = dict(outer_vars)
        for p, a in zip(params, py_args):
            local_vars[p] = a
        try:
            run_block(func_lines, local_vars, functions, in_function=True)
            return None
        except FerotDaoValue as f:
            return f.value
    return _callable

def build_eval_env(variables: dict, functions: dict) -> dict:
    """
    Build an eval environment that includes variables + Python callables for each BanglaScript function.
    Also tag known function names in __known_functions__ to improve error messages.
    """
    env = dict(variables)
    env['__known_functions__'] = set(functions.keys())
    # Inject callables
    for fname in functions.keys():
        env[fname] = make_callable(fname, functions, variables)
    return env

def eval_expression(expr: str, variables: dict, functions: dict):
    """
    Evaluate any BanglaScript expression:
    - supports nested function calls (via injected callables)
    - supports &&, ||, ! (outside strings)
    - supports variables and arithmetic
    """
    expr_py = replace_logical_ops_outside_strings(expr.strip())
    env = build_eval_env(variables, functions)
    return safe_eval(expr_py, env)

def parse_arguments(arg_str, variables, functions):
    """
    Parse function call argument list into evaluated Python values
    using the same evaluator (supports nested calls).
    """
    args = []
    if arg_str.strip():
        for raw in smart_split_args(arg_str):
            # If quoted string literal, unescape directly
            if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
                args.append(unescape_string(raw[1:-1]))
            else:
                args.append(eval_expression(raw, variables, functions))
    return args

# ------------------------------
# Core executor
# ------------------------------
def run_block(lines, variables, functions=None, in_function=False):
    if functions is None:
        functions = {}
    i = 0
    while i < len(lines):
        # Strip comments (// ...) and whitespace
        line = lines[i].split("//")[0].strip()
        if not line:
            i += 1
            continue

        # Skip function declarations during execution (they are pre-registered)
        if line.startswith("kaj"):
            _, end_index = extract_block(lines, i)
            i = end_index + 1
            continue

        # ferotDao return
        if line.startswith("ferotDao"):
            expr = line[len("ferotDao"):].strip()
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                value = unescape_string(expr[1:-1])
            else:
                value = eval_expression(expr, variables, functions)
            raise FerotDaoValue(value)

        # Declarations & Assignments
        if line.startswith("dhoro") or is_assignment(line):
            if line.startswith("dhoro"):
                parts = line.split("=", 1)
                tokens = line.split()
                if len(parts) == 1:
                    # 'dhoro x' without initializer
                    if len(tokens) != 2:
                        raise BanglaScriptError("Invalid declaration. Usage: dhoro <name> = <expr>  or  dhoro <name>")
                    var_name = tokens[1]
                    variables[var_name] = None
                    i += 1
                    continue
                # 'dhoro x = expr'
                _, var_name = tokens[0:2]
                expr = parts[1].strip()
            else:
                parts = line.split("=", 1)
                if len(parts) != 2:
                    raise BanglaScriptError("Invalid assignment. Usage: <name> = <expr>")
                var_name = parts[0].strip()
                expr = parts[1].strip()
                if var_name not in variables:
                    raise BanglaScriptError(f"Variable '{var_name}' not declared. Use 'dhoro' to declare it first.")

            # Evaluate RHS with full expression evaluator
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                value = unescape_string(expr[1:-1])
            else:
                value = eval_expression(expr, variables, functions)

            variables[var_name] = value
            i += 1
            continue

        # Printing
        if line.startswith("lekho"):
            # content inside parentheses
            if "(" not in line or not line.endswith(")"):
                raise BanglaScriptError(f"Malformed lekho statement: {line}")
            content = line[line.find("(")+1:line.rfind(")")]

            # newline handling like: lekho(expr\n)
            newline = "\\n" in content
            content = content.replace("\\n", "")

            # literal string with interpolation
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                string_value = unescape_string(content[1:-1])
                string_value = interpolate_string(string_value, variables, functions)
                print(string_value, end='\n' if newline else '')
            else:
                # General expression (variables, arithmetic, function calls, etc.)
                val = eval_expression(content, variables, functions)
                print(val, end='\n' if newline else '')
            i += 1
            continue

        # Conditionals chain: jodi / othoba / nahole
        if line.startswith("jodi"):
            executed_block = False
            while i < len(lines):
                current_line = lines[i].split("//")[0].strip()
                if not current_line:
                    i += 1
                    continue
                first_word = current_line.split()[0]
                if first_word not in ("jodi", "othoba", "nahole"):
                    break

                keyword = first_word
                if keyword in ("jodi", "othoba"):
                    if "(" not in current_line or ")" not in current_line:
                        raise BanglaScriptError(f"Malformed condition: {current_line}")
                    cond_expr = current_line[current_line.find("(")+1:current_line.rfind(")")]
                    condition = bool(eval_expression(cond_expr, variables, functions))
                else:
                    condition = True  # nahole

                block_lines, end_index = extract_block(lines, i)
                if not executed_block and condition:
                    run_block(block_lines, variables, functions)
                    executed_block = True
                i = end_index + 1
            continue

        # While loop: jokhon (cond) { ... }
        if line.startswith("jokhon"):
            if "(" not in line or ")" not in line:
                raise BanglaScriptError(f"Malformed while condition: {line}")
            cond_expr = line[line.find("(")+1:line.rfind(")")]
            block_lines, end_index = extract_block(lines, i)
            while True:
                if not bool(eval_expression(cond_expr, variables, functions)):
                    break
                run_block(block_lines, variables, functions)
            i = end_index + 1
            continue

        # Standalone function call line
        mcall = re.match(r"^(\w+)\s*\((.*)\)\s*$", line)
        if mcall:
            func_name, arg_str = mcall.group(1), mcall.group(2)
            if func_name not in functions:
                raise BanglaScriptError(f"Unknown function '{func_name}'")
            # Evaluate via eval_expression so nested calls work naturally
            _ = eval_expression(line, variables, functions)
            i += 1
            continue

        # Unknown
        raise BanglaScriptError(f"Unknown command: {line}")

# ------------------------------
# Function registry (first pass)
# ------------------------------
def register_functions(lines):
    functions = {}
    i = 0
    while i < len(lines):
        line = lines[i].split("//")[0].strip()
        if line.startswith("kaj"):
            # kaj name(a,b) {
            m = re.match(r'kaj\s+(\w+)\s*\((.*?)\)\s*{', line)
            if not m:
                raise BanglaScriptError(f"Malformed function declaration: {line}")
            func_name = m.group(1)
            param_str = m.group(2)
            params = [p.strip() for p in param_str.split(",") if p.strip()]
            block_lines, end_index = extract_block(lines, i)
            functions[func_name] = (params, block_lines)
            i = end_index + 1
        else:
            i += 1
    return functions

# ------------------------------
# Runner
# ------------------------------
def run_bs(bs_file_path):
    try:
        with open(bs_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {bs_file_path}")
        return

    functions = register_functions(lines)
    variables = {}

    try:
        run_block(lines, variables, functions)
    except BanglaScriptError as e:
        print(f"Error: {e}")

# ------------------------------
# CLI
# ------------------------------
def main():
    parser = argparse.ArgumentParser(description="BanglaScript interpreter")
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument("--metadata", action="store_true", help="Show metadata information")
    parser.add_argument("file_path", type=str, nargs='?', help="Path to the BanglaScript (.bs) file")
    args = parser.parse_args()

    if args.metadata:
        print("Developer: Mohammad Mahfuz Rahman")
        print("Email: mahfuzrahman0712@outlook.com")
        print("Github: github.com/mahfuz0712")
        return

    if not args.file_path:
        parser.error("the following arguments are required: file_path")

    run_bs(args.file_path)

if __name__ == "__main__":
    main()
