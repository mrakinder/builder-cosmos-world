import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Building, Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <Building className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Glow Nest</h1>
              <p className="text-sm text-slate-600">XGB Property Intelligence</p>
            </div>
          </Link>
        </div>
      </header>

      {/* 404 Content */}
      <div className="flex items-center justify-center min-h-[80vh]">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="mb-8">
            <div className="text-8xl font-bold text-slate-300 mb-4">404</div>
            <h1 className="text-2xl font-bold text-slate-900 mb-4">Сторінку не знайдено</h1>
            <p className="text-slate-600 mb-8">
              Вибачте, але сторінка, яку ви шукаете, не існує або була переміщена.
            </p>
          </div>

          <div className="space-y-4">
            <Button asChild size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              <Link to="/">
                <Home className="w-5 h-5 mr-2" />
                На головну
              </Link>
            </Button>
            
            <Button variant="outline" size="lg" onClick={() => window.history.back()}>
              <ArrowLeft className="w-5 h-5 mr-2" />
              Назад
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
