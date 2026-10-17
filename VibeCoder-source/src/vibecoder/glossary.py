"""Offline notes for Deep Wiki. This is a local glossary, not a web search."""

from __future__ import annotations

import re

_NOTES: dict[str, str] = {
    "print": "print(value) writes text to the output window, then starts a new line. print(a, b) separates the values with a space.",
    "len": "len(item) returns how many elements are in a string, list, dict, or other collection.",
    "range": "range(stop) counts from 0 up to, but not including, stop. range(start, stop, step) chooses the start and the jump.",
    "open": "open(path) opens a file. Use with open(path) as handle: so the file is closed even if something fails. mode 'r' reads, 'w' overwrites, 'a' appends.",
    "list": "list is an ordered collection you can change. list() builds one from another sequence. items[0] is the first item.",
    "dict": "dict maps a key to a value, written {key: value}. Look a value up with mapping[key].",
    "str": "str is text. str(number) turns a number into text. Text is immutable: methods return a new string.",
    "int": "int is a whole number. int('12') parses text into a number.",
    "float": "float is a number with a decimal point, such as 3.14.",
    "bool": "bool is True or False. Comparisons and if statements use it.",
    "def": "def name(arguments): starts a function. The indented lines under it are the body. Call it later with name(arguments).",
    "class": "class Name: starts a new type. Functions inside it are methods. The first argument of a method is usually self, the object itself.",
    "import": "import module loads another file so you can use module.function(). from module import name pulls that name in directly.",
    "return": "return sends a value back to the caller and leaves the function. A function with no return gives back None.",
    "yield": "yield pauses a function and hands back a value, turning the function into a generator. The next loop resumes after yield.",
    "lambda": "lambda arguments: expression is a small function written in one line. It returns the expression.",
    "self": "self is the usual name for the object a method is working on. self.name stores a value on that object.",
    "none": "None means no value. Functions that do not return anything return None.",
    "true": "True is the boolean value for yes. It is not the same as the text 'True'.",
    "false": "False is the boolean value for no.",
    "for": "for item in collection: repeats the indented body once per item.",
    "while": "while condition: repeats the indented body as long as the condition stays true.",
    "if": "if condition: runs the indented body only when the condition is true. elif checks another condition. else runs when none of them matched.",
    "elif": "elif condition: is an extra test after if. It runs only when earlier tests were false.",
    "else": "else: runs when the matching if, elif, for, while, or try did not take its other path.",
    "pass": "pass is an empty statement. It lets you leave a block blank without a syntax error.",
    "break": "break leaves the nearest loop immediately.",
    "continue": "continue skips the rest of this loop pass and starts the next one.",
    "raise": "raise Error('message') stops normal flow and reports an error the caller can catch with try.",
    "assert": "assert condition, 'message' stops the program if the condition is false. It is a check you expect to stay true.",
    "try": "try: watches the indented body. except Error: runs if that error is raised. finally: runs either way.",
    "except": "except ErrorType: handles that error from the matching try. except Exception: handles most errors.",
    "finally": "finally: runs after try whether an error happened or not. Use it for cleanup.",
    "with": "with expression as name: opens a resource and closes it when the block ends, even if an error is raised.",
    "async": "async def name(): defines a function that can pause on await. You run it from an event loop, not by calling it like a normal function.",
    "await": "await pauses an async function until another async task finishes, then continues with that result.",
    "global": "global name tells a function to assign to the module-level variable instead of creating a local one.",
    "nonlocal": "nonlocal name assigns to a variable in an enclosing function, not the module and not a new local.",
    "from": "from module import name copies that name into the current file.",
    "as": "as gives an imported module, an opened file, or a caught error a local name.",
    "in": "in tests membership. item in collection is true when the collection contains item.",
    "is": "is tests whether two names point at the same object. Use is None, not == None.",
    "and": "and is true only when both sides are true. It returns the last value it had to read.",
    "or": "or is true when either side is true. It stops at the first true value and returns it.",
    "not": "not flips True and False.",
    "del": "del name removes a variable, list item, or dict key.",
    "match": "match value: compares a value against case patterns, in order. It is Python's structural switch.",
    "case": "case pattern: is one branch inside match. case _: matches anything left over.",
    "function": "function name(arguments) { } defines a JavaScript function. A return inside it sends a value back.",
    "const": "const name = value creates a binding you cannot point at a different value later. The contents of an object can still change.",
    "let": "let name = value creates a variable that belongs to the current block.",
    "var": "var name = value creates a function-scoped variable. let and const are the usual choices in modern JavaScript.",
    "console": "console.log(value) writes a value to the JavaScript console. In a browser that is the developer tools; in Node it is the terminal.",
    "func": "func name() { } defines a Go function. func main() is where a Go program starts.",
    "package": "package name is the first line of a Go file. Every file in one folder shares one package. package main can be built into a program.",
    "defer": "defer call() runs that call when the current function returns. It is the usual way to close a file in Go.",
    "chan": "chan is a Go channel. One goroutine sends a value, another receives it.",
    "go": "go function() starts that call in a new goroutine so it can run at the same time as the rest of the function.",
    "fn": "fn name() { } defines a Rust function. fn main() is the program entry.",
    "mut": "let mut name = value makes a Rust binding you can assign again. Without mut, the binding stays as it was.",
    "impl": "impl Type { } adds methods to a Rust type. impl Trait for Type supplies a trait's behavior.",
    "trait": "trait Name { } describes methods a type must have. Other types opt in with impl Trait for Type.",
    "struct": "struct Name { field: Type } groups named fields into one Rust or C type.",
    "select": "A SQL SELECT reads rows. SELECT columns FROM table WHERE condition chooses which rows come back.",
    "insert": "INSERT INTO table (columns) VALUES (values) adds a row.",
    "update": "UPDATE table SET column = value WHERE condition changes existing rows. Without WHERE it changes every row.",
    "delete": "DELETE FROM table WHERE condition removes matching rows. Without WHERE it removes every row.",
}


def lookup(word: str) -> str | None:
    cleaned = word.strip().strip("()[]{}.,;:").lower()
    if not cleaned:
        return None
    return _NOTES.get(cleaned)


def explain(text: str) -> tuple[str, str]:
    """Explain a word or a highlighted block from the local notes."""
    snippet = text.strip()
    if not snippet:
        return "Deep Wiki", "Highlight a word or a block, or hover a known name."

    if "\n" not in snippet and " " not in snippet:
        note = lookup(snippet)
        if note:
            return snippet.strip(), note
        return snippet.strip(), (
            f"No local note for {snippet.strip()}. "
            "Deep Wiki is an offline glossary of common names, so unknown project functions stay unexplained here."
        )

    header = _signature(snippet)
    if header:
        return header, (
            f"This block starts with `{header}`. "
            "The indented lines under a header are its body. "
            "A def or function returns a value with return. "
            "A class groups methods that share one object."
        )

    line_count = snippet.count("\n") + 1
    return "Selection", (
        f"{line_count} lines selected. "
        "Deep Wiki can describe a single known name, or a block that starts with def, class, function, fn, or func. "
        "It does not search the web."
    )


def _signature(snippet: str) -> str | None:
    first = ""
    for line in snippet.splitlines():
        if line.strip():
            first = line.strip()
            break
    patterns = (
        r"^(?:async\s+def|def)\s+\w+\s*\([^)]*\)",
        r"^class\s+\w+",
        r"^function\s+\w+\s*\([^)]*\)",
        r"^fn\s+\w+\s*\(",
        r"^func\s+\w+\s*\(",
    )
    for pattern in patterns:
        match = re.match(pattern, first)
        if match:
            return match.group(0).rstrip(":")
    return None
