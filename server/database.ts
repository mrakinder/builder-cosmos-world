import Database from 'better-sqlite3';
import { join } from 'path';

// Initialize SQLite database
const dbPath = join(process.cwd(), 'glow_nest.db');
const db = new Database(dbPath);

// Enable WAL mode for better performance
db.pragma('journal_mode = WAL');

// Create tables if they don't exist
export const initializeDatabase = () => {
  // Properties table
  db.exec(`
    CREATE TABLE IF NOT EXISTS properties (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      olx_id TEXT UNIQUE NOT NULL,
      title TEXT NOT NULL,
      price_usd INTEGER NOT NULL,
      area INTEGER NOT NULL,
      rooms INTEGER,
      floor INTEGER,
      street TEXT,
      district TEXT NOT NULL,
      description TEXT,
      is_owner BOOLEAN NOT NULL DEFAULT 0,
      url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
      is_active BOOLEAN DEFAULT 1
    )
  `);

  // Price history table
  db.exec(`
    CREATE TABLE IF NOT EXISTS price_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      property_id INTEGER NOT NULL,
      olx_id TEXT NOT NULL,
      price_usd INTEGER NOT NULL,
      recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (property_id) REFERENCES properties (id)
    )
  `);

  // Street to district mapping table
  db.exec(`
    CREATE TABLE IF NOT EXISTS street_districts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      street TEXT UNIQUE NOT NULL,
      district TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Scraping state table
  db.exec(`
    CREATE TABLE IF NOT EXISTS scraping_state (
      id INTEGER PRIMARY KEY,
      last_page INTEGER DEFAULT 0,
      last_url TEXT,
      last_processed_id TEXT,
      total_processed INTEGER DEFAULT 0,
      last_run DATETIME,
      status TEXT DEFAULT 'idle'
    )
  `);

  // Activity log table
  db.exec(`
    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      message TEXT NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      type TEXT DEFAULT 'info'
    )
  `);

  // Initialize default street mappings if empty
  const streetCount = db.prepare('SELECT COUNT(*) as count FROM street_districts').get() as { count: number };
  
  if (streetCount.count === 0) {
    const insertStreet = db.prepare('INSERT INTO street_districts (street, district) VALUES (?, ?)');
    
    const defaultStreets = [
      // Center
      ["Галицька", "Центр"],
      ["Незалежності", "Центр"],
      ["Грушевського", "Центр"],
      ["Січових Стрільців", "Центр"],
      ["Шевченка", "Центр"],
      ["Леся Курбаса", "Центр"],
      
      // Pasichna
      ["Тролейбусна", "Пасічна"],
      ["Пасічна", "Пасічна"],
      ["Чорновола", "Пасічна"],
      
      // BAM
      ["Івасюка", "БАМ"],
      ["Надрічна", "БАМ"],
      ["Вовчинецька", "БАМ"],
      
      // Kaskad
      ["24 Серпня", "Каскад"],
      ["Каскадна", "Каскад"],
      ["Короля Данила", "Каскад"],
      
      // Railway (Vokzal)
      ["Стефаника", "Залізничний (Вокзал)"],
      ["Привокзальна", "Залізничний (Вокзал)"],
      ["Залізнична", "Залізничний (Вокзал)"],
      
      // Braty
      ["Хоткевича", "Брати"],
      ["Миколайчука", "Брати"],
      ["Довга", "Брати"],
      
      // Sofiyivka
      ["Пстрака", "Софіївка"],
      ["Софійська", "Софіївка"],
      ["Левицького", "Софіївка"],
      
      // Budivelnikiv
      ["Селянська", "Будівельників"],
      ["Будівельників", "Будівельників"],
      ["Промислова", "Будівельників"],
      
      // Naberezhna
      ["Набережна ім. В. Стефаника", "Набережна"],
      ["Набережна", "Набережна"],
      ["Дністровська", "Набережна"],
      
      // Opryshivtsi
      ["Опришівська", "Опришівці"],
      ["Гуцульська", "Опришівці"],
      ["Карпатська", "Опришівці"]
    ];

    defaultStreets.forEach(([street, district]) => {
      insertStreet.run(street, district);
    });
  }

  // Initialize scraping state if empty
  const stateCount = db.prepare('SELECT COUNT(*) as count FROM scraping_state').get() as { count: number };
  if (stateCount.count === 0) {
    db.prepare('INSERT INTO scraping_state (id, status) VALUES (1, ?)').run('idle');
  }
};

// Database operations
export const dbOperations = {
  // Properties
  insertProperty: db.prepare(`
    INSERT OR REPLACE INTO properties 
    (olx_id, title, price_usd, area, rooms, floor, street, district, description, is_owner, url, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `),
  
  getAllProperties: db.prepare('SELECT * FROM properties WHERE is_active = 1 ORDER BY created_at DESC'),
  
  getPropertyByOlxId: db.prepare('SELECT * FROM properties WHERE olx_id = ? AND is_active = 1'),
  
  updatePropertyPrice: db.prepare(`
    UPDATE properties 
    SET price_usd = ?, last_updated = datetime('now') 
    WHERE olx_id = ?
  `),
  
  // Price history
  insertPriceHistory: db.prepare(`
    INSERT INTO price_history (property_id, olx_id, price_usd)
    VALUES (?, ?, ?)
  `),
  
  // Street districts
  getAllStreetDistricts: db.prepare('SELECT * FROM street_districts ORDER BY district, street'),
  
  insertStreetDistrict: db.prepare(`
    INSERT INTO street_districts (street, district) VALUES (?, ?)
  `),
  
  getDistrictByStreet: db.prepare('SELECT district FROM street_districts WHERE street = ?'),
  
  // Scraping state
  getScrapingState: db.prepare('SELECT * FROM scraping_state WHERE id = 1'),
  
  updateScrapingState: db.prepare(`
    UPDATE scraping_state 
    SET last_page = ?, last_url = ?, last_processed_id = ?, total_processed = ?, last_run = datetime('now'), status = ?
    WHERE id = 1
  `),
  
  // Activity log
  insertActivity: db.prepare(`
    INSERT INTO activity_log (message, type) VALUES (?, ?)
  `),
  
  getRecentActivities: db.prepare('SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?'),
  
  // Statistics
  getPropertyStats: db.prepare(`
    SELECT 
      COUNT(*) as total_properties,
      SUM(CASE WHEN is_owner = 1 THEN 1 ELSE 0 END) as from_owners,
      SUM(CASE WHEN is_owner = 0 THEN 1 ELSE 0 END) as from_agencies,
      AVG(price_usd) as avg_price,
      MAX(last_updated) as last_update
    FROM properties 
    WHERE is_active = 1
  `),
  
  getDistrictStats: db.prepare(`
    SELECT 
      district,
      COUNT(*) as count,
      AVG(price_usd) as avg_price,
      AVG(area) as avg_area
    FROM properties 
    WHERE is_active = 1 
    GROUP BY district 
    ORDER BY count DESC
  `)
};

export default db;
