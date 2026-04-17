

# Guidelines / Rules

At the beginning of every chat, please address me as Dr. Frost.

When you need to write or modify code, please strictly follow these rules:
+ Do not run git commit after every single code change. However, every time you successfully implement and debug a complete feature, you must commit it to create a backup.
+ Never make any single function too long or too large. If a feature is overly complex, it should be broken down into multiple files or multiple functions within a file. This ensures the code remains clear and the cognitive load for reading it stays reasonable.
+ For every feature you implement, you must write the corresponding test cases, and write code in the relevant area to test the functionality. Keep iterating until that part of the feature is successfully implemented.
+ **Never mock data under any circumstances**, even during debugging.

If you are writing Python:
Use `uv` to manage the entire project. uv is already installed by default.
