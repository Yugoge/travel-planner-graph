// Test formatter functions extracted from generated HTML
const CATEGORY_MAPPINGS = {
  attraction_types: {
    'historical_site': 'Historical Site / 历史遗址',
    'museum': 'Museum / 博物馆',
    'temple': 'Temple / 寺庙',
    'natural_scenery': 'Natural Scenery / 自然景观',
    'park': 'Park / 公园',
    'cultural_experience': 'Cultural Experience / 文化体验',
    'ancient_architecture': 'Ancient Architecture / 古建筑',
    'modern_landmark': 'Modern Landmark / 现代地标',
    'unesco_heritage': 'UNESCO Heritage / 世界遗产',
    'scenic_spot': 'Scenic Spot / 风景名胜',
    'night_view': 'Night View / 夜景',
    'street_food': 'Street Food Area / 美食街',
    'shopping_district': 'Shopping District / 购物区'
  },
  hotel_categories: {
    'budget': 'Budget Hotel / 经济型酒店',
    'mid-range': 'Mid-Range Hotel / 中档酒店',
    'high-end': 'High-End Hotel / 高档酒店',
    'luxury': 'Luxury Hotel / 豪华酒店',
    'boutique': 'Boutique Hotel / 精品酒店',
    'hostel': 'Hostel / 青年旅社',
    'guesthouse': 'Guesthouse / 民宿'
  },
  restaurant_categories: {
    'local': 'Local Cuisine / 本地菜',
    'street_food': 'Street Food / 街头小吃',
    'fine_dining': 'Fine Dining / 高级餐厅',
    'casual': 'Casual Dining / 休闲餐厅',
    'fast_food': 'Fast Food / 快餐',
    'vegetarian': 'Vegetarian / 素食',
    'halal': 'Halal / 清真',
    'international': 'International / 国际美食',
    'cafe': 'Café / 咖啡馆',
    'teahouse': 'Teahouse / 茶馆'
  },
  entertainment_types: {
    'show': 'Show / 演出',
    'nightlife': 'Nightlife / 夜生活',
    'bar': 'Bar / 酒吧',
    'club': 'Club / 夜店',
    'karaoke': 'Karaoke / KTV',
    'theater': 'Theater / 剧院',
    'cinema': 'Cinema / 电影院',
    'live_music': 'Live Music / 现场音乐'
  }
};

function formatCategoryLabel(code, type) {
  if (!code) return '';

  let mapping;
  if (type === 'attraction') {
    mapping = CATEGORY_MAPPINGS.attraction_types;
  } else if (type === 'hotel') {
    mapping = CATEGORY_MAPPINGS.hotel_categories;
  } else if (type === 'restaurant') {
    mapping = CATEGORY_MAPPINGS.restaurant_categories;
  } else if (type === 'entertainment') {
    mapping = CATEGORY_MAPPINGS.entertainment_types;
  } else {
    return code;
  }

  return mapping[code] || code;
}

function formatAddress(address) {
  if (!address || address === null || address === 'null' || address.trim() === '') {
    return 'Address not available / 地址未提供';
  }
  return address;
}

// Test cases
console.log('Testing formatCategoryLabel():');
console.log('  historical_site (attraction):', formatCategoryLabel('historical_site', 'attraction'));
console.log('  mid-range (hotel):', formatCategoryLabel('mid-range', 'hotel'));
console.log('  local (restaurant):', formatCategoryLabel('local', 'restaurant'));
console.log('  show (entertainment):', formatCategoryLabel('show', 'entertainment'));
console.log('  unknown_code (attraction):', formatCategoryLabel('unknown_code', 'attraction'));
console.log('');

console.log('Testing formatAddress():');
console.log('  null:', formatAddress(null));
console.log('  "null":', formatAddress('null'));
console.log('  "":', formatAddress(''));
console.log('  "   ":', formatAddress('   '));
console.log('  "123 Main St":', formatAddress('123 Main St'));
console.log('');

// Expected results
const tests = [
  { fn: 'formatCategoryLabel', args: ['historical_site', 'attraction'], expected: 'Historical Site / 历史遗址' },
  { fn: 'formatCategoryLabel', args: ['mid-range', 'hotel'], expected: 'Mid-Range Hotel / 中档酒店' },
  { fn: 'formatCategoryLabel', args: ['local', 'restaurant'], expected: 'Local Cuisine / 本地菜' },
  { fn: 'formatAddress', args: [null], expected: 'Address not available / 地址未提供' },
  { fn: 'formatAddress', args: [''], expected: 'Address not available / 地址未提供' },
  { fn: 'formatAddress', args: ['123 Main St'], expected: '123 Main St' }
];

let passed = 0;
let failed = 0;

console.log('Running automated tests:');
tests.forEach((test, idx) => {
  const fn = test.fn === 'formatCategoryLabel' ? formatCategoryLabel : formatAddress;
  const result = fn(...test.args);
  const status = result === test.expected ? 'PASS' : 'FAIL';

  if (status === 'PASS') {
    passed++;
    console.log(`  ✓ Test ${idx + 1}: ${status}`);
  } else {
    failed++;
    console.log(`  ✗ Test ${idx + 1}: ${status}`);
    console.log(`    Expected: "${test.expected}"`);
    console.log(`    Got: "${result}"`);
  }
});

console.log('');
console.log(`Summary: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
