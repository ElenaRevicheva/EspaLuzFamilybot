with open('main.py', 'r') as f:
    lines = f.readlines()

# Fix line 3635 (0-indexed: 3634) - data = json.load(f)
if '            data = json.load(f)' in lines[3635]:
    lines[3635] = lines[3635].replace('            data', '                data')

# Fix lines around 3636-3643
fixes = {
    3636: ('            if user_email', '                if user_email'),
    3637: ('                data[user_email]', '                    data[user_email]'),
    3638: ('                f.seek', '                    f.seek'),
    3639: ('                json.dump', '                    json.dump'),
    3640: ('                f.truncate', '                    f.truncate'),
    3641: ('                bot.send_message', '                    bot.send_message'),
    3642: ('            else:', '                else:'),
    3643: ('                    bot.send', '                        bot.send'),
}

for line_no, (old, new) in fixes.items():
    if old in lines[line_no]:
        lines[line_no] = lines[line_no].replace(old, new)

with open('main.py', 'w') as f:
    f.writelines(lines)

print('Fixed!')
