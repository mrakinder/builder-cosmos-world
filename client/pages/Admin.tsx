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
  Clock,
  MapPin,
  Plus,
  Eye,
  Edit,
  Save,
  Brain,
  TrendingUp,
  Globe,
  BarChart3,
  Zap
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
  const [scrapingProgress, setScrapingProgress] = useState(0);
  const [modelProgress, setModelProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [activityLogs, setActivityLogs] = useState<string[]>([]);
  const [properties, setProperties] = useState([]);
  const [showProperties, setShowProperties] = useState(false);
  const [showStreetManager, setShowStreetManager] = useState(false);
  const [newStreet, setNewStreet] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [streetToDistrictMap, setStreetToDistrictMap] = useState({});
  const [mlModuleStatus, setMLModuleStatus] = useState({
    ml_trained: false,
    prophet_ready: false,
    streamlit_running: false,
    superset_running: false
  });
  const [showMLControls, setShowMLControls] = useState(false);

  useEffect(() => {
    loadStats();
    loadScrapingStatus();
    loadModelStatus();
    loadActivityLogs();
    loadStreetMap();
    loadMLModuleStatus();

    // Set up real-time monitoring
    const interval = setInterval(() => {
      loadScrapingStatus();
      loadModelStatus();
      loadActivityLogs();
      loadMLModuleStatus();
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
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
      setScrapingProgress(data.progressPercent || 0);
    } catch (error) {
      console.error('Failed to load scraping status:', error);
    }
  };

  const loadModelStatus = async () => {
    try {
      const response = await fetch('/api/model-info');
      const data = await response.json();
      setModelProgress(data.trainingProgress || 0);
    } catch (error) {
      console.error('Failed to load model status:', error);
    }
  };

  const loadActivityLogs = async () => {
    try {
      const response = await fetch('/api/activity-log');
      const data = await response.json();
      setActivityLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to load activity logs:', error);
    }
  };

  const loadProperties = async () => {
    try {
      const response = await fetch('/api/properties');
      const data = await response.json();
      setProperties(data.properties || []);
    } catch (error) {
      console.error('Failed to load properties:', error);
    }
  };

  const loadStreetMap = async () => {
    try {
      const response = await fetch('/api/street-map');
      const data = await response.json();
      setStreetToDistrictMap(data.streetMap || {});
    } catch (error) {
      console.error('Failed to load street map:', error);
    }
  };

  const loadMLModuleStatus = async () => {
    try {
      const response = await fetch('/api/pipeline/status');
      const data = await response.json();
      setMLModuleStatus(data);
    } catch (error) {
      console.error('Failed to load ML module status:', error);
    }
  };

  const handleAddStreet = async () => {
    if (!newStreet.trim() || !selectedDistrict) {
      alert('Будь ласка, введіть назву вулиці та оберіть район');
      return;
    }

    try {
      const response = await fetch('/api/add-street', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          street: newStreet.trim(),
          district: selectedDistrict
        })
      });

      if (response.ok) {
        alert(`Вулицю "${newStreet}" додано до району "${selectedDistrict}"`);
        setNewStreet('');
        setSelectedDistrict('');
        loadStreetMap();
      }
    } catch (error) {
      console.error('Failed to add street:', error);
      alert('Помилка додавання вулиці');
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
      alert('��омилка додавання');
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
                  <p className="text-sm text-slate-600">Адмін пан��ль</p>
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

        {/* Navigation Buttons */}
        <div className="flex flex-wrap gap-4 mb-8">
          <Button
            variant={showProperties ? "default" : "outline"}
            onClick={() => {
              setShowProperties(!showProperties);
              if (!showProperties) {
                loadProperties();
                setShowStreetManager(false);
              }
            }}
          >
            <Eye className="w-4 h-4 mr-2" />
            {showProperties ? 'Сховати' : 'Переглянути'} оголошення
          </Button>
          <Button
            variant={showStreetManager ? "default" : "outline"}
            onClick={() => {
              setShowStreetManager(!showStreetManager);
              if (!showStreetManager) {
                setShowProperties(false);
              }
            }}
          >
            <MapPin className="w-4 h-4 mr-2" />
            {showStreetManager ? 'Сховати' : 'Управління'} вулицями
          </Button>
          <Button
            variant={showMLControls ? "default" : "outline"}
            onClick={() => {
              setShowMLControls(!showMLControls);
              if (!showMLControls) {
                setShowProperties(false);
                setShowStreetManager(false);
              }
            }}
          >
            <Brain className="w-4 h-4 mr-2" />
            {showMLControls ? 'Сховати' : 'ML Модулі'} (5 систем)
          </Button>
        </div>

        {/* Street Manager */}
        {showStreetManager && (
          <Card className="border-0 shadow-xl mb-8">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <MapPin className="w-6 h-6 mr-3 text-green-600" />
                Управління вулицями та районами
              </CardTitle>
              <CardDescription>
                Додавання нових вулиць до існуючих районів
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      Назва вулиці
                    </label>
                    <Input
                      placeholder="Введіть назву вулиці..."
                      value={newStreet}
                      onChange={(e) => setNewStreet(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      Район
                    </label>
                    <Select value={selectedDistrict} onValueChange={setSelectedDistrict}>
                      <SelectTrigger>
                        <SelectValue placeholder="Оберіть район" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Центр">Центр</SelectItem>
                        <SelectItem value="Пасічна">Пасічна</SelectItem>
                        <SelectItem value="БАМ">БАМ</SelectItem>
                        <SelectItem value="Каскад">Каскад</SelectItem>
                        <SelectItem value="Залізничний (Вокзал)">Залізничний (Вокзал)</SelectItem>
                        <SelectItem value="Брати">Брати</SelectItem>
                        <SelectItem value="Софіївка">Софіївка</SelectItem>
                        <SelectItem value="Будівельників">Будівельників</SelectItem>
                        <SelectItem value="Набережна">Набережна</SelectItem>
                        <SelectItem value="Опришівці">Опришівці</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={handleAddStreet}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Додати вулицю
                  </Button>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h4 className="font-medium text-slate-900 mb-3">Поточні вулиці:</h4>
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {Object.entries(streetToDistrictMap).map(([street, district]) => (
                      <div key={street} className="flex justify-between items-center p-2 bg-white rounded border text-sm">
                        <span className="font-medium">{street}</span>
                        <span className="text-slate-600 text-xs bg-slate-100 px-2 py-1 rounded">{district}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ML Controls Section */}
        {showMLControls && (
          <div className="space-y-6 mb-8">
            {/* ML System Overview */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Brain className="w-6 h-6 mr-3 text-indigo-600" />
                  Комплексна ML Система (5 модулів)
                </CardTitle>
                <CardDescription>
                  Повнофункціональна система машинного навчання для аналізу нерухомості
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${mlModuleStatus.ml_trained ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                    <h4 className="font-medium text-sm">Botasaurus</h4>
                    <p className="text-xs text-slate-600">Збір даних</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${mlModuleStatus.ml_trained ? 'bg-blue-500' : 'bg-gray-400'}`}></div>
                    <h4 className="font-medium text-sm">LightAutoML</h4>
                    <p className="text-xs text-slate-600">Прогноз цін</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                    <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${mlModuleStatus.prophet_ready ? 'bg-purple-500' : 'bg-gray-400'}`}></div>
                    <h4 className="font-medium text-sm">Prophet</h4>
                    <p className="text-xs text-slate-600">Часові ряди</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg">
                    <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${mlModuleStatus.streamlit_running ? 'bg-orange-500' : 'bg-gray-400'}`}></div>
                    <h4 className="font-medium text-sm">Streamlit</h4>
                    <p className="text-xs text-slate-600">Веб-інтерфейс</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg">
                    <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${mlModuleStatus.superset_running ? 'bg-red-500' : 'bg-gray-400'}`}></div>
                    <h4 className="font-medium text-sm">Superset</h4>
                    <p className="text-xs text-slate-600">Аналітика</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* ML Module Controls */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* LightAutoML Controls */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Brain className="w-5 h-5 mr-2 text-blue-600" />
                    LightAutoML Прогнозування
                  </CardTitle>
                  <CardDescription>
                    Автоматичне ML для прогнозування цін нерухомості
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/ml/train', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                          alert(`✅ ${data.message}\nMAPE: ${data.mape}%`);
                          loadMLModuleStatus();
                        }
                      } catch (error) {
                        alert('❌ Помилка навчання ML моделі');
                      }
                    }}
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Тренувати LightAutoML модель
                  </Button>

                  <div className="p-3 bg-blue-50 rounded-lg text-sm">
                    <p><strong>Ціль:</strong> MAPE ≤ 15%</p>
                    <p><strong>Фічі:</strong> площа, район, кімнати, поверх, тип, ремонт</p>
                    <p><strong>Статус:</strong> {mlModuleStatus.ml_trained ? '✅ Готово' : '⏳ Не тренована'}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Prophet Forecasting */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-purple-600" />
                    Prophet Прогнозування
                  </CardTitle>
                  <CardDescription>
                    Прогноз цінових трендів на 6 місяців по районах
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          const response = await fetch('/api/ml/forecast');
                          const data = await response.json();
                          alert(`✅ Прогноз готовий!\nРайонів: ${data.districts?.length || 0}\nПеріод: 6 місяців`);
                        } catch (error) {
                          alert('❌ Помилка створення прогнозу');
                        }
                      }}
                    >
                      <TrendingUp className="w-4 h-4 mr-1" />
                      Всі райони
                    </Button>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        const district = prompt('Введіть назву району:');
                        if (!district) return;
                        try {
                          const response = await fetch(`/api/ml/forecast?district=${encodeURIComponent(district)}`);
                          const data = await response.json();
                          alert(`✅ Прогноз для "${district}" готовий!`);
                        } catch (error) {
                          alert('❌ Помилка прогнозування району');
                        }
                      }}
                    >
                      <BarChart3 className="w-4 h-4 mr-1" />
                      Один район
                    </Button>
                  </div>

                  <div className="p-3 bg-purple-50 rounded-lg text-sm">
                    <p><strong>Метод:</strong> Facebook Prophet</p>
                    <p><strong>Прогноз:</strong> 6 місяців з довірчими інтервалами</p>
                    <p><strong>Статус:</strong> {mlModuleStatus.prophet_ready ? '✅ Готово' : '⏳ Не готово'}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Streamlit Web Interface */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Globe className="w-5 h-5 mr-2 text-orange-600" />
                    Streamlit Веб-Інтерфейс
                  </CardTitle>
                  <CardDescription>
                    Публічний інтерфейс для оцінки нерухомості
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      className="bg-orange-600 hover:bg-orange-700"
                      onClick={async () => {
                        try {
                          const response = await fetch('/api/streamlit/start', { method: 'POST' });
                          const data = await response.json();
                          if (response.ok) {
                            alert(`✅ Streamlit запущено!\nURL: ${data.url}`);
                            loadMLModuleStatus();
                          }
                        } catch (error) {
                          alert('❌ Помилка запуску Streamlit');
                        }
                      }}
                    >
                      Запустити
                    </Button>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          await fetch('/api/streamlit/stop', { method: 'POST' });
                          alert('✅ Streamlit зупинено');
                          loadMLModuleStatus();
                        } catch (error) {
                          alert('❌ Помилка зупинки');
                        }
                      }}
                    >
                      Зупинити
                    </Button>
                  </div>

                  <div className="p-3 bg-orange-50 rounded-lg text-sm">
                    <p><strong>Функції:</strong> ML прогноз, схожі об'єкти, аналіз</p>
                    <p><strong>Відгук:</strong> ≤1.5 сек на запит</p>
                    <p><strong>Статус:</strong> {mlModuleStatus.streamlit_running ? '✅ Запущено' : '⏹️ Зупинено'}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Apache Superset Analytics */}
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2 text-red-600" />
                    Apache Superset
                  </CardTitle>
                  <CardDescription>
                    Бізнес-аналітика з 4 готовими дашбордами
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button
                    className="w-full bg-red-600 hover:bg-red-700"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/superset/status');
                        const data = await response.json();
                        if (data.running) {
                          alert(`✅ Superset активний!\nURL: ${data.url}\nДашборди: 4`);
                        } else {
                          alert('⏳ Superset не запущений\nЗапустіть через CLI: python property_monitor_cli.py superset start');
                        }
                      } catch (error) {
                        alert('❌ Помилка перевірки Superset');
                      }
                    }}
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Перевірити статус Superset
                  </Button>

                  <div className="p-3 bg-red-50 rounded-lg text-sm">
                    <p><strong>Дашборди:</strong></p>
                    <ul className="list-disc list-inside text-xs mt-1 space-y-1">
                      <li>Market Overview IF</li>
                      <li>Dynamics & Trends</li>
                      <li>Model Quality</li>
                      <li>Scraper Health</li>
                    </ul>
                    <p className="mt-2"><strong>Статус:</strong> {mlModuleStatus.superset_running ? '✅ Запущено' : '⏹️ Зупинено'}</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Unified CLI Access */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Settings className="w-6 h-6 mr-3 text-slate-600" />
                  Уніфікований CLI Інтерфейс
                </CardTitle>
                <CardDescription>
                  Командний рядок для управління всіма 5 модулями системи
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm">
                  <div className="mb-2 text-slate-300"># Доступні команди:</div>
                  <div className="space-y-1 text-xs">
                    <div><span className="text-blue-400">python property_monitor_cli.py</span> <span className="text-yellow-400">scraper</span> start</div>
                    <div><span className="text-blue-400">python property_monitor_cli.py</span> <span className="text-yellow-400">ml</span> train</div>
                    <div><span className="text-blue-400">python property_monitor_cli.py</span> <span className="text-yellow-400">forecasting</span> predict --all</div>
                    <div><span className="text-blue-400">python property_monitor_cli.py</span> <span className="text-yellow-400">web</span> start</div>
                    <div><span className="text-blue-400">python property_monitor_cli.py</span> <span className="text-yellow-400">pipeline</span> status</div>
                  </div>
                </div>

                <div className="mt-4 grid md:grid-cols-3 gap-4 text-sm">
                  <div className="p-3 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-800 mb-1">Модуль 1: Botasaurus</h4>
                    <p className="text-green-600 text-xs">Антибан парсинг OLX з resume функцією</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-800 mb-1">Модуль 2: LightAutoML</h4>
                    <p className="text-blue-600 text-xs">AutoML для прогнозування цін</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-800 mb-1">Модуль 3: Prophet</h4>
                    <p className="text-purple-600 text-xs">Часові ряди та тренди</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Properties Viewer */}
        {showProperties && (
          <Card className="border-0 shadow-xl mb-8">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Eye className="w-6 h-6 mr-3 text-blue-600" />
                Спаршені оголошення ({properties.length})
              </CardTitle>
              <CardDescription>
                Перегляд усіх зібраних оголошень з OLX
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-96 overflow-y-auto">
                {properties.length > 0 ? (
                  <div className="space-y-3">
                    {properties.map((property: any, index) => (
                      <div key={property.id || index} className="border rounded-lg p-4 bg-slate-50">
                        <div className="grid md:grid-cols-3 gap-4">
                          <div>
                            <h4 className="font-medium text-slate-900 mb-1">{property.title}</h4>
                            <p className="text-sm text-slate-600">{property.district}</p>
                            <p className="text-xs text-slate-500 mt-1">
                              {property.isOwner ? '👤 Власник' : '🏢 Агентство'}
                            </p>
                          </div>
                          <div className="text-sm">
                            <p><span className="font-medium">Ціна:</span> ${property.price_usd?.toLocaleString()}</p>
                            <p><span className="font-medium">Площа:</span> {property.area}м²</p>
                            <p><span className="font-medium">Поверх:</span> {property.floor}</p>
                          </div>
                          <div className="text-xs text-slate-500">
                            <p><span className="font-medium">ID:</span> {property.olx_id}</p>
                            <p><span className="font-medium">Додано:</span> {new Date(property.created_at).toLocaleDateString('uk-UA')}</p>
                            {property.url && (
                              <a href={property.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                Переглянути на OLX
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <Database className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>Немає оголошень для перегляду</p>
                    <p className="text-sm">Запустіть парсинг для збору даних</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

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
                Контроль збору дан��х з OLX
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    scrapingStatus === 'running' ? 'bg-green-500 animate-pulse' :
                    scrapingStatus === 'completed' ? 'bg-blue-500' :
                    scrapingStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
                  }`}></div>
                  <span className="text-sm text-slate-600">
                    Статус: {scrapingStatus === 'running' ? 'Активний' :
                             scrapingStatus === 'completed' ? 'Завершено' :
                             scrapingStatus === 'error' ? 'Помилка' : 'Неактивний'}
                  </span>
                </div>

                {scrapingStatus === 'running' && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>Прогрес парсингу</span>
                      <span>{scrapingProgress}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${scrapingProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <Button
                  className="w-full bg-green-600 hover:bg-green-700"
                  disabled={scrapingStatus === 'running'}
                  onClick={async () => {
                    try {
                      const response = await fetch('/api/start-scraping', { method: 'POST' });
                      const data = await response.json();
                      if (response.ok) {
                        setScrapingStatus('running');
                        alert(`${data.message}\nОчікуваний час: ${data.estimatedTime}`);
                      }
                    } catch (error) {
                      console.error('Scraping error:', error);
                    }
                  }}
                >
                  <Activity className="w-4 h-4 mr-2" />
                  {scrapingStatus === 'running' ? 'Парсинг активний...' : 'Запустити парсинг'}
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
                    Зуп��нити
                  </Button>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <h4 className="text-sm font-medium text-slate-900 mb-1">Налаштування:</h4>
                <ul className="text-xs text-slate-600 space-y-1">
                  <li>• Максимум 10 сторінок за запуск</li>
                  <li>• Затримка 4-8 секунд м��ж запитами</li>
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
                Управління базою д��них
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
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/check-property-updates', { method: 'POST' });
                        const data = await response.json();
                        alert(`Перевірено ${data.totalChecked} оголошень\nЗнайдено ${data.updatesFound} оновлень цін`);
                        if (data.updatesFound > 0) {
                          loadStats();
                        }
                      } catch (error) {
                        console.error('Update check failed:', error);
                        alert('Помилка перевірки онов��ень');
                      }
                    }}
                  >
                    Перевірити оновлення цін
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
                {modelProgress > 0 && modelProgress < 100 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>Прогрес навчання</span>
                      <span>{modelProgress}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${modelProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                <Button
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  disabled={modelProgress > 0 && modelProgress < 100}
                  onClick={async () => {
                    try {
                      const response = await fetch('/api/retrain-model', { method: 'POST' });
                      const data = await response.json();
                      if (response.ok) {
                        alert(`✅ ${data.message}\nОчікуваний час: ${data.estimatedTime}`);
                        setModelProgress(0); // Reset progress
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
                  {modelProgress > 0 && modelProgress < 100 ? 'Тренування...' : 'Перетренувати основну модель'}
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
                        alert('❌ Помилка запус��у розширеного навчання');
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
              {activityLogs.length > 0 ? (
                activityLogs.map((log, index) => (
                  <div key={index} className={`mb-1 ${
                    log.includes('Парсинг') || log.includes('парсинг') ? 'text-green-400' :
                    log.includes('Модель') || log.includes('модель') || log.includes('тренування') ? 'text-purple-400' :
                    log.includes('Помилка') || log.includes('помилка') ? 'text-red-400' :
                    'text-blue-400'
                  }`}>
                    {log}
                  </div>
                ))
              ) : (
                <div className="text-slate-500">Журнал активності порожній...</div>
              )}
            </div>
            <div className="mt-3 flex justify-between text-xs text-slate-500">
              <span>Оновлюється кожні 2 секунди</span>
              <span>Останніх записів: {activityLogs.length}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
