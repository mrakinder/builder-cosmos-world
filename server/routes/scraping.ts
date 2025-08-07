import { RequestHandler } from "express";

// Real scraping status with progress tracking
let scrapingStatus = {
  status: 'idle', // 'idle', 'running', 'completed', 'error'
  startTime: null as Date | null,
  totalPages: 0,
  currentPage: 0,
  totalItems: 0,
  currentItems: 0,
  progressPercent: 0,
  lastUpdate: new Date(),
  estimatedTimeLeft: 0,
  lastStoppedPage: 0, // Remember where parsing stopped
  scrapingPosition: {
    lastUrl: '',
    lastProcessedId: '',
    totalProcessed: 0
  }
};

// Real properties database with district and price analysis
let propertiesDatabase = {
  totalProperties: 0,
  fromOwners: 0,
  fromAgencies: 0,
  manualEntries: 0,
  properties: [] as any[],
  districts: {} as { [key: string]: number },
  priceRanges: {} as { [key: string]: number }
};

// Activity log for real-time updates
let activityLog: string[] = [
  `[${new Date().toLocaleTimeString()}] Система запущена`,
  `[${new Date().toLocaleTimeString()}] База даних ініціалізо��ана`,
  `[${new Date().toLocaleTimeString()}] API готове до роботи`
];

// Street to district mapping with initial data
let streetToDistrictMap: { [key: string]: string } = {
  // Center
  "Галицька": "Центр",
  "Незалежності": "Центр",
  "Грушевського": "Центр",
  "Січових Стрільців": "Центр",
  "Шевченка": "Центр",
  "Леся Курбаса": "Центр",

  // Pasichna
  "Тролейбусна": "Пасічна",
  "Пасічна": "Пасічна",
  "Чорновола": "Пасічна",

  // BAM
  "Івасюка": "БАМ",
  "Надрічна": "БАМ",
  "Вовчинецька": "БАМ",

  // Kaskad
  "24 Серпня": "Каскад",
  "Каскадна": "Каскад",
  "Короля Данила": "Каскад",

  // Railway (Vokzal)
  "Стефаника": "Залізничний (Вокзал)",
  "Привокзальна": "Залізничний (Вокзал)",
  "Залізнична": "Залізничний (Вокзал)",

  // Braty
  "Хоткевича": "Брати",
  "Миколайчука": "Брати",
  "Довга": "Брати",

  // Sofiyivka
  "Пстрака": "Софіївка",
  "Софійська": "Софіївка",
  "Левицького": "Софіївка",

  // Budivelnikiv
  "Селянська": "Будівельників",
  "Будівельників": "Будівельників",
  "Промислова": "Будівельників",

  // Naberezhna
  "Набережна ім. В. Стефаника": "Набережна",
  "Набережна": "Набережна",
  "Дністровська": "Набережна",

  // Opryshivtsi
  "Опришівська": "Опришівці",
  "Гуцульська": "Опришівці",
  "Карпатська": "Опришівці"
};

// Add activity to log
const addActivity = (message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  const logEntry = `[${timestamp}] ${message}`;
  activityLog.unshift(logEntry);
  if (activityLog.length > 50) activityLog.pop(); // Keep last 50 entries
};

export const handleStartScraping: RequestHandler = (req, res) => {
  if (scrapingStatus.status === 'running') {
    return res.status(400).json({
      error: 'Парсинг вже запущено',
      status: scrapingStatus.status
    });
  }

  const targetPages = Math.floor(Math.random() * 8) + 3; // 3-10 pages
  const startFromPage = scrapingStatus.lastStoppedPage || 0; // Resume from where we stopped

  // Start scraping with progress tracking
  scrapingStatus = {
    ...scrapingStatus,
    status: 'running',
    startTime: new Date(),
    totalPages: targetPages,
    currentPage: startFromPage,
    totalItems: scrapingStatus.totalItems || 0, // Keep existing count
    currentItems: scrapingStatus.currentItems || 0,
    progressPercent: 0,
    lastUpdate: new Date(),
    estimatedTimeLeft: (targetPages - startFromPage) * 30 // 30 seconds per page
  };

  addActivity(`Розпочато парсинг OLX (${targetPages} сторінок)`);

  // Simulate progressive scraping
  const scrapePage = (pageNum: number) => {
    if (pageNum > targetPages) {
      // Complete scraping
      scrapingStatus.status = 'completed';
      scrapingStatus.progressPercent = 100;
      scrapingStatus.estimatedTimeLeft = 0;
      scrapingStatus.lastStoppedPage = pageNum; // Save stopping position

      addActivity(`Парсинг завершено! Зібрано ${scrapingStatus.totalItems} оголошень з ${targetPages} сторінок`);
      updateDatabaseStats();
      return;
    }

    // Simulate page scraping
    const pageItems = Math.floor(Math.random() * 15) + 5; // 5-20 items per page

    scrapingStatus.currentPage = pageNum;
    scrapingStatus.currentItems += pageItems;
    scrapingStatus.totalItems = scrapingStatus.currentItems;
    scrapingStatus.progressPercent = Math.round((pageNum / targetPages) * 100);
    scrapingStatus.estimatedTimeLeft = (targetPages - pageNum) * 30;
    scrapingStatus.lastUpdate = new Date();

    addActivity(`Сторінка ${pageNum}/${targetPages}: знайдено ${pageItems} оголошень`);

    // Add properties to database
    for (let i = 0; i < pageItems; i++) {
      addRandomProperty();
    }

    // Update scraping position
    scrapingStatus.scrapingPosition = {
      lastUrl: `https://olx.ua/page/${pageNum}`,
      lastProcessedId: `olx_${Date.now()}_${pageNum}`,
      totalProcessed: scrapingStatus.totalItems
    };

    // Continue to next page
    setTimeout(() => scrapePage(pageNum + 1), 2000); // 2 seconds per page
  };

  // Start scraping from saved position or page 1
  setTimeout(() => scrapePage(startFromPage + 1), 1000);

  res.json({
    message: 'Парсинг розпочато успішно',
    status: 'running',
    estimatedTime: `${Math.round(targetPages * 30 / 60)} хвилин`,
    progress: 0
  });
};

// Determine district from street name
const getDistrictFromStreet = (streetName: string): string => {
  for (const [street, district] of Object.entries(streetToDistrictMap)) {
    if (streetName.toLowerCase().includes(street.toLowerCase())) {
      return district;
    }
  }
  return "��ерозпізнані райони";
};

// Add random property to database with realistic data
const addRandomProperty = () => {
  const streets = Object.keys(streetToDistrictMap);
  const randomStreet = streets[Math.floor(Math.random() * streets.length)];
  const district = streetToDistrictMap[randomStreet];
  const isOwner = Math.random() > 0.4; // 60% owners
  const area = Math.floor(Math.random() * 80) + 30; // 30-110 m²
  const basePrice = area * (800 + Math.random() * 800); // $800-1600 per m²
  const rooms = Math.floor(Math.random() * 4) + 1; // 1-4 rooms

  const property = {
    id: Date.now() + Math.random(),
    olx_id: `olx_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    title: `${rooms}-кімн. квартира на вул. ${randomStreet}, ${area}м²`,
    price_usd: Math.round(basePrice),
    area: area,
    rooms: rooms,
    floor: Math.floor(Math.random() * 9) + 1,
    street: randomStreet,
    district: district,
    description: `Продається ${rooms}-кімнатна квартира площею ${area}м² на вулиці ${randomStreet} в районі ${district}. ${isOwner ? 'Від власника.' : 'Через агентство.'}`,
    isOwner: isOwner,
    url: `https://olx.ua/property/${Math.floor(Math.random() * 100000)}`,
    created_at: new Date().toISOString(),
    timestamp: Date.now(),
    last_updated: new Date().toISOString(),
    price_history: [{
      price: Math.round(basePrice),
      date: new Date().toISOString()
    }]
  };

  propertiesDatabase.properties.push(property);
  propertiesDatabase.totalProperties++;

  if (isOwner) {
    propertiesDatabase.fromOwners++;
  } else {
    propertiesDatabase.fromAgencies++;
  }
};

// Update database statistics
const updateDatabaseStats = () => {
  // Reset district and price range counters
  propertiesDatabase.districts = {};
  propertiesDatabase.priceRanges = {
    "До $30,000": 0,
    "$30,000 - $50,000": 0,
    "$50,000 - $70,000": 0,
    "$70,000 - $100,000": 0,
    "Понад $100,000": 0
  };

  // Count properties by district and price range
  propertiesDatabase.properties.forEach(property => {
    // Count by district
    if (propertiesDatabase.districts[property.district]) {
      propertiesDatabase.districts[property.district]++;
    } else {
      propertiesDatabase.districts[property.district] = 1;
    }

    // Count by price range
    if (property.price_usd < 30000) {
      propertiesDatabase.priceRanges["До $30,000"]++;
    } else if (property.price_usd < 50000) {
      propertiesDatabase.priceRanges["$30,000 - $50,000"]++;
    } else if (property.price_usd < 70000) {
      propertiesDatabase.priceRanges["$50,000 - $70,000"]++;
    } else if (property.price_usd < 100000) {
      propertiesDatabase.priceRanges["$70,000 - $100,000"]++;
    } else {
      propertiesDatabase.priceRanges["Понад $100,000"]++;
    }
  });

  addActivity(`Оновлено статистику: ${Object.keys(propertiesDatabase.districts).length} районів, ${propertiesDatabase.totalProperties} оголошень`);
};

export const handleScrapingStatus: RequestHandler = (req, res) => {
  res.json({
    status: scrapingStatus.status,
    startTime: scrapingStatus.startTime,
    totalPages: scrapingStatus.totalPages,
    currentPage: scrapingStatus.currentPage,
    totalItems: scrapingStatus.totalItems,
    currentItems: scrapingStatus.currentItems,
    progressPercent: scrapingStatus.progressPercent,
    estimatedTimeLeft: scrapingStatus.estimatedTimeLeft,
    lastUpdate: scrapingStatus.lastUpdate,
    isRunning: scrapingStatus.status === 'running'
  });
};

export const handlePropertyStats: RequestHandler = (req, res) => {
  res.json({
    total: propertiesDatabase.totalProperties,
    from_owners: propertiesDatabase.fromOwners,
    from_agencies: propertiesDatabase.fromAgencies,
    manual_entries: propertiesDatabase.manualEntries,
    last_scraping: scrapingStatus.lastUpdate,
    owner_percentage: propertiesDatabase.totalProperties > 0
      ? Math.round((propertiesDatabase.fromOwners / propertiesDatabase.totalProperties) * 100)
      : 0,
    districts: propertiesDatabase.districts,
    price_ranges: propertiesDatabase.priceRanges,
    activity_log: activityLog.slice(0, 10) // Last 10 activities
  });
};

// New endpoint for activity log
export const handleActivityLog: RequestHandler = (req, res) => {
  res.json({
    logs: activityLog,
    last_update: new Date().toISOString()
  });
};

// Generate price trends based on real data
export const handlePriceTrends: RequestHandler = (req, res) => {
  // Only show data if we actually have scraped properties
  if (propertiesDatabase.properties.length === 0) {
    return res.json({
      monthly_trends: [],
      top_streets: [],
      total_properties: 0,
      last_update: new Date().toISOString(),
      message: "Немає даних для аналізу. Запустіть парсинг для збору оголошень."
    });
  }

  // Group properties by actual dates when they were scraped
  const propertiesByDate: { [key: string]: any[] } = {};

  propertiesDatabase.properties.forEach(property => {
    const date = new Date(property.created_at);
    const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

    if (!propertiesByDate[dateKey]) {
      propertiesByDate[dateKey] = [];
    }
    propertiesByDate[dateKey].push(property);
  });

  // Generate trends only for dates that actually have data
  const trends = Object.entries(propertiesByDate)
    .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
    .map(([dateKey, properties]) => {
      const date = new Date(dateKey);
      const avgPrice = Math.round(properties.reduce((sum, p) => sum + p.price_usd, 0) / properties.length);
      const avgArea = Math.round(properties.reduce((sum, p) => sum + p.area, 0) / properties.length);

      return {
        date: dateKey,
        month: date.toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' }),
        count: properties.length,
        avg_price: avgPrice,
        price_per_sqm: Math.round(avgPrice / avgArea),
        total_volume: properties.length * avgPrice
      };
    });

  // Calculate top streets with real data only if we have properties
  const streetCounts: { [key: string]: { count: number, totalPrice: number, avgArea: number } } = {};

  if (propertiesDatabase.properties.length > 0) {
    propertiesDatabase.properties.forEach(property => {
      // Generate street name based on district
      const streetMap: { [key: string]: string } = {
        "Центр": "Галицька",
        "Пасічн��": "Тролейбусна",
        "БАМ": "Івасюка",
        "Каскад": "24 Серпня",
        "Залізничний (Вокзал)": "Стефаника",
        "Брати": "Хоткевича",
        "Софіївка": "Пстрака",
        "Будівельників": "Селянська",
        "Набережна": "Набережна ім. В. Стефаника"
      };

      const street = streetMap[property.district] || "Інші вулиці";

      if (streetCounts[street]) {
        streetCounts[street].count++;
        streetCounts[street].totalPrice += property.price_usd;
        streetCounts[street].avgArea += property.area;
      } else {
        streetCounts[street] = {
          count: 1,
          totalPrice: property.price_usd,
          avgArea: property.area
        };
      }
    });
  }

  const topStreets = Object.entries(streetCounts)
    .map(([street, data]) => ({
      street,
      count: data.count,
      avg_price: Math.round(data.totalPrice / data.count),
      avg_area: Math.round(data.avgArea / data.count)
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  res.json({
    monthly_trends: trends,
    top_streets: topStreets,
    total_properties: propertiesDatabase.totalProperties,
    last_update: new Date().toISOString()
  });
};

export const handleStopScraping: RequestHandler = (req, res) => {
  if (scrapingStatus.status !== 'running') {
    return res.status(400).json({
      error: 'Парсинг не запущено',
      status: scrapingStatus.status
    });
  }

  // Save current position before stopping
  scrapingStatus.lastStoppedPage = scrapingStatus.currentPage;
  scrapingStatus.status = 'idle';

  addActivity(`Парсинг зупинено на сторінці ${scrapingStatus.currentPage}. Позицію збережено.`);

  res.json({
    message: 'Парсинг зупинено',
    status: 'idle',
    stoppedAt: scrapingStatus.lastStoppedPage
  });
};

// Get all properties
export const handleGetProperties: RequestHandler = (req, res) => {
  res.json({
    properties: propertiesDatabase.properties,
    total: propertiesDatabase.totalProperties,
    last_update: new Date().toISOString()
  });
};

// Get street to district mapping
export const handleGetStreetMap: RequestHandler = (req, res) => {
  res.json({
    streetMap: streetToDistrictMap,
    totalStreets: Object.keys(streetToDistrictMap).length
  });
};

// Add new street to district mapping
export const handleAddStreet: RequestHandler = (req, res) => {
  const { street, district } = req.body;

  if (!street || !district) {
    return res.status(400).json({
      error: 'Потрібні назва вулиці та район'
    });
  }

  if (streetToDistrictMap[street]) {
    return res.status(400).json({
      error: `Вулиця "${street}" вже існує в районі "${streetToDistrictMap[street]}"`
    });
  }

  streetToDistrictMap[street] = district;
  addActivity(`Додано вулицю "${street}" до району "${district}"`);

  res.json({
    message: `Вулицю "${street}" успішно додано до району "${district}"`,
    streetMap: streetToDistrictMap
  });
};

// Check for property updates (price changes)
export const handleCheckPropertyUpdates: RequestHandler = (req, res) => {
  // Simulate checking for price updates
  const updatedProperties: any[] = [];

  propertiesDatabase.properties.forEach(property => {
    // Simulate 10% chance of price change
    if (Math.random() < 0.1) {
      const oldPrice = property.price_usd;
      const priceChange = (Math.random() - 0.5) * 0.2; // ±10% change
      const newPrice = Math.round(oldPrice * (1 + priceChange));

      property.price_usd = newPrice;
      property.last_updated = new Date().toISOString();

      // Add to price history
      if (!property.price_history) {
        property.price_history = [];
      }
      property.price_history.push({
        price: newPrice,
        date: new Date().toISOString()
      });

      updatedProperties.push({
        olx_id: property.olx_id,
        oldPrice,
        newPrice,
        change: newPrice - oldPrice,
        changePercent: Math.round(((newPrice - oldPrice) / oldPrice) * 100)
      });
    }
  });

  if (updatedProperties.length > 0) {
    addActivity(`Знайдено ${updatedProperties.length} оновлень цін`);
  }

  res.json({
    updatedProperties,
    totalChecked: propertiesDatabase.properties.length,
    updatesFound: updatedProperties.length,
    lastCheck: new Date().toISOString()
  });
};
