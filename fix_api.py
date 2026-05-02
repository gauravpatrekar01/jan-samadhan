import re

with open('js/api_backup.js', 'r', encoding='utf-8') as f:
    backup_code = f.read()

with open('js/api_stable.js', 'r', encoding='utf-8') as f:
    current_code = f.read()

class_end_idx = current_code.find('\n}\n\n// Create global API instance')

methods = re.findall(r'(    async [a-zA-Z0-9_]+\([^)]*\)\s*\{[\s\S]*?\n    \})', backup_code)
existing_methods = re.findall(r'    async ([a-zA-Z0-9_]+)\(', current_code)

missing_methods = []
for m in methods:
    name_match = re.search(r'async ([a-zA-Z0-9_]+)\(', m)
    if name_match:
        name = name_match.group(1)
        if name not in existing_methods and name not in ['_fetch', 'getAnalytics', 'getNotices', 'getGrievanceByID']:
            missing_methods.append(m)

aliases = """
    // Aliases for frontend compatibility
    async getAnalytics() {
        return this.getPublicStats();
    }
    
    async getNotices() {
        return [
            { date: new Date().toISOString(), text: "System maintenance scheduled for this weekend.", pinned: true },
            { date: new Date().toISOString(), text: "New guidelines for emergency grievances published.", pinned: false }
        ];
    }
    
    async getGrievanceByID(id) {
        return this.getComplaint(id);
    }
"""

new_code = current_code[:class_end_idx] + '\n\n' + aliases + '\n\n' + '\n\n'.join(missing_methods) + current_code[class_end_idx:]

with open('js/api.js', 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Done")
