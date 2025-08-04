import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Building, 
  ArrowLeft, 
  Database, 
  Trash2, 
  Download, 
  Upload, 
  Settings, 
  Activity,
  AlertCircle,
  CheckCircle,
  Clock
} from "lucide-react";

export default function Admin() {
  const [stats, setStats] = useState({
    totalProperties: 0,
    fromOwners: 0,
    fromAgencies: 0,
    manualEntries: 0,
    lastScraping: null
  });

  const [scrapingStatus, setScrapingStatus] = useState("idle");
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    loadStats();
    loadScrapingStatus();
  }, []);

  const loadStats = async () => {
    try {
      const response = await fetch('/api/property-stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadScrapingStatus = async () => {
    try {
      const response = await fetch('/api/scraping-status');
      const data = await response.json();
      setScrapingStatus(data.status);
    } catch (error) {
      console.error('Failed to load scraping status:', error);
    }
  };

  const handleManualPropertyAdd = async () => {
    const propertyData = {
      title: "Тестове оголошення",
      price_usd: 50000,
      area: 60,
      floor: 3,
      district: "Центр",
      description: "Тестовий опис для налагодження",
      isOwner: true,
      url: "manual_entry",
      olx_id: `manual_${Date.now()}`
    };

    try {
      const response = await fetch('/api/manual-property/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(propertyData)
      });
      
      if (response.ok) {
        alert('Тестове оголошення додано!');
        loadStats();
      }
    } catch (error) {
      console.error('Failed to add manual property:', error);
      alert('Помилка додавання');
    }
  };

  const handleDeleteManualProperties = async () => {
    if (!confirm('Видалити всі ручно додані оголошення?')) return;

    try {
      const response = await fetch('/api/manual-property/delete-manual-properties', {
        method: 'DELETE'
      });
      
      if (response.ok) {
        alert('Ручні оголошення видалено!');
        loadStats();
      }
    } catch (error) {
      console.error('Failed to delete manual properties:', error);
      alert('Помилка видалення');
    }
  };

  const handleExportData = async () => {
    try {
      const response = await fetch('/api/export-properties');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `properties_export_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Помилка експорту');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link to="/" className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                  <Building className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900">Glow Nest</h1>
                  <p className="text-sm text-slate-600">Адмін панель</p>
                </div>
              </Link>
            </div>
            <Button variant="outline" asChild>
              <Link to="/">
                <ArrowLeft className="w-4 h-4 mr-2" />
                На головну
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Dashboard Overview */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Панель адміністратора</h1>
          <p className="text-slate-600">Управління парсингом, моделями та базою даних</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Database className="w-5 h-5 mr-2 text-blue-600" />
                Всього оголошень
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats.totalProperties}</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                Від власників
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{stats.fromOwners}</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Building className="w-5 h-5 mr-2 text-orange-600" />
                Від агентств
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">{stats.fromAgencies}</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Settings className="w-5 h-5 mr-2 text-purple-600" />
                Ручні записи
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{stats.manualEntries}</div>
            </CardContent>
          </Card>
        </div>

        {/* Control Panels */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Scraping Controls */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Activity className="w-6 h-6 mr-3 text-green-600" />
                Управління парсингом
              </CardTitle>
              <CardDescription>
                Контроль збору даних з OLX
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  scrapingStatus === 'running' ? 'bg-green-500 animate-pulse' : 
                  scrapingStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
                }`}></div>
                <span className="text-sm text-slate-600">
                  Статус: {scrapingStatus === 'running' ? 'Активний' : 
                           scrapingStatus === 'error' ? 'Помилка' : 'Неактивний'}
                </span>
              </div>

              <div className="space-y-3">
                <Button 
                  className="w-full bg-green-600 hover:bg-green-700"
                  onClick={async () => {
                    try {
                      const response = await fetch('/api/start-scraping', { method: 'POST' });
                      if (response.ok) {
                        setScrapingStatus('running');
                        alert('Парсинг розпочато!');
                      }
                    } catch (error) {
                      console.error('Scraping error:', error);
                    }
                  }}
                >
                  <Activity className="w-4 h-4 mr-2" />
                  Запустити повний парсинг
                </Button>

                <div className="grid grid-cols-2 gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={loadScrapingStatus}
                  >
                    <Clock className="w-4 h-4 mr-1" />
                    Статус
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      fetch('/api/stop-scraping', { method: 'POST' })
                        .then(() => setScrapingStatus('idle'));
                    }}
                  >
                    <AlertCircle className="w-4 h-4 mr-1" />
                    Зупинити
                  </Button>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <h4 className="text-sm font-medium text-slate-900 mb-1">Налаштування:</h4>
                <ul className="text-xs text-slate-600 space-y-1">
                  <li>• Максимум 10 сторінок за запуск</li>
                  <li>• Затримка 4-8 секунд між запитами</li>
                  <li>• Лише USD валюта</li>
                  <li>• Антибан захист активний</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Database Management */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Database className="w-6 h-6 mr-3 text-blue-600" />
                Управління базою даних
              </CardTitle>
              <CardDescription>
                Операції з даними та резервними копіями
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  onClick={handleManualPropertyAdd}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Додати тестове оголошення
                </Button>

                <div className="grid grid-cols-2 gap-2">
                  <Button 
                    variant="outline"
                    onClick={handleExportData}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Експорт
                  </Button>
                  <Button 
                    variant="destructive"
                    onClick={handleDeleteManualProperties}
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Очистити
                  </Button>
                </div>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-medium text-slate-900 mb-2">Швидкі дії:</h4>
                <div className="space-y-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => window.open('/statistics', '_blank')}
                  >
                    Детальна статистика
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={loadStats}
                  >
                    Оновити дані
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Model Training Controls */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Activity className="w-6 h-6 mr-3 text-purple-600" />
                Навчання моделей
              </CardTitle>
              <CardDescription>
                Перетренування ML-моделей на нових даних
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-3 bg-purple-50 rounded-lg">
                <h4 className="text-sm font-medium text-slate-900 mb-2">Доступні моделі:</h4>
                <ul className="text-xs text-slate-600 space-y-1">
                  <li>• XGBoost (Python)</li>
                  <li>• Real Data Model (TS)</li>
                  <li>• Advanced Model (TS)</li>
                  <li>• Поліноміальна регресія</li>
                </ul>
              </div>

              <div className="space-y-3">
                <Button
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  onClick={async () => {
                    try {
                      const response = await fetch('/api/retrain-model', { method: 'POST' });
                      const data = await response.json();
                      if (response.ok) {
                        alert(`✅ ${data.message}\nОчікуваний час: ${data.estimatedTime}`);
                      }
                    } catch (error) {
                      console.error('Retrain error:', error);
                      alert('❌ Помилка запуску навчання');
                    }
                  }}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Перетренувати основну модель
                </Button>

                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/retrain-advanced-model', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                          alert(`✅ ${data.message}\nОчікуваний час: ${data.estimatedTime}`);
                        }
                      } catch (error) {
                        console.error('Advanced retrain error:', error);
                        alert('❌ Помилка запуску розширеного навчання');
                      }
                    }}
                  >
                    Розширена модель
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/model-comparison');
                        const data = await response.json();
                        alert(`Порівняння моделей:\nНайкраща: ${data.bestModel}\nДата: ${new Date(data.comparisonDate).toLocaleDateString('uk-UA')}`);
                      } catch (error) {
                        console.error('Comparison error:', error);
                        alert('❌ Помилка порівняння моделей');
                      }
                    }}
                  >
                    Порівняти моделі
                  </Button>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <h4 className="text-sm font-medium text-slate-900 mb-1">Стан моделей:</h4>
                <div className="space-y-1 text-xs text-slate-600">
                  <div>• Основна модель: Готова</div>
                  <div>• Розширена модель: Готова</div>
                  <div>• XGBoost: Готова</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Logs Section */}
        <Card className="border-0 shadow-xl mt-8">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <Activity className="w-6 h-6 mr-3 text-purple-600" />
              Журнал подій
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm h-48 overflow-y-auto">
              <div>[{new Date().toLocaleTimeString()}] Адмін панель завантажена</div>
              <div>[{new Date().toLocaleTimeString()}] Статистика оновлена</div>
              <div>[{new Date().toLocaleTimeString()}] Система готова до роботи</div>
              {logs.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
