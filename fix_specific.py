#!/usr/bin/env python3
"""Fix specific indentation issues in main.py by line number"""

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines to fix (0-indexed, so subtract 1):
# Line 2625 and 2626 need extra 4 spaces
# Line 2702 and 2703 need extra 4 spaces

lines_to_fix = [2625, 2626, 2702, 2703]

for line_num in lines_to_fix:
    i = line_num - 1  # Convert to 0-indexed
    old_line = lines[i]
    # Add 4 more spaces (change from 4 to 8 spaces indent)
    new_line = "        " + old_line.strip() + "\n"
    lines[i] = new_line
    print(f"Fixed line {line_num}")

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Verifying syntax...")
import subprocess
result = subprocess.run(['python', '-m', 'py_compile', 'main.py'], capture_output=True, text=True)
if result.returncode == 0:
    print("SUCCESS! Syntax is valid!")
else:
    print(f"Error: {result.stderr}")
