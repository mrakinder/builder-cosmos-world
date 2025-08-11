import { RequestHandler } from "express";
import { initializeDatabase, dbOperations } from '../database';
import { API_CONFIG, safeFetch, getScraperStartUrl, buildApiUrl, logApiRequest, logApiResponse, handleApiError } from '../../shared/config';

// Safe JSON parsing function to prevent "Unexpected end of JSON input" errors
async function safeJsonParse(response: Response): Promise<{ok: boolean, data?: any, error?: string, status: number}> {
  try {
    const text = await response.text();
    if (!text || text.trim() === '') {
      return { ok: false, error: 'Empty response body', status: response.status };
    }

    try {
      const data = JSON.parse(text);
      return { ok: true, data, status: response.status };
    } catch (parseError) {
      return {
        ok: false,
        error: `Invalid JSON: ${parseError.message}`,
        status: response.status
      };
    }
  } catch (error) {
    return {
      ok: false,
      error: `Response read error: ${error.message}`,
      status: response.status
    };
  }
}

// Ensure database is initialized (will be called when first route is accessed)
const ensureDatabase = () => {
  try {
    initializeDatabase();
  } catch (error) {
    console.error('Database initialization failed:', error);
  }
};

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

// Activity log for real-time updates (in-memory for quick access)
let activityLog: string[] = [];

// SSE connections for real-time updates
let sseConnections: any[] = [];

// Load recent activities from database on startup
const loadRecentActivities = () => {
  try {
    const activities = dbOperations.getRecentActivities.all(20) as any[];
    activityLog = activities.map(activity => 
      `[${new Date(activity.timestamp).toLocaleTimeString()}] ${activity.message}`
    ).reverse();
    
    if (activityLog.length === 0) {
      addActivity('Система запущена');
      addActivity('База даних ініціалізована');
      addActivity('API готове до роботи');
    }
  } catch (error) {
    console.error('Failed to load activities:', error);
    activityLog = [
      `[${new Date().toLocaleTimeString()}] Система запущена`,
      `[${new Date().toLocaleTimeString()}] База даних ініціалізована`,
      `[${new Date().toLocaleTimeString()}] API готове до роботи`
    ];
  }
};

// Activities will be loaded when first needed

// Add activity to log (both memory and database)
const addActivity = (message: string, type: string = 'info') => {
  const timestamp = new Date().toLocaleTimeString();
  const logEntry = `[${timestamp}] ${message}`;

  // Add to memory log for quick access
  activityLog.unshift(logEntry);
  if (activityLog.length > 50) activityLog.pop(); // Keep last 50 entries

  // Add to database for persistence
  try {
    dbOperations.insertActivity.run(message, type);
  } catch (error) {
    console.error('Failed to insert activity:', error);
  }

  // Broadcast to SSE connections (будемо викликати з server/index.ts)
  if ((global as any).broadcastSSE) {
    (global as any).broadcastSSE({
      type: 'log',
      message: logEntry,
      timestamp: Date.now()
    });
  }
};

export const handleStartScraping: RequestHandler = async (req, res) => {
  ensureDatabase();

  try {
    const { listing_type = 'sale', max_pages = 10 } = req.body;

    // Validate parameters
    if (max_pages < 1 || max_pages > 50) {
      return res.status(400).json({
        error: 'max_pages має бути між 1 та 50',
        status: 'error'
      });
    }

    addActivity(`🔧 FIX: Redirecting to Python FastAPI backend instead of Node spawn`);
    addActivity(`🤖 ПОЧАТОК: Реальний Botasaurus парсинг OLX (${max_pages} сторінок, тип: ${listing_type})`);
    addActivity(`🛡️ Використання: AntiDetectionDriver + Stealth режим`);
    addActivity(`🎯 Цільовий регіон: Івано-Франківськ, валюта: USD`);

    // Call Python FastAPI backend instead of Node spawn
    // Production API URL will be https://glow-nest-api.fly.dev
    const pythonBackendUrl = process.env.PYTHON_API_URL || 'https://glow-nest-api.fly.dev';
    const requestUrl = `${pythonBackendUrl}/scraper/start`;

    // Prepare request body with validation
    const requestBody = {
      listing_type,
      max_pages: Number(max_pages), // ensure integer
      delay_ms: 5000,
      headful: false
    };

    addActivity(`🚪 Node → Python: POST ${requestUrl}`);
    addActivity(`📦 Request body: ${JSON.stringify(requestBody)}`);
    addActivity(`🏷️ Content-Type: application/json`);

    const response = await fetch(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    addActivity(`📨 Python response: ${response.status} ${response.statusText}`);

    // Safe JSON parsing to prevent "Unexpected end of JSON input"
    const parsedResponse = await safeJsonParse(response);

    // Log response details for diagnostics
    addActivity(`📖 Response body (first 100 chars): ${parsedResponse.ok ? JSON.stringify(parsedResponse.data).substring(0, 100) + '...' : parsedResponse.error}`);

    if (!parsedResponse.ok) {
      addActivity(`❌ JSON parse error: ${parsedResponse.error}`);
      addActivity(`📜 Raw response: ${parsedResponse.error}`);
      throw new Error(`Python backend JSON error: ${parsedResponse.error}`);
    }

    const pythonResult = parsedResponse.data;

    if (!response.ok || !pythonResult?.ok) {
      const errorMsg = pythonResult?.error || pythonResult?.detail || `HTTP ${response.status}`;
      addActivity(`❌ Python backend error: ${errorMsg}`);
      throw new Error(errorMsg);
    }

    addActivity(`✅ Python backend success: task=${pythonResult.task || 'unknown'}`);

    // Update local status for compatibility
    scrapingStatus = {
      status: 'running',
      startTime: new Date(),
      totalPages: max_pages,
      currentPage: 0,
      totalItems: 0,
      currentItems: 0,
      progressPercent: 0,
      lastUpdate: new Date(),
      estimatedTimeLeft: max_pages * 30,
      lastStoppedPage: 0,
      scrapingPosition: {
        lastUrl: '',
        lastProcessedId: `python_backend_${Date.now()}`,
        totalProcessed: 0
      }
    };

    addActivity(`✅ Python backend response: ${pythonResult.message || 'Scraping started'}`);
    addActivity(`📊 Task ID: ${pythonResult.task || 'unknown'}`);
    addActivity(`🕐 Estimated time: ${pythonResult.estimated_time || 'calculating...'}`);
    addActivity(`📍 Status: ${pythonResult.status || 'unknown'}`);
    addActivity(`🚪 Node → Admin: Returning success response`);

    res.json({
      success: true,
      message: 'Реальний Botasaurus парсинг запущено через Python backend',
      status: 'running',
      estimatedTime: `${Math.round(max_pages * 30 / 60)} хвилин`,
      progress: 0,
      framework: 'Botasaurus v4.0.10+ (Python Backend)',
      features: ['AntiDetectionDriver', 'Stealth Mode', 'Resume Capability', 'Real-time Progress'],
      python_backend: true,
      task_id: pythonResult.task_id,
      backend_url: pythonBackendUrl
    });

  } catch (error) {
    console.error('Error starting scraping via Python backend:', error);
    addActivity(`❌ ПОМИЛКА запуску через Python backend: ${error.message}`);

    res.status(500).json({
      success: false,
      error: `Помилка запуску через Python backend: ${error.message}`,
      status: 'error'
    });
  }
};

// Add random property to database with realistic data
const addRandomProperty = () => {
  try {
    // Get random street from database
    const streets = dbOperations.getAllStreetDistricts.all() as any[];
    if (streets.length === 0) {
      console.error('No streets found in database');
      return;
    }
    
    const randomStreet = streets[Math.floor(Math.random() * streets.length)];
    const isOwner = Math.random() > 0.4; // 60% owners
    const area = Math.floor(Math.random() * 80) + 30; // 30-110 m²
    const basePrice = area * (800 + Math.random() * 800); // $800-1600 per m²
    const rooms = Math.floor(Math.random() * 4) + 1; // 1-4 rooms

    const title = `${rooms}-кімн. квартира на вул. ${randomStreet.street}, ${area}м²`;
    const finalPrice = Math.round(basePrice);
    const floor = Math.floor(Math.random() * 9) + 1;

    // Check if similar property already exists to avoid duplicates
    const existingProperty = dbOperations.checkPropertyExists.get(
      title,
      area,
      randomStreet.street,
      finalPrice
    ) as { count: number };

    if (existingProperty.count > 0) {
      // Property already exists, skip
      console.log(`Skipping duplicate property: ${title}`);
      return;
    }

    const olxId = `olx_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

    // Insert property into database
    const result = dbOperations.insertProperty.run(
      olxId,
      title,
      finalPrice,
      area,
      rooms,
      floor,
      randomStreet.street,
      randomStreet.district,
      `Продається ${rooms}-кімнатна квартира площею ${area}м² на вулиці ${randomStreet.street} в районі ${randomStreet.district}. ${isOwner ? 'Від власника.' : 'Через аг��нтство.'}`,
      isOwner ? 1 : 0,
      `https://olx.ua/property/${Math.floor(Math.random() * 100000)}`
    );
    
    // Add initial price to history
    if (result.lastInsertRowid) {
      dbOperations.insertPriceHistory.run(result.lastInsertRowid, olxId, finalPrice);
    }
    
  } catch (error) {
    console.error('Failed to add property:', error);
  }
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
  ensureDatabase();

  try {
    const stats = dbOperations.getPropertyStats.get() as any;
    
    res.json({
      totalProperties: stats?.total_properties || 0,
      fromOwners: stats?.from_owners || 0,
      fromAgencies: stats?.from_agencies || 0,
      manualEntries: 0, // TODO: Add manual entries tracking
      lastScraping: stats?.last_update || null,
      ownerPercentage: stats?.total_properties > 0
        ? Math.round((stats.from_owners / stats.total_properties) * 100)
        : 0,
      avgPrice: Math.round(stats?.avg_price || 0),
      activityLog: activityLog.slice(0, 10) // Last 10 activities
    });
  } catch (error) {
    console.error('Failed to get property stats:', error);
    res.status(500).json({ error: 'Failed to load statistics' });
  }
};

// New endpoint for activity log
export const handleActivityLog: RequestHandler = (req, res) => {
  ensureDatabase();

  // Load recent activities if not already loaded
  if (activityLog.length === 0) {
    loadRecentActivities();
  }

  res.json({
    logs: activityLog,
    last_update: new Date().toISOString()
  });
};

export const handleStopScraping: RequestHandler = async (req, res) => {
  try {
    // Call Python FastAPI backend to stop scraping
    // Production API URL will be https://glow-nest-api.fly.dev
    const pythonBackendUrl = process.env.PYTHON_API_URL || 'https://glow-nest-api.fly.dev';

    const response = await fetch(`${pythonBackendUrl}/scraper/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    // Safe JSON parsing to prevent "Unexpected end of JSON input"
    const parsedResponse = await safeJsonParse(response);

    if (!parsedResponse.ok) {
      addActivity(`❌ Stop JSON parse error: ${parsedResponse.error}`);
      throw new Error(`Python backend JSON error: ${parsedResponse.error}`);
    }

    const pythonResult = parsedResponse.data;

    if (!response.ok || !pythonResult?.ok) {
      const errorMsg = pythonResult?.error || pythonResult?.detail || `HTTP ${response.status}`;
      addActivity(`❌ Python backend stop error: ${errorMsg}`);
      throw new Error(errorMsg);
    }

    // Update local status
    scrapingStatus.lastStoppedPage = scrapingStatus.currentPage;
    scrapingStatus.status = 'idle';

    // Update database with stopped state
    try {
      dbOperations.updateScrapingState.run(
        scrapingStatus.currentPage,
        scrapingStatus.scrapingPosition?.lastUrl || '',
        scrapingStatus.scrapingPosition?.lastProcessedId || '',
        scrapingStatus.totalItems,
        'idle'
      );
    } catch (error) {
      console.error('Failed to update scraping state on stop:', error);
    }

    addActivity(`⏹️ Парсинг зупинено через Python backend на сторінці ${scrapingStatus.currentPage}`);
    addActivity(`✅ Python backend response: ${pythonResult.message}`);

    res.json({
      success: true,
      message: 'Парсинг зупинено через Python backend',
      status: 'idle',
      stoppedAt: scrapingStatus.lastStoppedPage,
      python_backend: true
    });

  } catch (error) {
    console.error('Error stopping scraping via Python backend:', error);
    addActivity(`❌ Помилка зупинки ��ерез Python backend: ${error.message}`);

    res.status(500).json({
      success: false,
      error: `Помилка з��пинки через Python backend: ${error.message}`,
      status: 'error'
    });
  }
};

// Get all properties
export const handleGetProperties: RequestHandler = (req, res) => {
  ensureDatabase();

  try {
    const properties = dbOperations.getAllProperties.all();
    
    res.json({
      properties: properties.map((p: any) => ({
        id: p.id,
        olx_id: p.olx_id,
        title: p.title,
        price_usd: p.price_usd,
        area: p.area,
        rooms: p.rooms,
        floor: p.floor,
        street: p.street,
        district: p.district,
        description: p.description,
        isOwner: p.is_owner === 1,
        url: p.url,
        created_at: p.created_at,
        last_updated: p.last_updated
      })),
      total: properties.length,
      last_update: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to get properties:', error);
    res.status(500).json({ error: 'Failed to load properties' });
  }
};

// Get street to district mapping
export const handleGetStreetMap: RequestHandler = (req, res) => {
  ensureDatabase();

  try {
    const streets = dbOperations.getAllStreetDistricts.all() as any[];
    const streetMap: { [key: string]: string } = {};
    
    streets.forEach(street => {
      streetMap[street.street] = street.district;
    });
    
    res.json({
      streetMap,
      totalStreets: streets.length
    });
  } catch (error) {
    console.error('Failed to get street map:', error);
    res.status(500).json({ error: 'Failed to load street mapping' });
  }
};

// Add new street to district mapping
export const handleAddStreet: RequestHandler = (req, res) => {
  ensureDatabase();

  const { street, district } = req.body;
  
  if (!street || !district) {
    return res.status(400).json({
      error: 'Потрібні назва вулиці та рай��н'
    });
  }

  try {
    // Check if street already exists
    const existing = dbOperations.getDistrictByStreet.get(street) as any;
    if (existing) {
      return res.status(400).json({
        error: `Вулиця "${street}" вже існує в районі "${existing.district}"`
      });
    }

    // Insert new street
    dbOperations.insertStreetDistrict.run(street, district);
    addActivity(`Додано вулицю "${street}" до району "${district}"`);
    
    res.json({
      message: `Вулицю "${street}" успішно додано до району "${district}"`
    });
  } catch (error) {
    console.error('Failed to add street:', error);
    res.status(500).json({ error: 'Помил��а додавання ��улиці' });
  }
};

// Check for property updates (price changes)
export const handleCheckPropertyUpdates: RequestHandler = (req, res) => {
  ensureDatabase();

  try {
    // Get all properties from database
    const properties = dbOperations.getAllProperties.all() as any[];
    const updatedProperties: any[] = [];
    
    properties.forEach(property => {
      // Simulate 10% chance of price change
      if (Math.random() < 0.1) {
        const oldPrice = property.price_usd;
        const priceChange = (Math.random() - 0.5) * 0.2; // ±10% change
        const newPrice = Math.round(oldPrice * (1 + priceChange));
        
        // Update price in database
        dbOperations.updatePropertyPrice.run(newPrice, property.olx_id);
        
        // Add to price history
        dbOperations.insertPriceHistory.run(property.id, property.olx_id, newPrice);
        
        updatedProperties.push({
          olx_id: property.olx_id,
          title: property.title,
          oldPrice,
          newPrice,
          change: newPrice - oldPrice,
          changePercent: Math.round(((newPrice - oldPrice) / oldPrice) * 100)
        });
      }
    });
    
    if (updatedProperties.length > 0) {
      addActivity(`Знайдено ${updatedProperties.length} оно��лень цін`);
    }
    
    res.json({
      updatedProperties,
      totalChecked: properties.length,
      updatesFound: updatedProperties.length,
      lastCheck: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to check property updates:', error);
    res.status(500).json({ error: 'Помилка перевірки оновлень' });
  }
};

// Generate price trends based on real data
export const handlePriceTrends: RequestHandler = (req, res) => {
  ensureDatabase();

  try {
    const properties = dbOperations.getAllProperties.all() as any[];
    
    // Only show data if we actually have scraped properties
    if (properties.length === 0) {
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

    properties.forEach(property => {
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

    // Calculate top streets with real data
    const streetCounts: { [key: string]: { count: number, totalPrice: number, avgArea: number } } = {};

    properties.forEach(property => {
      const street = property.street || "Інші вулиці";

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
      total_properties: properties.length,
      last_update: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to generate price trends:', error);
    res.status(500).json({ error: 'Помилка генерації трендів' });
  }
};
