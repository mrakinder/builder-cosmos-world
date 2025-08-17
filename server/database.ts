import Database from 'better-sqlite3';
import type { Database as BetterSqlite3Database } from 'better-sqlite3';
import { join } from 'path';

// Initialize SQLite database lazily
let db: BetterSqlite3Database | null = null;

export const getDatabase = () => {
  if (!db) {
    const dbPath = process.env.DB_PATH || join(process.cwd(), 'glow_nest.db');
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
  }
  return db;
};

// Create tables if they don't exist
export const initializeDatabase = () => {
  const database = getDatabase();
  
  // Properties table
  database.exec(`
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
  database.exec(`
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
  database.exec(`
    CREATE TABLE IF NOT EXISTS street_districts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      street TEXT UNIQUE NOT NULL,
      district TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Scraping state table
  database.exec(`
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
  database.exec(`
    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      message TEXT NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      type TEXT DEFAULT 'info'
    )
  `);

  // Initialize default street mappings if empty
  const streetCount = database.prepare('SELECT COUNT(*) as count FROM street_districts').get() as { count: number };
  
  if (streetCount.count === 0) {
    const insertStreet = database.prepare('INSERT INTO street_districts (street, district) VALUES (?, ?)');
    
    const defaultStreets = [
      // Center
      ["Галицька", "Центр"],
      ["Незалежності", "Центр"],
      ["Г��ушевського", "Центр"],
      ["Січових Стрільців", "Центр"],
      ["Шевченка", "Центр"],
      ["Леся Курбаса", "Центр"],
      
      // Pasichna
      ["Тролейбусна", "Пасічна"],
      ["Пасічна", "П��січна"],
      ["Чорновола", "Пасічна"],
      
      // BAM
      ["Івасюка", "БАМ"],
      ["Надрічна", "БАМ"],
      ["Вовчинецька", "БАМ"],
      
      // Kaskad
      ["24 Серпня", "Каскад"],
      ["Каскадна", "Кас��ад"],
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
      ["Набережна ім. В. Ст��фаника", "Набережна"],
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
  const stateCount = database.prepare('SELECT COUNT(*) as count FROM scraping_state').get() as { count: number };
  if (stateCount.count === 0) {
    database.prepare('INSERT INTO scraping_state (id, status) VALUES (1, ?)').run('idle');
  }
};

// Database operations with lazy initialization
export const dbOperations = {
  // Properties
  get insertProperty() {
    return getDatabase().prepare(`
      INSERT OR REPLACE INTO properties
      (olx_id, title, price_usd, area, rooms, floor, street, district, description, is_owner, url, last_updated)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `);
  },

  get checkPropertyExists() {
    return getDatabase().prepare(`
      SELECT COUNT(*) as count FROM properties
      WHERE title = ? AND area = ? AND street = ? AND price_usd = ?
    `);
  },
  
  get getAllProperties() {
    return getDatabase().prepare('SELECT * FROM properties WHERE is_active = 1 ORDER BY created_at DESC');
  },
  
  get getPropertyByOlxId() {
    return getDatabase().prepare('SELECT * FROM properties WHERE olx_id = ? AND is_active = 1');
  },
  
  get updatePropertyPrice() {
    return getDatabase().prepare(`
      UPDATE properties 
      SET price_usd = ?, last_updated = datetime('now') 
      WHERE olx_id = ?
    `);
  },
  
  // Price history
  get insertPriceHistory() {
    return getDatabase().prepare(`
      INSERT INTO price_history (property_id, olx_id, price_usd)
      VALUES (?, ?, ?)
    `);
  },
  
  // Street districts
  get getAllStreetDistricts() {
    return getDatabase().prepare('SELECT * FROM street_districts ORDER BY district, street');
  },
  
  get insertStreetDistrict() {
    return getDatabase().prepare(`
      INSERT INTO street_districts (street, district) VALUES (?, ?)
    `);
  },
  
  get getDistrictByStreet() {
    return getDatabase().prepare('SELECT district FROM street_districts WHERE street = ?');
  },
  
  // Scraping state
  get getScrapingState() {
    return getDatabase().prepare('SELECT * FROM scraping_state WHERE id = 1');
  },
  
  get updateScrapingState() {
    return getDatabase().prepare(`
      UPDATE scraping_state 
      SET last_page = ?, last_url = ?, last_processed_id = ?, total_processed = ?, last_run = datetime('now'), status = ?
      WHERE id = 1
    `);
  },
  
  // Activity log
  get insertActivity() {
    return getDatabase().prepare(`
      INSERT INTO activity_log (message, type) VALUES (?, ?)
    `);
  },
  
  get getRecentActivities() {
    return getDatabase().prepare('SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?');
  },
  
  // Statistics
  get getPropertyStats() {
    return getDatabase().prepare(`
      SELECT 
        COUNT(*) as total_properties,
        SUM(CASE WHEN is_owner = 1 THEN 1 ELSE 0 END) as from_owners,
        SUM(CASE WHEN is_owner = 0 THEN 1 ELSE 0 END) as from_agencies,
        AVG(price_usd) as avg_price,
        MAX(last_updated) as last_update
      FROM properties 
      WHERE is_active = 1
    `);
  },
  
  get getDistrictStats() {
    return getDatabase().prepare(`
      SELECT 
        district,
        COUNT(*) as count,
        AVG(price_usd) as avg_price,
        AVG(area) as avg_area
      FROM properties 
      WHERE is_active = 1 
      GROUP BY district 
      ORDER BY count DESC
    `);
  }
};

export default getDatabase;
