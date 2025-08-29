# BanglaScript Programming Language

BanglaScript is a simple, beginner-friendly programming language designed to help developers write and execute scripts in a natural and intuitive way. This documentation will guide you through the basics of BanglaScript, its syntax, and how to use the interpreter.

---

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Syntax](#syntax)
4. [Running BanglaScript](#running-banglascript)
5. [Examples](#examples)
6. [Metadata](#metadata)

---

## Introduction
BanglaScript is a lightweight scripting language that uses simple keywords to perform operations. It is designed to be easy to learn and use, especially for beginners.

---

## Installation
To use BanglaScript, ensure you have Python installed on your system. Clone the repository and navigate to the `src` directory:

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the src directory
cd BanglaScript-Programming Language/src
```

---

## Syntax
BanglaScript uses a few simple keywords to perform operations. Below are the key components:

### Variable Declaration
Use the `dhoro` keyword to declare variables:
```
dhoro x = 5
```

### Printing Output
Use the `lekho` keyword to print variables or values:
```
lekho(x)
lekho(10)
```

### Reserved Words
The following words are reserved and cannot be used as variable names:
- `jodi`
- `nahole`
- `jokhon`
- `for`
- `ferotDao`
- `dhoro`
- `lekho`

---

## Running BanglaScript
To execute a BanglaScript file, use the interpreter:

```bash
python bs.py <file_path>
```

### Example:
If your script is named `main.bs`, run:
```bash
python bs.py main.bs
```

---

## Examples
### Example 1: Basic Variable Assignment and Printing
**main.bs**:
```
dhoro x = 5
lekho(x)
```
**Output**:
```
5
```

### Example 2: Printing Direct Values
**main.bs**:
```
lekho(10)
```
**Output**:
```
10
```

---

## Metadata
To view metadata about the BanglaScript interpreter, such as developer information, use the `--metadata` flag:

```bash
python bs.py --metadata
```

**Output**:
```
Developer: Your Name
Email: your.email@example.com
Phone: +1234567890
```

---

## Contributing
Contributions are welcome! Feel free to fork the repository and submit pull requests.

---

## License
This project is licensed under the MIT License.