import os

file_path = r'c:\[Dhaafin]\Projects\Personal Projects\data-scraping\docs\ARTIST_VALIDATION_REPORT.md'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
# Keep headers until the table starts
in_table = False
table_header_count = 0
for line in lines:
    if line.startswith('| Artist Name |'):
        in_table = True
        new_lines.append(line)
        continue
    
    if in_table:
        if line.startswith('| :--- |'):
            new_lines.append(line)
            continue
        
        # Filter table rows
        if '❓ UNCERTAIN' in line or '🌎 FOREIGN' in line:
            new_lines.append(line)
    else:
        # Keep summary statistics but maybe mark it as "Filtered for Review"
        if '## 📊 Summary Statistics' in line:
            new_lines.append(line)
            new_lines.append("> **Note**: This report has been filtered to show only records requiring manual review.\n")
            continue
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Filtered report written to {file_path}")
