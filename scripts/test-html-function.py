#!/usr/bin/env python3
"""Test that formatCategoryLabel JavaScript function works correctly in HTML."""

import subprocess
import sys
from pathlib import Path

# Create a minimal HTML test file
test_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Category Translation</title>
</head>
<body>
    <div id="output"></div>
    <script>
"""

# Read the actual formatCategoryLabel function from html_generator.py
generator_file = Path('scripts/lib/html_generator.py')
with open(generator_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract CATEGORY_MAPPINGS
import re
mappings_match = re.search(r'const CATEGORY_MAPPINGS = \{\{(.*?)\}\};', content, re.DOTALL)
if not mappings_match:
    print("Could not find CATEGORY_MAPPINGS")
    sys.exit(1)

mappings = "const CATEGORY_MAPPINGS = {" + mappings_match.group(1).replace('{{', '{').replace('}}', '}') + "};"

# Extract formatCategoryLabel function
func_match = re.search(r'function formatCategoryLabel\(code, type\) \{\{(.*?)\n    \}\}', content, re.DOTALL)
if not func_match:
    print("Could not find formatCategoryLabel function")
    sys.exit(1)

func = "function formatCategoryLabel(code, type) {" + func_match.group(1).replace('{{', '{').replace('}}', '}') + "\n}"

test_html += mappings + "\n\n" + func + """

// Test cases
const testCases = [
    'Church / Museum / Historic Building',
    'Mountain / Observation Deck / Tourist Attraction',
    'Buddhist Temple / Historic Site',
    'Winter Theme Park / Ice Sculpture Park',
    'Historic Street / Pedestrian Area',
    'museum'
];

let output = 'Compound Category Translation Test Results:\\n';
output += '===========================================\\n\\n';

testCases.forEach(test => {
    const result = formatCategoryLabel(test, 'attraction');
    output += 'Input:  ' + test + '\\n';
    output += 'Output: ' + result + '\\n';
    output += 'Status: ' + (result !== test && result.includes('/') ? '✓ TRANSLATED' : (result !== test ? '✓ TRANSLATED' : '✗ NOT TRANSLATED')) + '\\n\\n';
});

console.log(output);
document.getElementById('output').innerHTML = '<pre>' + output + '</pre>';
    </script>
</body>
</html>
"""

# Write test HTML
test_file = Path('data/test-category-translation.html')
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(test_html)

print(f"Created test file: {test_file}")
print("Running test with Node.js...")

# Extract and run just the JavaScript
js_code = test_html.split('<script>')[1].split('</script>')[0]

# Run with Node.js
result = subprocess.run(['node', '-e', js_code], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr, file=sys.stderr)
    sys.exit(1)

print("✓ Test completed successfully")
