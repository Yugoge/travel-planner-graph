# Gaode Maps - Geocoding Tools

Location conversion tools for addresses, coordinates, and IP-based location.

## Available Tools

### 1. geocode

Convert address to coordinates (forward geocoding).

**MCP Tool**: `geocode`

**Parameters**:
- `address` (required): Address to geocode (e.g., "北京市朝阳区国贸", "重庆洪崖洞")
- `city` (optional): City name to improve accuracy (e.g., "北京")

**Returns**:
- Formatted address
- Province
- City
- District
- Township
- Street
- Neighborhood
- Coordinates (longitude, latitude in GCJ-02)
- Geocode level (country, province, city, district, street, POI)

**Example**:
```javascript
// Geocode attraction name
geocode({
  address: "洪崖洞",
  city: "重庆"
})

// Returns: { lng: 106.583299, lat: 29.560299, ... }
```

**Use Cases**:
- Convert user-provided addresses to coordinates
- Validate address existence
- Get administrative division information
- Prepare coordinates for nearby search or routing

---

### 2. reverse_geocode

Convert coordinates to address (reverse geocoding).

**MCP Tool**: `reverse_geocode`

**Parameters**:
- `location` (required): Coordinates in "longitude,latitude" format (e.g., "116.481488,39.990464")
- `radius` (optional): Search radius in meters (default 1000, max 3000)

**Returns**:
- Formatted address
- Province, city, district
- Township, street, neighborhood
- POI name (if coordinates match a POI)
- Address components (structured)
- Cross information (nearest roads, intersections)

**Example**:
```javascript
// Get address from coordinates
reverse_geocode({
  location: "104.065735,30.659462",  // Chengdu coordinates
  radius: 100
})

// Returns: "四川省成都市锦江区红星路三段1号"
```

**Use Cases**:
- Display human-readable addresses from GPS coordinates
- Verify location accuracy
- Get nearby POI information
- Generate location descriptions

---

### 3. ip_location

Get location from IP address.

**MCP Tool**: `ip_location`

**Parameters**:
- `ip` (optional): IP address (if omitted, uses requester's IP)

**Returns**:
- Province
- City
- Ad code (administrative division code)
- Rectangular region (coordinates)

**Example**:
```javascript
// Get location of user's IP
ip_location()

// Get location of specific IP
ip_location({ ip: "220.181.38.148" })
```

**Use Cases**:
- Auto-detect user's current city
- Suggest nearby destinations
- Customize content by location
- Analytics and logging

---

## Coordinate Systems

### GCJ-02 (Mars Coordinates)

Gaode Maps uses GCJ-02 coordinate system:
- Used in: Mainland China
- Offset from WGS-84 by 50-500 meters
- Required for: Gaode Maps, Baidu Maps, Tencent Maps

**Important**: Don't manually convert between coordinate systems. Gaode API handles this automatically.

### WGS-84 (GPS Coordinates)

Standard GPS coordinates:
- Used in: International GPS devices, Google Maps (outside China)
- Direct satellite positioning

**Gaode Maps handles conversion**:
- Input: WGS-84 or GCJ-02 (auto-detected)
- Output: GCJ-02 for China locations
- Output: WGS-84 for international locations

---

## Best Practices

### 1. Address Input Flexibility

Accept various address formats:

**Full address**:
```javascript
geocode({ address: "四川省成都市武侯区天府大道天府软件园" })
```

**Partial address with city context**:
```javascript
geocode({
  address: "天府软件园",
  city: "成都"  // Improves accuracy
})
```

**Landmark name**:
```javascript
geocode({
  address: "春熙路",
  city: "成都"
})
```

**Multi-language support**:
```javascript
// Chinese
geocode({ address: "北京故宫" })

// English (limited support)
geocode({ address: "Forbidden City Beijing" })
```

### 2. Geocoding Validation

**Check geocode level**:
```javascript
function isAccurateGeocode(result) {
  // Prefer POI, street, or district level
  const acceptableLevels = ['POI', 'street', 'district'];
  return acceptableLevels.includes(result.level);
}

const result = await geocode({ address: "洪崖洞", city: "重庆" });
if (!isAccurateGeocode(result)) {
  console.warn('Geocode result may be imprecise');
}
```

**Handle ambiguous addresses**:
```javascript
async function disambiguateAddress(address, city) {
  const result = await geocode({ address, city });

  if (result.level === 'city' || result.level === 'province') {
    // Too vague, search POI instead
    const pois = await poi_search_keyword({
      keywords: address,
      city: city,
      page_size: 1
    });

    if (pois.count > 0) {
      return {
        lng: pois.pois[0].location.lng,
        lat: pois.pois[0].location.lat,
        address: pois.pois[0].address
      };
    }
  }

  return result;
}
```

### 3. Reverse Geocoding Use Cases

**Get nearest POI**:
```javascript
async function getNearestPOI(lng, lat) {
  const result = await reverse_geocode({
    location: `${lng},${lat}`,
    radius: 100  // Small radius for exact match
  });

  return result.poi || result.formatted_address;
}
```

**Get administrative info**:
```javascript
async function getAdministrativeInfo(lng, lat) {
  const result = await reverse_geocode({
    location: `${lng},${lat}`
  });

  return {
    province: result.province,
    city: result.city,
    district: result.district,
    street: result.street
  };
}
```

**Format location for display**:
```javascript
function formatLocationForDisplay(reverseGeocodeResult) {
  const { poi, formatted_address, district, street } = reverseGeocodeResult;

  if (poi) {
    return poi;  // POI name is most recognizable
  }

  if (district && street) {
    return `${district} ${street}`;  // Short format
  }

  return formatted_address;  // Full address as fallback
}
```

### 4. IP Location Use Cases

**Auto-detect user city**:
```javascript
async function getUserCity() {
  try {
    const location = await ip_location();
    return location.city;
  } catch (error) {
    console.warn('IP location failed, using default');
    return '北京';  // Default city
  }
}
```

**Suggest nearby destinations**:
```javascript
async function suggestDestinations() {
  const userCity = await getUserCity();

  // Suggest destinations within same province or nearby provinces
  const suggestions = getNearbyDestinations(userCity);

  return suggestions;
}
```

### 5. Batch Geocoding

**Process multiple addresses**:
```javascript
async function batchGeocode(addresses, city) {
  const results = [];

  for (const address of addresses) {
    try {
      const result = await geocode({ address, city });
      results.push({
        address,
        coordinates: { lng: result.lng, lat: result.lat },
        success: true
      });
    } catch (error) {
      results.push({
        address,
        error: error.message,
        success: false
      });
    }

    // Rate limiting: small delay between requests
    await sleep(100);
  }

  return results;
}
```

### 6. Error Handling

**Handle geocoding failures**:
```javascript
async function safeGeocode(address, city) {
  try {
    return await geocode({ address, city });
  } catch (error) {
    if (error.message.includes('not found')) {
      // Try without city constraint
      try {
        return await geocode({ address });
      } catch (error2) {
        // Fall back to POI search
        const pois = await poi_search_keyword({
          keywords: address,
          city: city
        });

        if (pois.count > 0) {
          return {
            lng: pois.pois[0].location.lng,
            lat: pois.pois[0].location.lat,
            address: pois.pois[0].address,
            source: 'poi_search'
          };
        }

        throw new Error(`Unable to geocode: ${address}`);
      }
    }
    throw error;
  }
}
```

**Handle invalid coordinates**:
```javascript
function validateCoordinates(lng, lat) {
  // China bounding box (approximate)
  const MIN_LNG = 73.5;
  const MAX_LNG = 135.0;
  const MIN_LAT = 3.5;
  const MAX_LAT = 53.5;

  if (lng < MIN_LNG || lng > MAX_LNG) {
    throw new Error(`Invalid longitude: ${lng}`);
  }

  if (lat < MIN_LAT || lat > MAX_LAT) {
    throw new Error(`Invalid latitude: ${lat}`);
  }

  return true;
}

async function safeReverseGeocode(lng, lat) {
  validateCoordinates(lng, lat);
  return await reverse_geocode({ location: `${lng},${lat}` });
}
```

---

## Integration with Other Tools

### Chain Geocoding → Nearby Search

```javascript
async function findNearbyRestaurants(address, city) {
  // 1. Geocode the address
  const coords = await geocode({ address, city });

  // 2. Search nearby restaurants
  const restaurants = await poi_search_nearby({
    location: `${coords.lng},${coords.lat}`,
    keywords: "餐厅",
    types: "050100",
    radius: 1000
  });

  return restaurants;
}
```

### Chain Geocoding → Routing

```javascript
async function planRoute(originAddress, destAddress, city) {
  // 1. Geocode both addresses
  const origin = await geocode({ address: originAddress, city });
  const dest = await geocode({ address: destAddress, city });

  // 2. Plan driving route
  const route = await driving_route({
    origin: `${origin.lng},${origin.lat}`,
    destination: `${dest.lng},${dest.lat}`
  });

  return route;
}
```

### Use IP Location for Context

```javascript
async function contextAwareSearch(keywords) {
  // 1. Get user's city from IP
  const location = await ip_location();
  const city = location.city;

  // 2. Search in user's city
  const results = await poi_search_keyword({
    keywords,
    city,
    citylimit: true
  });

  return { city, results };
}
```

---

## Integration with Travel Planning Agents

### Transportation Agent

```javascript
// Geocode origin and destination for route planning
async function planInterCityRoute(fromCity, toCity) {
  // 1. Geocode cities (use city center or train station)
  const origin = await geocode({
    address: `${fromCity}火车站`,
    city: fromCity
  });

  const destination = await geocode({
    address: `${toCity}火车站`,
    city: toCity
  });

  // 2. Plan transit route
  const route = await transit_route({
    origin: `${origin.lng},${origin.lat}`,
    destination: `${destination.lng},${destination.lat}`,
    cityd: toCity
  });

  return route;
}
```

### Accommodation Agent

```javascript
// Geocode accommodation address for nearby searches
async function processAccommodation(hotelName, city) {
  // 1. Geocode hotel
  const coords = await geocode({
    address: hotelName,
    city: city
  });

  // 2. Find nearby conveniences
  const restaurants = await poi_search_nearby({
    location: `${coords.lng},${coords.lat}`,
    keywords: "餐厅",
    radius: 500
  });

  const metro = await poi_search_nearby({
    location: `${coords.lng},${coords.lat}`,
    types: "150600",  // Subway stations
    radius: 1000
  });

  return {
    coordinates: coords,
    nearby_restaurants: restaurants.count,
    nearest_metro: metro.pois[0]?.name
  };
}
```

### Attractions Agent

```javascript
// Geocode attraction for distance calculation
async function processAttraction(attractionName, city, hotelAddress) {
  // 1. Geocode attraction
  const attraction = await geocode({
    address: attractionName,
    city: city
  });

  // 2. Geocode hotel
  const hotel = await geocode({
    address: hotelAddress,
    city: city
  });

  // 3. Calculate distance
  const distance = await distance_measure({
    origins: `${hotel.lng},${hotel.lat}`,
    destination: `${attraction.lng},${attraction.lat}`
  });

  return {
    attraction_coords: attraction,
    distance_from_hotel: distance,
    formatted_address: attraction.formatted_address
  };
}
```

---

## Example: Complete Address Processing Pipeline

```javascript
async function processLocationPipeline(userInput, city) {
  // Step 1: Try geocoding
  let coords;
  try {
    const geocodeResult = await geocode({
      address: userInput,
      city: city
    });

    if (isAccurateGeocode(geocodeResult)) {
      coords = { lng: geocodeResult.lng, lat: geocodeResult.lat };
    } else {
      // Step 2: Geocode not precise, try POI search
      const pois = await poi_search_keyword({
        keywords: userInput,
        city: city,
        citylimit: true,
        page_size: 1
      });

      if (pois.count > 0) {
        coords = pois.pois[0].location;
      } else {
        throw new Error('Location not found');
      }
    }
  } catch (error) {
    console.error('Geocoding failed:', error);
    throw error;
  }

  // Step 3: Reverse geocode to get formatted address
  const reverseResult = await reverse_geocode({
    location: `${coords.lng},${coords.lat}`,
    radius: 100
  });

  return {
    coordinates: coords,
    formatted_address: reverseResult.formatted_address,
    poi_name: reverseResult.poi,
    district: reverseResult.district,
    confidence: 'high'
  };
}
```
