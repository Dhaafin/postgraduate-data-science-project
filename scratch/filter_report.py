import re

file_path = r'c:\[Dhaafin]\Projects\Personal Projects\data-scraping\docs\ARTIST_VALIDATION_REPORT.md'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
# Keep headers
for i in range(min(18, len(lines))):
    new_lines.append(lines[i])

# Filter table
for line in lines[18:]:
    if '❓ UNCERTAIN' in line or '🌎 FOREIGN' in line:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
