#!/usr/bin/env python3
"""Fix indentation issues in main.py"""

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation issues
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check for the problematic pattern
    if line.strip() == 'if translated:' and i + 1 < len(lines):
        next_line = lines[i + 1]
        # If next line is bot.send_message without proper indent
        if next_line.strip().startswith('bot.send_message') and not next_line.startswith('        '):
            fixed_lines.append(line)
            # Add the proper indentation to the next two lines
            fixed_lines.append('        ' + lines[i + 1].strip() + '\n')
            fixed_lines.append('        ' + lines[i + 2].strip() + '\n')
            i += 3
            continue
    
    fixed_lines.append(line)
    i += 1

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Fixed indentation issues!")
