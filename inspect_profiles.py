import re
from pathlib import Path

with open('mentor/distill_digest_refresh.txt', encoding='utf-8', errors='replace') as f:
    text = f.read()

profiles = {}
lines = text.split('\n')
current_profile = None
current_lines = []

for line in lines:
    if line.startswith('### '):
        if current_profile and current_lines:
            profiles[current_profile] = '\n'.join(current_lines)
        tag_match = re.search(r'\[([^\]]+)\]', line)
        profile_tag = tag_match.group(1) if tag_match else None
        if profile_tag in ('rakhimoff_amir', 'ivy_roadmap'):
            current_profile = profile_tag
            current_lines = [line]
        else:
            current_profile = None
            current_lines = []
    elif current_profile is not None:
        current_lines.append(line)

if current_profile:
    profiles[current_profile] = '\n'.join(current_lines)

for profile in sorted(profiles):
    content = profiles[profile]
    print(f"=== {profile} ===")
    non_empty = [l for l in content.split('\n') if l.strip() and not l.startswith('===') and not l.startswith('### ')]
    codes = re.findall(r'### ([A-Za-z0-9_-]{10,15})', content)
    print(f"  Sections: {len(re.findall('===', content))}")
    print(f"  Transcript refs: {codes}")
    print(f"  Substantive lines: {len(non_empty)}")
    for snippet in non_empty[:6]:
        print(f"    {snippet[:160]}")
    print()
