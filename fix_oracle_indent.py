#!/usr/bin/env python3
"""Fix indentation issues in main.py"""

with open('main.py', 'r') as f:
    lines = f.readlines()

# Fix the with block indentation (lines around 3635)
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix: "            with open(...) as f:\n" followed by badly indented content
    if 'with open(subscribers_file, "r+") as f:' in line and '            with' in line:
        new_lines.append(line)
        i += 1
        # The next lines should be indented by 4 more spaces
        while i < len(lines):
            next_line = lines[i]
            # Check if we're still inside the with block
            if next_line.strip() and not next_line.startswith('                ') and not next_line.startswith('        else:') and not next_line.startswith('    except'):
                # Need to fix indentation - add 4 spaces
                if next_line.startswith('            ') and not next_line.startswith('                '):
                    new_lines.append('    ' + next_line)
                elif next_line.startswith('                ') and 'bot.send_message' in next_line:
                    # Fix double-indented else block
                    new_lines.append(next_line.replace('                    bot.send_message', '                    bot.send_message'))
                else:
                    new_lines.append(next_line)
            else:
                new_lines.append(next_line)
            i += 1
            if '        else:' in next_line or '    except' in next_line:
                break
        continue
    
    new_lines.append(line)
    i += 1

with open('main.py', 'w') as f:
    f.writelines(new_lines)

print('Fixed indentation!')
