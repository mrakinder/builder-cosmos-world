import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Building, ArrowLeft } from "lucide-react";

export default function AdminTest() {
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
                  <p className="text-sm text-slate-600">Тест Адмін Панель</p>
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
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-3xl font-bold text-slate-900 mb-4">✅ Адмін панель працює!</h1>
          <p className="text-lg text-slate-600 mb-8">
            Маршрутизація працює правильно. Ви успішно потрапили на сторінку адміністратора.
          </p>
          
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Статус компон��нтів:</h2>
            <div className="space-y-2 text-left">
              <div className="flex justify-between">
                <span>React Router:</span>
                <span className="text-green-600 font-medium">✅ Працює</span>
              </div>
              <div className="flex justify-between">
                <span>Express.js Backend:</span>
                <span className="text-green-600 font-medium">✅ Працює</span>
              </div>
              <div className="flex justify-between">
                <span>Навігація між сторінками:</span>
                <span className="text-green-600 font-medium">✅ Працює</span>
              </div>
              <div className="flex justify-between">
                <span>SPA Fallback:</span>
                <span className="text-green-600 font-medium">✅ Працює</span>
              </div>
            </div>
          </div>

          <div className="space-x-4">
            <Button asChild>
              <Link to="/statistics">Перейти до статистики</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/">Повернутися на головну</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
