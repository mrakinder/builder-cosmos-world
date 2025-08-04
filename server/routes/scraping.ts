import { RequestHandler } from "express";

// Mock scraping status storage
let scrapingStatus = {
  status: 'idle', // 'idle', 'running', 'completed', 'error'
  startTime: null as Date | null,
  totalPages: 0,
  totalItems: 0,
  lastUpdate: new Date()
};

// Mock properties database
let mockDatabase = {
  totalProperties: 0,
  fromOwners: 0,
  fromAgencies: 0,
  manualEntries: 0,
  properties: [] as any[]
};

export const handleStartScraping: RequestHandler = (req, res) => {
  if (scrapingStatus.status === 'running') {
    return res.status(400).json({ 
      error: 'Парсинг вже запущено', 
      status: scrapingStatus.status 
    });
  }

  // Start scraping simulation
  scrapingStatus = {
    status: 'running',
    startTime: new Date(),
    totalPages: 0,
    totalItems: 0,
    lastUpdate: new Date()
  };

  // Simulate scraping process
  setTimeout(() => {
    const newItems = Math.floor(Math.random() * 50) + 20; // 20-70 new items
    const newOwners = Math.floor(newItems * 0.6); // 60% owners
    const newAgencies = newItems - newOwners;

    mockDatabase.totalProperties += newItems;
    mockDatabase.fromOwners += newOwners;
    mockDatabase.fromAgencies += newAgencies;

    scrapingStatus = {
      status: 'completed',
      startTime: scrapingStatus.startTime,
      totalPages: Math.floor(Math.random() * 8) + 3, // 3-10 pages
      totalItems: newItems,
      lastUpdate: new Date()
    };

    console.log(`Scraping completed: ${newItems} new properties added`);
  }, 3000); // Complete after 3 seconds

  res.json({ 
    message: 'Парсинг розпочато успішно', 
    status: 'running',
    estimatedTime: '2-5 хвилин'
  });
};

export const handleScrapingStatus: RequestHandler = (req, res) => {
  res.json({
    status: scrapingStatus.status,
    startTime: scrapingStatus.startTime,
    totalPages: scrapingStatus.totalPages,
    totalItems: scrapingStatus.totalItems,
    lastUpdate: scrapingStatus.lastUpdate,
    isRunning: scrapingStatus.status === 'running'
  });
};

export const handlePropertyStats: RequestHandler = (req, res) => {
  res.json({
    total: mockDatabase.totalProperties,
    from_owners: mockDatabase.fromOwners,
    from_agencies: mockDatabase.fromAgencies,
    manual_entries: mockDatabase.manualEntries,
    last_scraping: scrapingStatus.lastUpdate,
    owner_percentage: mockDatabase.totalProperties > 0 
      ? Math.round((mockDatabase.fromOwners / mockDatabase.totalProperties) * 100) 
      : 0
  });
};

export const handleStopScraping: RequestHandler = (req, res) => {
  if (scrapingStatus.status !== 'running') {
    return res.status(400).json({ 
      error: 'Парсинг не запущено', 
      status: scrapingStatus.status 
    });
  }

  scrapingStatus.status = 'idle';
  res.json({ 
    message: 'Парсинг зупинено', 
    status: 'idle' 
  });
};
