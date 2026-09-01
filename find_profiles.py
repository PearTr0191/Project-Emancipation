import re
from pathlib import Path
from collections import Counter, defaultdict

profiles = defaultdict(set)

# From digest file
with open('mentor/distill_digest_refresh.txt', encoding='utf-8', errors='replace') as f:
    digest = f.read()

# Find profile-tagged sections
current_profile = None
current_codes = []
for line in digest.split('\n'):
    if line.startswith('### '):
        if current_profile:
            profiles[current_profile].update(current_codes)
        m = re.search(r'\[([^\]]+)\]', line)
        current_profile = m.group(1) if m else 'unknown'
        current_codes = []
        # Extract code from the line header (before [profile])
        line_before_tag = line.split('[')[0].strip()
        if line_before_tag.startswith('### '):
            current_codes.append(line_before_tag.replace('### ', '').strip())
    else:
        current_codes.append(line)

if current_profile:
    profiles[current_profile].update(current_codes)

# From transcript directory - search file contents for profile tags
transcript_dir = Path('mentor/transcripts')
for f in transcript_dir.glob('*.md'):
    text = f.read_text(encoding='utf-8', errors='replace')
    for profile in ['rakhimoff_amir', 'ivy_roadmap', 'ultimateivyleagueguide']:
        if profile in text.lower() or profile.replace('_', '') in text.lower():
            profiles[profile].add(f.stem)

for p in sorted(profiles):
    print(f"{p}: {len(profiles[p])} unique codes")
    codes = sorted(list(profiles[p]))[:10]
    print(f"  {codes}")
