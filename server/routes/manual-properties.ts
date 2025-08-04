import { RequestHandler } from "express";

// Mock manual properties storage
let manualProperties: any[] = [];

export const handleAddManualProperty: RequestHandler = (req, res) => {
  const propertyData = {
    id: Date.now(),
    olx_id: `manual_${Date.now()}`,
    title: req.body.title || "Тестове оголошення",
    price_usd: req.body.price_usd || 50000,
    area: req.body.area || 60,
    floor: req.body.floor || 3,
    district: req.body.district || "Центр",
    description: req.body.description || "Тестовий опис для налагодження",
    isOwner: req.body.isOwner ?? true,
    url: req.body.url || "manual_entry",
    created_at: new Date().toISOString(),
    timestamp: Date.now()
  };

  manualProperties.push(propertyData);

  res.json({ 
    message: 'Оголошення додано успішно', 
    property: propertyData,
    total_manual: manualProperties.length
  });
};

export const handleManualPropertyStats: RequestHandler = (req, res) => {
  const totalManual = manualProperties.length;
  const totalAll = 150 + totalManual; // Assume 150 scraped properties
  const manualPercentage = totalAll > 0 ? Math.round((totalManual / totalAll) * 100) : 0;

  res.json({
    total_manual: totalManual,
    total_all: totalAll,
    manual_percentage: manualPercentage,
    last_added: manualProperties.length > 0 
      ? manualProperties[manualProperties.length - 1].created_at 
      : null
  });
};

export const handleDeleteManualProperties: RequestHandler = (req, res) => {
  const deletedCount = manualProperties.length;
  manualProperties = [];

  res.json({ 
    message: `Видалено ${deletedCount} ручних оголошень`, 
    deleted_count: deletedCount,
    remaining: manualProperties.length
  });
};

export const handleExportProperties: RequestHandler = (req, res) => {
  const exportData = {
    export_date: new Date().toISOString(),
    total_properties: 150 + manualProperties.length,
    manual_properties: manualProperties,
    scraped_properties_count: 150,
    statistics: {
      from_owners: 90,
      from_agencies: 60,
      manual_entries: manualProperties.length
    }
  };

  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', `attachment; filename=properties_export_${new Date().toISOString().split('T')[0]}.json`);
  res.json(exportData);
};
