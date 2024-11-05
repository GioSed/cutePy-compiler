# CutePy Compiler

This project is a compiler for a custom language called **CutePy**, which is similar to Python. The CutePy compiler performs lexical analysis, parsing, and generates intermediate code (quads) and assembly code.

### Features:
- **Lexical analysis**: Converts source code into tokens.
- **Syntax analysis**: Verifies the structure of the CutePy code.
- **Code generation**: Produces intermediate code and assembly code.

### Language Overview

CutePy provides basic control structures, expressions, and functions similar to Python, with the addition of special symbols for organizing code blocks. Below is a list of supported lexical symbols, structures, and operators.

---

## Lexical Symbols

### **Operators**:

- **Arithmetic**:
  - `+` : Addition
  - `-` : Subtraction
  - `*` : Multiplication
  - `//` : Integer Division

- **Comparison**:
  - `<`  : Less than
  - `>`  : Greater than
  - `<=` : Less than or equal to
  - `>=` : Greater than or equal to
  - `==` : Equality
  - `!=` : Not equal

- **Assignment**:
  - `=` : Assignment operator (e.g., `x = 5`)

- **Logical**:
  - `and` : Logical AND
  - `or`  : Logical OR
  - `not` : Logical NOT

### **Punctuation**:

- `(`, `)` : Parentheses for grouping expressions or function calls
- `{`, `}` : Braces to define blocks of code (e.g., function or if-statement blocks)
- `[`, `]` : Brackets for arrays/lists (if applicable)
- `,`      : Comma for separating variables or parameters
- `;`      : Semicolon for ending statements
- `:`      : Colon used after `if`, `else`, and function definitions

### **Special Symbols and Keywords**:

Special Symbols:
#$    : Multi-line comment start and end.
#{    : Left hash bracket (used to mark a block of code).
#}    : Right hash bracket (used to close a block of code).
#     : Single-line comment.

Keywords:
declare : Used to declare variables
def     : Defines a function
if      : Conditional statement
else    : Else block for if
while   : Loop construct
return  : Return a value from a function
input   : Reads input from the user
print   : Outputs to the console
