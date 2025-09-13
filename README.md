# BornomalaScript Programming Language

BornomalaScript is a simple, beginner-friendly programming language designed to help children write and execute scripts or program in a natural and intuitive way. This documentation will guide you through the basics of BornomalaScript, its syntax, and how to use it.

---

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Running BornomalaScript](#running-Bornomalascript)
4. [Examples](#examples)


---

## Introduction
BornomalaScript is a lightweight scripting language that uses simple keywords to perform operations. It is designed to be easy to learn and use, especially for kids.

---

## Installation
To use BornomalaScript, ensure you have it's compiler installed on your system.

### Windows Guide
* Step 1: Download the latest release from <a href="https://bornomala-script.vercel.app/" target="_blank">Website</a>


* Step 2: Double click the setup file and follow the installation instructions.
* Step 3: Open "C:\Program Files (x86)\Mohammad Mahfuz Rahman\BornomalaScript" and copy the path.
* Step 4: Open Environment Variables and add the copied path to the Path variable. 
* Step 5: Open Command Prompt and type 
```bash
bs --version
```
If the installation was successful, you should see the BornomalaScript compiler version. 
* Step 6: To check the metadata of BornomalaScript, type 
```bash
bs --metadata
``` 
in the command prompt. 
* Step 7: To see all the available commands, type 
```bash
bs --help
``` 
in the command prompt.

---

### Linux Guide (Debian based distros only)
* Step 1: Download the latest release from <a href="https://bornomala-script.vercel.app/" target="_blank">Website</a>

* Step 2: Open the folder where the .deb file is downloaded
* Step 3: Open terminal or console there and type the command below
```bash
dpkg -i file\to\.deb
```
* Step 4: Open terminal anywhere and type 
```bash
bs --version
```
If the installation was successful, you should see the BornomalaScript compiler version.
* Step 6: To check the metadata of BornomalaScript, type 
```bash
bs --metadata
```
in the terminal.
* Step 7: To see all the available commands, type 
```bash
bs --help
```
in the terminal.


## VS Code Setup

* Step 1: <a href="https://marketplace.visualstudio.com/items?itemName=mahfuz0712.bornomala-script-pack" target="_blank">Download the vs code extension</a> and install it



## Running BornomalaScript
To execute a BornomalaScript file, use the interpreter:

```bash
bs <file_path>
```

### Example:
If your script is named `main.bs`, run:
```bash
bs main.bs
```

---

## Examples
### Basic Variable Assignment and Printing
**main.bs**:
```
dhoro x = 5
lekho(x)
```
**Output**:
```
5
```

### Printing Direct Values
**main.bs**:
```
lekho(10)
```
**Output**:
```
10
```

### Taking an input from user
**main.bs**:
```
dhoro input = inputNao("Enter something: ")
lekho("you entered ${input}")
```
**Output**:
```
you entered "whatever is input"
```

for further details check documentation at <a href="https://bornomala-script.vercel.app/" target="_blank">BornomalaScript Official Website</a>

Happy Coding