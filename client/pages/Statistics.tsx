import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Building, 
  ArrowLeft, 
  TrendingUp, 
  Users, 
  MapPin, 
  Calendar,
  DollarSign,
  BarChart3,
  PieChart,
  Activity
} from "lucide-react";

interface StatisticsData {
  total: number;
  from_owners: number;
  from_agencies: number;
  manual_entries: number;
  last_scraping: string;
  owner_percentage: number;
  districts: { [key: string]: number };
  price_ranges: { [key: string]: number };
  monthly_data: Array<{ month: string; count: number; avg_price: number }>;
  top_streets: Array<{ street: string; count: number; avg_price: number }>;
}

export default function Statistics() {
  const [stats, setStats] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);

      // Load real stats and price trends from API
      const [statsResponse, trendsResponse] = await Promise.all([
        fetch('/api/property-stats'),
        fetch('/api/price-trends')
      ]);

      const apiStats = await statsResponse.json();
      const trendsData = await trendsResponse.json();

      // Use real data from API
      const comprehensiveStats: StatisticsData = {
        total: apiStats.total || 0,
        from_owners: apiStats.from_owners || 0,
        from_agencies: apiStats.from_agencies || 0,
        manual_entries: apiStats.manual_entries || 0,
        last_scraping: apiStats.last_scraping,
        owner_percentage: apiStats.owner_percentage || 0,
        districts: apiStats.districts || {},
        price_ranges: apiStats.price_ranges || {},
        // Use real price trends data
        monthly_data: trendsData.monthly_trends || [],
        top_streets: trendsData.top_streets || []
      };

      setStats(comprehensiveStats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
      // Fallback to basic data if trends fail
      try {
        const response = await fetch('/api/property-stats');
        const apiStats = await response.json();
        setStats({
          total: apiStats.total || 0,
          from_owners: apiStats.from_owners || 0,
          from_agencies: apiStats.from_agencies || 0,
          manual_entries: apiStats.manual_entries || 0,
          last_scraping: apiStats.last_scraping,
          owner_percentage: apiStats.owner_percentage || 0,
          districts: apiStats.districts || {},
          price_ranges: apiStats.price_ranges || {},
          monthly_data: [],
          top_streets: []
        });
      } catch (fallbackError) {
        console.error('Failed to load fallback data:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Завантаження статистики...</p>
        </div>
      </div>
    );
  }

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
                  <p className="text-sm text-slate-600">Статистика парсингу</p>
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
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Детальна статистика парсингу OLX</h1>
          <p className="text-slate-600">Повний аналіз зібраних даних про нерухомість в Івано-Франківську</p>
        </div>

        {/* Overview Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Building className="w-5 h-5 mr-2 text-blue-600" />
                Всього оголошень
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats?.total || 0}</div>
              <p className="text-sm text-slate-600 mt-1">Зібрано з OLX</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Users className="w-5 h-5 mr-2 text-green-600" />
                Від власників
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{stats?.from_owners || 0}</div>
              <p className="text-sm text-slate-600 mt-1">{stats?.owner_percentage || 0}% від загальної кількості</p>
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
              <div className="text-3xl font-bold text-orange-600">{stats?.from_agencies || 0}</div>
              <p className="text-sm text-slate-600 mt-1">{100 - (stats?.owner_percentage || 0)}% від загальної кіль��ості</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-purple-600" />
                Останнє оновлення
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-slate-900">
                {stats?.last_scraping ? new Date(stats.last_scraping).toLocaleDateString('uk-UA') : 'Невідомо'}
              </div>
              <p className="text-sm text-slate-600 mt-1">Дата парсингу</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Districts Distribution */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <MapPin className="w-6 h-6 mr-3 text-blue-600" />
                Розподіл по районах
              </CardTitle>
              <CardDescription>Кількість оголошень по мікрорайонах міста</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats?.districts && Object.entries(stats.districts)
                  .sort(([,a], [,b]) => b - a)
                  .map(([district, count]) => (
                    <div key={district} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">{district}</span>
                      <div className="flex items-center space-x-3">
                        <div className="w-24 bg-slate-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${(count / Math.max(...Object.values(stats.districts))) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-bold text-slate-900 w-8">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Price Distribution */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <DollarSign className="w-6 h-6 mr-3 text-green-600" />
                Розподіл по ціновим категоріям
              </CardTitle>
              <CardDescription>Кількість оголошень в різних цінових діапазонах</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats?.price_ranges && Object.entries(stats.price_ranges).map(([range, count]) => (
                  <div key={range} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">{range}</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-24 bg-slate-200 rounded-full h-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${(count / Math.max(...Object.values(stats.price_ranges))) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-bold text-slate-900 w-8">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Monthly Trends */}
        <Card className="border-0 shadow-xl mb-8">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <TrendingUp className="w-6 h-6 mr-3 text-purple-600" />
              Тенденції по датах
            </CardTitle>
            <CardDescription>Кількість оголошень та середня ціна по датах збору даних</CardDescription>
          </CardHeader>
          <CardContent>
            {stats?.monthly_data && stats.monthly_data.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stats.monthly_data.map((period) => (
                  <div key={period.month || period.date} className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg">
                    <h4 className="font-medium text-slate-900 mb-2">{period.month}</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-600">Кількість:</span>
                        <span className="text-sm font-bold">{period.count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-600">Середня ціна:</span>
                        <span className="text-sm font-bold text-green-600">${period.avg_price.toLocaleString()}</span>
                      </div>
                      {period.price_per_sqm && (
                        <div className="flex justify-between">
                          <span className="text-sm text-slate-600">За м²:</span>
                          <span className="text-sm font-bold text-blue-600">${period.price_per_sqm.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-slate-400 mb-4">
                  <Calendar className="w-16 h-16 mx-auto mb-4" />
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">Немає даних для аналізу</h3>
                <p className="text-slate-600 mb-4">
                  Запустіть парсинг в адмін панелі для збору оголошень з OLX
                </p>
                <Button
                  onClick={() => window.open('/admin', '_blank')}
                  variant="outline"
                >
                  Відкрити адмін панель
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Streets */}
        <Card className="border-0 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <BarChart3 className="w-6 h-6 mr-3 text-indigo-600" />
              Топ вулиць за активністю
            </CardTitle>
            <CardDescription>Найпопулярніші вулиці за кількістю оголошень</CardDescription>
          </CardHeader>
          <CardContent>
            {stats?.top_streets && stats.top_streets.length > 0 ? (
              <div className="space-y-4">
                {stats.top_streets.map((street, index) => (
                  <div key={street.street} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-bold text-indigo-600">{index + 1}</span>
                      </div>
                      <div>
                        <h4 className="font-medium text-slate-900">{street.street}</h4>
                        <p className="text-sm text-slate-600">{street.count} оголошень</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-600">${street.avg_price.toLocaleString()}</div>
                      <div className="text-sm text-slate-600">середня ціна</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-slate-400 mb-4">
                  <MapPin className="w-16 h-16 mx-auto mb-4" />
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">Немає даних по вулицях</h3>
                <p className="text-slate-600">
                  Дані з'являться після парсингу оголошень
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Refresh Button */}
        <div className="flex justify-center mt-8">
          <Button 
            onClick={loadStatistics}
            disabled={loading}
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            <Activity className="w-5 h-5 mr-2" />
            Оновити статистику
          </Button>
        </div>
      </div>
    </div>
  );
}
