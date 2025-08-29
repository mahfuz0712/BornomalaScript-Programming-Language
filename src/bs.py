import re
import argparse

reserved_words = {"jodi", "othoba", "nahole", "jokhon", "dhoro", "lekho", "kaj", "ferotDao"}

class BanglaScriptError(Exception):
    pass

class FerotDaoValue(Exception):
    def __init__(self, value):
        self.value = value

def unescape_string(s):
    return bytes(s, "utf-8").decode("unicode_escape")

def interpolate_string(s, variables):
    def replacer(match):
        expr = match.group(1)
        try:
            if expr in variables:
                return str(variables[expr])
            else:
                return str(eval(expr.replace("&&", " and ").replace("||", " or ").replace("!", " not "), {}, variables))
        except Exception as e:
            raise BanglaScriptError(f"Error in string interpolation '{expr}': {e}")
    return re.sub(r"\$\{(.+?)\}", replacer, s)

def extract_block(lines, start_index):
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
            block[-1] = block[-1].replace('}', '', 1)
            break
        i += 1
    if open_braces != 0:
        raise BanglaScriptError("Block braces '{' were not closed")
    return block, i

def is_assignment(line):
    if any(line.startswith(k) for k in reserved_words):
        return False
    in_string = False
    for char in line:
        if char in ('"', "'"):
            in_string = not in_string
        elif char == "=" and not in_string:
            return True
    return False

def parse_arguments(arg_str, variables, functions):
    args = []
    if arg_str.strip():
        # Split arguments by commas, handle quotes
        split_args = re.findall(r'("[^"]*"|\'[^\']*\'|[^,]+)', arg_str)
        for arg in split_args:
            arg = arg.strip()
            func_match = re.match(r"^(\w+)\s*\((.*)\)$", arg)
            if func_match and func_match.group(1) in functions:
                func_name, inner_arg_str = func_match.group(1), func_match.group(2)
                inner_args = parse_arguments(inner_arg_str, variables, functions)
                params, func_lines = functions[func_name]
                if len(inner_args) != len(params):
                    raise BanglaScriptError(f"Function '{func_name}' expects {len(params)} arguments, got {len(inner_args)}")
                local_vars = variables.copy()
                for p, a in zip(params, inner_args):
                    local_vars[p] = a
                try:
                    run_block(func_lines, local_vars, functions, in_function=True)
                    value = None
                except FerotDaoValue as f:
                    value = f.value
                args.append(value)
            elif (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                args.append(unescape_string(arg[1:-1]))
            else:
                arg_py = arg.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
                args.append(eval(arg_py, {}, variables))
    return args

def run_block(lines, variables, functions=None, in_function=False):
    if functions is None:
        functions = {}
    i = 0
    while i < len(lines):
        line = lines[i].split("//")[0].strip()
        if not line:
            i += 1
            continue

        # Skip function declarations during execution
        if line.startswith("kaj"):
            _, end_index = extract_block(lines, i)
            i = end_index + 1
            continue

        # ferotDao handling
        if line.startswith("ferotDao"):
            expr = line[len("ferotDao"):].strip()
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                value = unescape_string(expr[1:-1])
            else:
                value = eval(expr.replace("&&", " and ").replace("||", " or ").replace("!", " not "), {}, variables)
            raise FerotDaoValue(value)

        # Variable assignment
        if line.startswith("dhoro") or is_assignment(line):
            if line.startswith("dhoro"):
                parts = line.split("=", 1)
                _, var_name = line.split()[0:2]
                expr = parts[1].strip()
            else:
                parts = line.split("=", 1)
                var_name = parts[0].strip()
                expr = parts[1].strip()
                if var_name not in variables:
                    raise BanglaScriptError(f"Variable '{var_name}' not declared. Use 'dhoro' to declare it first.")

            func_match = re.match(r"(\w+)\s*\((.*)\)", expr)
            if func_match and func_match.group(1) in functions:
                func_name, arg_str = func_match.group(1), func_match.group(2)
                args = parse_arguments(arg_str, variables, functions)
                params, func_lines = functions[func_name]
                if len(args) != len(params):
                    raise BanglaScriptError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
                local_vars = variables.copy()
                for p, a in zip(params, args):
                    local_vars[p] = a
                try:
                    run_block(func_lines, local_vars, functions, in_function=True)
                    value = None
                except FerotDaoValue as f:
                    value = f.value
            else:
                if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                    value = unescape_string(expr[1:-1])
                else:
                    expr_py = expr.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
                    value = eval(expr_py, {}, variables)

            variables[var_name] = value
            i += 1
            continue

        # Print statement
        elif line.startswith("lekho"):
            content = line[line.find("(")+1:line.rfind(")")]
            newline = "\\n" in content
            content = content.replace("\\n", "")

            func_match = re.match(r"(\w+)\s*\((.*)\)", content)
            if func_match and func_match.group(1) in functions:
                func_name, arg_str = func_match.group(1), func_match.group(2)
                args = parse_arguments(arg_str, variables, functions)
                params, func_lines = functions[func_name]
                local_vars = variables.copy()
                for p, a in zip(params, args):
                    local_vars[p] = a
                try:
                    run_block(func_lines, local_vars, functions, in_function=True)
                    value = None
                except FerotDaoValue as f:
                    value = f.value
                print(value, end='\n' if newline else '')
            elif (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                string_value = unescape_string(content[1:-1])
                string_value = interpolate_string(string_value, variables)
                print(string_value, end='\n' if newline else '')
            elif content in variables:
                print(variables[content], end='\n' if newline else '')
            else:
                content_py = content.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
                print(eval(content_py, {}, variables), end='\n' if newline else '')
            i += 1
            continue

        # Conditionals
        elif line.startswith("jodi") or line.startswith("othoba") or line.startswith("nahole"):
            executed_block = False
            while i < len(lines):
                current_line = lines[i].strip()
                if not current_line:
                    i += 1
                    continue
                first_word = current_line.split()[0]
                if first_word not in ("jodi", "othoba", "nahole"):
                    break
                keyword = first_word
                if keyword in ("jodi", "othoba"):
                    cond_expr = current_line[current_line.find("(")+1:current_line.rfind(")")]
                    cond_expr = cond_expr.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
                    condition = eval(cond_expr, {}, variables)
                else:
                    condition = True
                block_lines, end_index = extract_block(lines, i)
                if not executed_block and condition:
                    run_block(block_lines, variables, functions)
                    executed_block = True
                i = end_index + 1
            continue

        # While loop
        elif line.startswith("jokhon"):
            cond_expr = line[line.find("(")+1:line.rfind(")")]
            cond_expr = cond_expr.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
            block_lines, end_index = extract_block(lines, i)
            while eval(cond_expr, {}, variables):
                run_block(block_lines, variables, functions)
            i = end_index + 1
            continue

        # Function call standalone
        first_word = line.split("(")[0].strip()
        if first_word in functions:
            m = re.match(r"^(\w+)\s*\((.*)\)$", line)
            func_name, arg_str = m.group(1), m.group(2)
            args = parse_arguments(arg_str, variables, functions)
            params, func_lines = functions[func_name]
            local_vars = variables.copy()
            for p, a in zip(params, args):
                local_vars[p] = a
            try:
                run_block(func_lines, local_vars, functions, in_function=True)
                ret_value = None
            except FerotDaoValue as f:
                ret_value = f.value
            if is_assignment(line):
                assign_var = line.split('=')[0].strip()
                variables[assign_var] = ret_value
            i += 1
            continue

        raise BanglaScriptError(f"Unknown command: {line}")

def register_functions(lines):
    functions = {}
    i = 0
    while i < len(lines):
        line = lines[i].split("//")[0].strip()
        if line.startswith("kaj"):
            _, func_name_and_params = line.split(None, 1)
            func_name = func_name_and_params[:func_name_and_params.find("(")]
            param_str = func_name_and_params[func_name_and_params.find("(")+1:func_name_and_params.find(")")]
            params = [p.strip() for p in param_str.split(",") if p.strip()]
            block_lines, end_index = extract_block(lines, i)
            functions[func_name] = (params, block_lines)
            i = end_index + 1
        else:
            i += 1
    return functions

def run_bs(bs_file_path):
    try:
        with open(bs_file_path, "r") as f:
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

def main():
    parser = argparse.ArgumentParser(description="BanglaScript interpreter")
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument("--metadata", action="store_true", help="Show metadata information")
    parser.add_argument("file_path", type=str, nargs='?', help="Path to the BanglaScript (.bs) file")
    args = parser.parse_args()
    
    # Adjusted the '--metadata' flag to work without requiring 'file_path'
    if args.metadata:
        print("Developer: Mohammad Mahfuz Rahman")
        print("Email: mahfuzrahman0712@outlook.com")
        print("Github: github.com/mahfuz0712")
        return

    # Ensure 'file_path' is only required when '--metadata' is not used
    if not args.file_path:
        parser.error("the following arguments are required: file_path")
    
    run_bs(args.file_path)

if __name__ == "__main__":
    main()
