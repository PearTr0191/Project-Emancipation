from pathlib import Path

# Verify the two modified files
files = ['mentor/knowledge/school-list-strategy.md', 'mentor/knowledge/core-theme.md']
for f in files:
    text = Path(f).read_text(encoding='utf-8', errors='replace')
    dirty = 'Distilled items' in text
    lines = len(text.split(chr(10)))
    has_scholarship = 'QuestBridge' in text
    has_beast = 'beast with a story' in text
    print(f"{Path(f).name:32} {lines:>4} lines CLEAN={not dirty}")
    print(f"  scholarship ref added: {has_scholarship} | anti-prestige ref added: {has_beast}")

# Verify no other files changed
kb = Path('mentor/knowledge')
kb_files = sorted([f.name for f in kb.glob('*.md')])
all_clean = all('Distilled items' not in open(f'mentor/knowledge/{f}', encoding='utf-8', errors='replace').read() for f in kb_files)
print(f"All {len(kb_files)} KB files clean: {all_clean}")

# Verify workspace noise is still removed
noise = ['chrome_profile', '__pycache__', 'rollback_kb.py', 'debug_reel_video.py',
         'debug_scroll3.py', 'pending_codes.json', 'pipeline_state.json', 'manifest_delta.json',
         'manifest.json.bak', 'process_profiles.py', 'mentor/inbox', 'mentor/pipeline', 'extractig.md']
all_removed = True
for item in noise:
    if '/' in item:
        p = Path('.').joinpath(*item.split('/'))
    else:
        p = Path(item)
    if p.exists():
        all_removed = False
        print(f"  STILL PRESENT: {item}")
print(f"All noise removed: {all_removed}")