import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Building, TrendingUp, Brain, MapPin, ArrowRight, Star, Shield, Zap, BarChart3, Settings } from "lucide-react";
import { Link } from "react-router-dom";

export default function Index() {
  const [formData, setFormData] = useState({
    area: "",
    floor: "",
    totalFloors: "",
    street: "",
    district: "",
    condition: "",
    description: ""
  });

  const [prediction, setPrediction] = useState<{
    price: number;
    confidence: number;
    factors: string[];
    recommendation: string;
  } | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  // Comprehensive street-to-district mapping
  const streetToDistrict: { [key: string]: string[] } = {
    "Августина Волошина": ["Центр"],
    "Арсенальна": ["Центр"],
    "Бельведерська": ["Центр"],
    "Василя Стуса": ["Позитрон", "Каскад", "Софіївка"],
    "Вербицького": ["Брати"],
    "Вовчинецька": ["Позитрон", "Кішлак", "Софіївка", "Залізничний (Вокзал)"],
    "Галицька": ["Пасічна"],
    "Героїв-пожежників": ["Залізничний (Вокзал)"],
    "Грюнвальдська": ["Залізничний (Вокзал)"],
    "Дашевсь��ого": ["Залізничний (Вокзал)"],
    "Деповська": ["Залізничний (Вокзал)"],
    "Донцова": ["Залізничний (Вокзал)"],
    "Дунаєвського": ["Будівельників"],
    "Залізнична": ["Залізничний (Вокзал)"],
    "Івана Павла ІІ": ["Будівельників", "Софіївка"],
    "Івасюка": ["БАМ", "Софіївка"],
    "Карпатської Січі": ["Центр"],
    "Кисілевської": ["БАМ"],
    "Коновальця": ["Центр", "Опришівці"],
    "Коцюбинського": ["Залізничний (Вокзал)"],
    "Купчинського": ["Залізничний (��окзал)"],
    "Курінного Чорноти": ["Центр"],
    "Львівська": ["Центр"],
    "Мазепи": ["Хриплин"],
    "Марійки Підгірянки": ["Залізничний (Вокзал)"],
    "Матейка": ["Центр"],
    "Миколайчука": ["Центр", "Каскад"],
    "Миру": ["Будівельників"],
    "Молодіжна": ["БАМ", "Будівельників"],
    "Набер��жна ім. В. Стефаника": ["Набережна"],
    "Національної Гвардії": ["Центр"],
    "о. Івана Блавацького": ["Опришівці"],
    "Опільського": ["БАМ"],
    "Паркова": ["БАМ", "Брати"],
    "Пасічна": ["Пасічна"],
    "Петлюри": ["Хриплин"],
    "Пстрака": ["Софіївка"],
    "Прив��кзальна площа": ["Залізничний (Вокзал)"],
    "Промислова": ["Залізничний (Вокзал)"],
    "Реміснича": ["Брати"],
    "Республіканська": ["Центр"],
    "Селянська": ["Будівельників"],
    "Симоненка": ["��озитрон", "Каскад", "Кішлак"],
    "Стефаника": ["Залізничний (Вокзал)"],
    "Тарнавського": ["Залізничний (Вокзал)"],
    "Трильовського": ["БАМ"],
    "Тролейбусна": ["Пасічна"],
    "Угорницька": ["БАМ", "Брати"],
    "Української Дивізії": ["Брати", "Будівельників"],
    "Хіміків": ["Пасічна"],
    "Хоткевича": ["БАМ", "Брати"],
    "Черемшини": ["Залізничний (Вокзал)"],
    "Чорновола": ["Центр"],
    "Чубинського": ["Брати"],
    "24 Серпня": ["Центр", "��аскад"]
  };

  // Updated comprehensive districts list sorted alphabetically
  const districts = [
    "БАМ",
    "Брати",
    "Будівельників",
    "Залізничний (Вокзал)",
    "Каскад",
    "Кішлак",
    "Набережна",
    "Опришівці",
    "Пасічна",
    "Позитрон",
    "Софіївка",
    "Хриплин",
    "Центр",
    "Нерозпізнані райони"
  ];

  const conditions = [
    "Новобудова", "Євроремонт", "Гарний стан", "Житловий стан", "Потребує ремонту"
  ];

  // Function to determine district from street name
  const getDistrictFromStreet = (streetName: string): string => {
    const normalizedStreet = streetName.trim();

    // Check if street exists in our mapping
    if (streetToDistrict[normalizedStreet]) {
      return streetToDistrict[normalizedStreet][0]; // Return first district if multiple
    }

    // Check partial matches (for streets like "вул. Центральна")
    for (const [street, districts] of Object.entries(streetToDistrict)) {
      if (normalizedStreet.toLowerCase().includes(street.toLowerCase()) ||
          street.toLowerCase().includes(normalizedStreet.toLowerCase())) {
        return districts[0];
      }
    }

    return "Нерозпізнані райони";
  };

  // Enhanced price calculation based on district
  const getDistrictPriceMultiplier = (district: string): number => {
    const districtMultipliers: { [key: string]: number } = {
      "Центр": 1.4,
      "Набережна": 1.3,
      "Каскад": 1.2,
      "Софіївка": 1.1,
      "Пасічна": 1.0,
      "БАМ": 0.95,
      "Залізничний (В��кзал)": 0.9,
      "Брати": 0.95,
      "Будівельників": 0.9,
      "Опришівці": 0.85,
      "Позитрон": 0.9,
      "Кішлак": 0.8,
      "Хриплин": 0.75,
      "Нерозпізнані райони": 0.8
    };

    return districtMultipliers[district] || 0.8;
  };

  const handlePredict = async () => {
    if (!formData.area || !formData.condition) {
      return;
    }

    setIsLoading(true);

    try {
      // Determine district from street if provided
      let actualDistrict = formData.district;
      if (formData.street && !formData.district) {
        actualDistrict = getDistrictFromStreet(formData.street);
      }

      // Simulate API call to /api/evaluate
      await new Promise(resolve => setTimeout(resolve, 1500));

      const area = parseFloat(formData.area);
      const basePrice = 1200; // Base price per m²
      const districtMultiplier = getDistrictPriceMultiplier(actualDistrict || "Нерозпізнані райони");

      // Enhanced price calculation
      const conditionMultiplier = {
        "Новобудова": 1.3,
        "Євроремонт": 1.2,
        "Гарний стан": 1.0,
        "Житловий стан": 0.9,
        "Потребує ремонту": 0.7
      }[formData.condition] || 1.0;

      const floorMultiplier = formData.floor ?
        (parseInt(formData.floor) > 1 && parseInt(formData.floor) < 9 ? 1.05 : 0.95) : 1.0;

      const calculatedPrice = Math.round(
        area * basePrice * districtMultiplier * conditionMultiplier * floorMultiplier +
        (Math.random() * 10000 - 5000) // Random variance ±5000
      );

      // Generate district-specific factors
      const getDistrictFactors = (district: string): string[] => {
        const factorsMap: { [key: string]: string[] } = {
          "Центр": ["Престижний центральний район", "Близькість до історичного центру", "Розвинена інфраструктура"],
          "Набережна": ["Мальовничий вид", "Близькість до набережної", "Тиха локація"],
          "��аскад": ["Новий сучасний район", "Гарна екологія", "Сучасна забудова"],
          "Софіївка": ["Зелений район", "Спокійне середовище", "Доступні ціни"],
          "Пасічна": ["Добра транспортна доступність", "Розвинена торгівля", "Центральне розташування"],
          "БАМ": ["Великий житловий масив", "Розвинена соціальна інфраструктура", "Доступне житло"],
          "Залізничний (Вокзал)": ["Близькість до вокзалу", "Транспортний вузол", "Комерційна активність"],
          "Нерозпізнані райони": ["Потребує уточнення рай��ну", "Середні ринкові показники", "Стандартні умови"]
        };
        return factorsMap[district] || factorsMap["Нерозпізнані райони"];
      };

      const confidence = actualDistrict === "Нерозпізнані райони" ?
        Math.round(70 + Math.random() * 10) :
        Math.round(85 + Math.random() * 10);

      const mockPrediction = {
        price: calculatedPrice,
        confidence: confidence,
        factors: getDistrictFactors(actualDistrict || "Нерозпізнані райони"),
        recommendation: actualDistrict === "Нерозпізнані райони" ?
          "Рекомендуємо уточнити район для більш точного прогнозу" :
          `Ціна відповідає ринковим показникам для району "${actualDistrict}"`
      };

      setPrediction(mockPrediction);
    } catch (error) {
      console.error("Prediction error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Building className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Glow Nest</h1>
                <p className="text-sm text-slate-600">XGB Property Intelligence</p>
              </div>
            </div>
            <nav className="flex items-center space-x-3 md:space-x-6">
              <a href="#evaluate" className="hidden md:block text-slate-600 hover:text-blue-600 transition-colors">Оцінити</a>
              <a href="#analytics" className="hidden md:block text-slate-600 hover:text-blue-600 transition-colors">Аналітика</a>
              <Button
                variant="outline"
                size="sm"
                asChild
                className="border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white"
              >
                <Link to="/admin">
                  <Settings className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Адмін панель</span>
                  <span className="sm:hidden">Адмін</span>
                </Link>
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 lg:py-32">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl lg:text-6xl font-bold text-slate-900 mb-6">
              Прогнозування вартості
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent block mt-2">
                нерухомості в Івано-Франківську
              </span>
            </h1>
            <p className="text-xl text-slate-600 mb-8 leading-relaxed">
              Використовуйте передові ML-алгоритми XGBoost для точн��го прогнозування 
              ринкової вартості об'єктів нерухомості на основі відкритих даних та експертного аналізу
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8"
                onClick={() => document.getElementById('evaluate')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <TrendingUp className="w-5 h-5 mr-2" />
                Оцінити нерухомість
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-slate-300"
                onClick={() => document.getElementById('analytics')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <BarChart3 className="w-5 h-5 mr-2" />
                Переглянути аналітику
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Чому обирають Glow Nest</h2>
            <p className="text-lg text-slate-600">Найсучасніші технології для найточніших прогнозів</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-blue-600" />
                </div>
                <CardTitle className="text-xl">XGBoost ML</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <CardDescription className="text-base leading-relaxed">
                  Передові алгоритми машинного навчання з високою точністю прогнозування на основі історичних даних
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-green-600" />
                </div>
                <CardTitle className="text-xl">Надійні дані</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <CardDescription className="text-base leading-relaxed">
                  Валідація через Zod та Pydantic, кешування результатів та аналіз відкритих да��их OLX
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-8 h-8 text-purple-600" />
                </div>
                <CardTitle className="text-xl">Швидкі результати</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <CardDescription className="text-base leading-relaxed">
                  Миттєва оцінка через REST API з детальним аналізом факторів та рекомендаціями
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Property Evaluation Form */}
      <section id="evaluate" className="py-20 bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-slate-900 mb-4">Оцінити нерухомість</h2>
              <p className="text-lg text-slate-600">Введіть характеристики об'єкта для отримання прогнозу вартості</p>
            </div>

            <Card className="border-0 shadow-2xl">
              <CardHeader>
                <CardTitle className="flex items-center text-2xl">
                  <MapPin className="w-6 h-6 mr-3 text-blue-600" />
                  Характеристики нерухомості
                </CardTitle>
                <CardDescription>
                  Заповніть усі обов'язкові поля для отримання точного прогнозу
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Площа (м²) *</label>
                    <Input
                      type="number"
                      placeholder="60"
                      value={formData.area}
                      onChange={(e) => setFormData(prev => ({ ...prev, area: e.target.value }))}
                      className="h-12"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Вулиця (необов'язково)</label>
                    <Input
                      type="text"
                      placeholder="наприклад: Центральна, Галицька"
                      value={formData.street}
                      onChange={(e) => {
                        const street = e.target.value;
                        setFormData(prev => ({
                          ...prev,
                          street: street,
                          district: street ? getDistrictFromStreet(street) : prev.district
                        }));
                      }}
                      className="h-12"
                    />
                    {formData.street && (
                      <p className="text-xs text-blue-600">
                        Автоматично визначено район: {getDistrictFromStreet(formData.street)}
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Район</label>
                    <Select value={formData.district} onValueChange={(value) => setFormData(prev => ({ ...prev, district: value }))}>
                      <SelectTrigger className="h-12">
                        <SelectValue placeholder="Оберіть район або введ��ть вулицю" />
                      </SelectTrigger>
                      <SelectContent>
                        {districts.map((district) => (
                          <SelectItem key={district} value={district}>{district}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Поверх</label>
                    <Input
                      type="number"
                      placeholder="3"
                      value={formData.floor}
                      onChange={(e) => setFormData(prev => ({ ...prev, floor: e.target.value }))}
                      className="h-12"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Загальна кількість поверхів</label>
                    <Input
                      type="number"
                      placeholder="9"
                      value={formData.totalFloors}
                      onChange={(e) => setFormData(prev => ({ ...prev, totalFloors: e.target.value }))}
                      className="h-12"
                    />
                  </div>
                  <div></div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">Стан нерухомості *</label>
                  <Select value={formData.condition} onValueChange={(value) => setFormData(prev => ({ ...prev, condition: value }))}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Оберіть стан" />
                    </SelectTrigger>
                    <SelectContent>
                      {conditions.map((condition) => (
                        <SelectItem key={condition} value={condition}>{condition}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">Опис (опціонально)</label>
                  <textarea 
                    className="w-full h-24 px-3 py-2 border border-input rounded-md bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    placeholder="Додаткова інформація про об'єкт..."
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  />
                </div>

                <Button
                  onClick={handlePredict}
                  disabled={isLoading || !formData.area || !formData.condition}
                  size="lg"
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 h-12"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Аналізую...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <TrendingUp className="w-5 h-5 mr-2" />
                      Отримати прогноз
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </div>
                  )}
                </Button>

                {/* Prediction Results */}
                {prediction && (
                  <div className="mt-8 p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                    <div className="flex items-center mb-4">
                      <Star className="w-6 h-6 text-green-600 mr-2" />
                      <h3 className="text-xl font-semibold text-green-800">Результат прогнозування</h3>
                    </div>
                    
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <div className="text-3xl font-bold text-green-800 mb-2">
                          ${prediction.price.toLocaleString()}
                        </div>
                        <div className="text-sm text-green-600 mb-4">
                          ��очність: {prediction.confidence}%
                        </div>
                        <div className="space-y-2">
                          <h4 className="font-medium text-green-800">Ключові фактори:</h4>
                          <ul className="space-y-1">
                            {prediction.factors.map((factor, index) => (
                              <li key={index} className="text-sm text-green-700 flex items-center">
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></div>
                                {factor}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-green-800 mb-2">Рекомендація:</h4>
                        <p className="text-sm text-green-700 leading-relaxed">
                          {prediction.recommendation}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>



      {/* Analytics Section */}
      <section id="analytics" className="py-20 bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-slate-900 mb-4">Аналітика та статистика</h2>
              <p className="text-lg text-slate-600">Детальний аналіз ринку нерухомості та ефективності моделей</p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="border-0 shadow-lg">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <BarChart3 className="w-8 h-8 text-green-600" />
                  </div>
                  <CardTitle>Статистика OLX</CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => window.open('/statistics', '_blank')}
                  >
                    Детальна статистика
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-8 h-8 text-blue-600" />
                  </div>
                  <CardTitle>Ефективність моделі</CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/model-info');
                        const data = await response.json();
                        alert(`Модель:\nR²: ${data.r2 || 'N/A'}\nMAE: ${data.mae || 'N/A'}\nRMSE: ${data.rmse || 'N/A'}`);
                      } catch (error) {
                        console.error('Model info error:', error);
                        alert('Помилка отримання інформації про модель');
                      }
                    }}
                  >
                    Метрики моделі
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-purple-600" />
                  </div>
                  <CardTitle>Ручні дані</CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/manual-property-stats');
                        const data = await response.json();
                        alert(`Ручні дані:\nВсього: ${data.total_manual}\nЧастка: ${data.manual_percentage}%`);
                      } catch (error) {
                        console.error('Manual stats error:', error);
                        alert('Помилка отримання статистики ручних даних');
                      }
                    }}
                  >
                    Статистика ручних даних
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Building className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold">Glow Nest XGB</span>
              </div>
              <p className="text-slate-400 text-sm">
                Інноваційна платформа для прогнозування вартості нерухомості в Івано-Франківську
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">API</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>/api/evaluate</li>
                <li>/api/advanced-evaluate</li>
                <li>/api/predict-xgb</li>
                <li>/api/scraping</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Моделі</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>XGBoost ML</li>
                <li>Поліноміальна регресія</li>
                <li>Advanced Model</li>
                <li>Real Data Model</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Технології</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>Python + Node.js</li>
                <li>SQLite Database</li>
                <li>Playwright Scraping</li>
                <li>Zod + Pydantic</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-sm text-slate-400">
            <p>&copy; 2024 Glow Nest XGB. Усі права захищені.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
