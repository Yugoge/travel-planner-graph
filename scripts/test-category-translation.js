// Test script to verify formatCategoryLabel handles compound categories
const CATEGORY_MAPPINGS = {
  attraction_types: {
    'church': '教堂',
    'museum': '博物馆',
    'historic_building': '历史建筑',
    'historic building': '历史建筑',
    'historic_site': '历史遗址',
    'pedestrian_area': '步行区',
    'pedestrian area': '步行区'
  }
};

function formatCategoryLabel(code, type) {
  if (!code) return '';

  let mapping;
  if (type === 'attraction') {
    mapping = CATEGORY_MAPPINGS.attraction_types;
  } else {
    return code;
  }

  // Handle compound categories with slashes
  if (code.toString().includes('/')) {
    const parts = code.toString().split('/');
    const translatedParts = [];
    for (const part of parts) {
      const trimmed = part.trim();
      const normalized = trimmed.toLowerCase().replace(/\s+/g, '_');
      const translated = mapping[normalized] || mapping[trimmed.toLowerCase()] || mapping[trimmed] || trimmed;
      translatedParts.push(translated);
    }
    return translatedParts.join(' / ');
  }

  // Single category: Normalize the code for mapping lookup
  const normalizedCode = code.toString().trim().toLowerCase().replace(/\s+/g, '_');

  // Try normalized code first, then original code with space normalization
  return mapping[normalizedCode] || mapping[code.toString().trim().toLowerCase()] || mapping[code] || code;
}

// Test cases
console.log('Test 1 - Single category:');
console.log('  Input: "museum"');
console.log('  Output:', formatCategoryLabel('museum', 'attraction'));
console.log('  Expected: 博物馆');
console.log();

console.log('Test 2 - Compound category:');
console.log('  Input: "Church / Museum / Historic Building"');
console.log('  Output:', formatCategoryLabel('Church / Museum / Historic Building', 'attraction'));
console.log('  Expected: 教堂 / 博物馆 / 历史建筑');
console.log();

console.log('Test 3 - Mixed case compound:');
console.log('  Input: "church / museum"');
console.log('  Output:', formatCategoryLabel('church / museum', 'attraction'));
console.log('  Expected: 教堂 / 博物馆');
console.log();

console.log('Test 4 - Unknown compound category:');
console.log('  Input: "Unknown Type / Museum"');
console.log('  Output:', formatCategoryLabel('Unknown Type / Museum', 'attraction'));
console.log('  Expected: Unknown Type / 博物馆');
