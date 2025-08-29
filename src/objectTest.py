import re
import argparse

reserved_words = {"jodi", "othoba", "nahole", "jokhon", "dhoro", "lekho", "kaj", "ferotDao"}

class BanglaScriptError(Exception):
    pass

class FerotDaoValue(Exception):
    def __init__(self, value):
        self.value = value

class BanglaObject:
    def __init__(self, obj_dict):
        self.__dict__.update(obj_dict)
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)

def unescape_string(s):
    return bytes(s, "utf-8").decode("unicode_escape")

def interpolate_string(s, variables):
    def replacer(match):
        expr = match.group(1)
        if expr in variables:
            return str(variables[expr])
        try:
            return str(eval(expr, {}, variables))
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
        split_args = re.findall(r'("[^"]*"|\'[^\']*\'|\{.*?\}|[^,]+)', arg_str)
        for arg in split_args:
            arg = arg.strip()
            if arg.startswith('{') and arg.endswith('}'):
                # object literal
                args.append(parse_object(arg, variables, functions))
            elif (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                args.append(unescape_string(arg[1:-1]))
            elif re.match(r'\w+\s*\(.*\)', arg):  # function call
                func_name, inner_args = re.match(r'(\w+)\s*\((.*)\)', arg).groups()
                if func_name not in functions:
                    raise BanglaScriptError(f"Unknown function: {func_name}")
                inner_args_parsed = parse_arguments(inner_args, variables, functions)
                params, func_lines = functions[func_name]
                if len(params) != len(inner_args_parsed):
                    raise BanglaScriptError(f"Function '{func_name}' expects {len(params)} args, got {len(inner_args_parsed)}")
                local_vars = variables.copy()
                for p, a in zip(params, inner_args_parsed):
                    local_vars[p] = a
                try:
                    run_block(func_lines, local_vars, functions, in_function=True)
                    value = None
                except FerotDaoValue as f:
                    value = f.value
                args.append(value)
            else:
                try:
                    args.append(eval(arg, {}, variables))
                except:
                    if arg in variables:
                        args.append(variables[arg])
                    else:
                        raise BanglaScriptError(f"Unknown argument: {arg}")
    return args

def parse_object(block_str, variables, functions):
    obj = {}
    block_str = block_str.strip()[1:-1].strip()
    lines = [l.strip() for l in block_str.split(',') if l.strip()]
    for line in lines:
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('{') and value.endswith('}'):
            obj[key] = parse_object(value, variables, functions)
        elif re.match(r'\w+\s*\(.*\)\s*\{', value):  # function inside object
            func_name_match = re.match(r'(\w+)\s*\(.*\)\s*\{', value)
            func_name = func_name_match.group(1)
            func_block, _ = extract_block([value], 0)
            obj[key] = lambda *args, fb=func_block: run_block(fb, variables.copy(), functions, in_function=True)
        elif (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            obj[key] = unescape_string(value[1:-1])
        elif re.match(r'\[.*\]', value):  # array
            obj[key] = eval(value, {}, variables)
        else:
            try:
                obj[key] = eval(value, {}, variables)
            except:
                if value in variables:
                    obj[key] = variables[value]
                else:
                    raise BanglaScriptError(f"Unknown value for object key '{key}': {value}")
    return BanglaObject(obj)

def eval_expression(expr, variables, functions):
    expr = expr.strip()
    # object literal
    if expr.startswith('{') and expr.endswith('}'):
        return parse_object(expr, variables, functions)
    # function call
    m = re.match(r'(\w+)\((.*)\)', expr)
    if m and m.group(1) in functions:
        func_name, arg_str = m.group(1), m.group(2)
        args = parse_arguments(arg_str, variables, functions)
        params, func_lines = functions[func_name]
        if len(params) != len(args):
            raise BanglaScriptError(f"Function '{func_name}' expects {len(params)} args, got {len(args)}")
        local_vars = variables.copy()
        for p, a in zip(params, args):
            local_vars[p] = a
        try:
            run_block(func_lines, local_vars, functions, in_function=True)
            return None
        except FerotDaoValue as f:
            return f.value
    # dot access
    if '.' in expr:
        parts = expr.split('.')
        val = variables.get(parts[0])
        if val is None:
            raise BanglaScriptError(f"Unknown object: {parts[0]}")
        for attr in parts[1:]:
            val = getattr(val, attr)
        return val
    # fallback eval
    try:
        return eval(expr, {}, variables)
    except:
        if expr in variables:
            return variables[expr]
        raise BanglaScriptError(f"Cannot evaluate expression: {expr}")

def run_block(lines, variables, functions=None, in_function=False):
    if functions is None:
        functions = {}
    i = 0
    while i < len(lines):
        line = lines[i].split('//')[0].strip()
        if not line:
            i += 1
            continue

        # Skip function declarations
        if line.startswith("kaj"):
            _, end_index = extract_block(lines, i)
            i = end_index + 1
            continue

        # ferotDao
        if line.startswith("ferotDao"):
            expr = line[len("ferotDao"):].strip()
            value = eval_expression(expr, variables, functions)
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
            value = eval_expression(expr, variables, functions)
            variables[var_name] = value
            i += 1
            continue

        # Print statement
        elif line.startswith("lekho"):
            content = line[line.find("(")+1:line.rfind(")")]
            newline = "\\n" in content
            content = content.replace("\\n", "")
            value = eval_expression(content, variables, functions)
            print(value, end='\n' if newline else '')
            i += 1
            continue

        # Unknown command fallback
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
    parser = argparse.ArgumentParser(description="BanglaScript interpreter with objects")
    parser.add_argument("file_path", type=str, help="Path to the BanglaScript (.bs) file")
    args = parser.parse_args()
    run_bs(args.file_path)

if __name__ == "__main__":
    main()
