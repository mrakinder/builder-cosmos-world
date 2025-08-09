"""
Unified REST API Server for Property Monitor IF
Button-based control interface for all 5 modules
Replaces CLI with web-based management
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import uvicorn
from .tasks import TaskManager
from .utils import Logger, EventLogger


# Pydantic models for API
class ScrapingRequest(BaseModel):
    listing_type: str = "sale"  # 'rent' or 'sale'
    max_pages: int = 10
    delay_ms: int = 5000
    headful: bool = False  # додано для сумісності з майбутніми запитами

class MLTrainingRequest(BaseModel):
    target_mape: float = 15.0
    timeout: int = 3600

class ProphetForecastRequest(BaseModel):
    districts: Optional[List[str]] = None
    forecast_months: int = 6

class MLPredictionRequest(BaseModel):
    area: float
    district: str
    rooms: int = 2
    floor: int = 1
    total_floors: int = 9
    building_type: str = "квартира"
    renovation_status: str = "хороший"
    seller_type: str = "owner"

class StreamlitControlRequest(BaseModel):
    action: str  # 'start' or 'stop'
    port: int = 8501

class StreetMappingRequest(BaseModel):
    street: str
    district: str


# Global task manager
task_manager = TaskManager()
logger = Logger("cli/logs/api_server.log")
event_logger = EventLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("🚀 Starting Property Monitor IF API Server")
    event_logger.log_event("api_server", "startup", "API server starting up", "INFO")
    
    # Initialize task manager
    await task_manager.initialize()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Property Monitor IF API Server")
    event_logger.log_event("api_server", "shutdown", "API server shutting down", "INFO")
    
    # Cleanup tasks
    await task_manager.cleanup()


# FastAPI application
app = FastAPI(
    title="Property Monitor IF - Unified API",
    description="REST API for managing 5-module real estate analysis system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev",  # Frontend URL
        "http://localhost:3000",  # Local development
        "http://localhost:8080",  # Local API testing
        "*"  # Allow all for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Enhanced health check endpoint with runtime info
@app.get("/health")
async def health_check():
    """Enhanced health check with process info"""
    import os
    import subprocess

    # Get git info if available
    git_info = "unknown"
    try:
        git_info = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                          stderr=subprocess.DEVNULL).decode().strip()
    except:
        pass

    return {
        "ok": True,
        "status": "healthy",
        "pid": os.getpid(),
        "timestamp": datetime.now().isoformat(),
        "version": git_info,
        "host": "0.0.0.0:8080",
        "runtime": "FastAPI + Uvicorn",
        "modules": {
            "scraper": "ready",
            "ml": "ready",
            "prophet": "ready",
            "streamlit": "ready",
            "superset": "ready"
        }
    }


# ---- CUSTOM JSON HANDLERS FOR 404/422 TO PREVENT EMPTY BODY ----
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Всюди JSON, навіть на 404
    return JSONResponse(
        {"ok": False, "error": f"{exc.status_code} {exc.detail}", "path": str(request.url.path)},
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"ok": False, "error": "ValidationError", "details": exc.errors()}, status_code=422)

# ---- ROUTE LOGGING AT STARTUP ----
@app.on_event("startup")
async def dump_routes():
    logger.info("📍 AVAILABLE ROUTES:")
    for r in app.routes:
        try:
            if hasattr(r, 'methods') and hasattr(r, 'path'):
                methods = ','.join(r.methods) if r.methods else 'N/A'
                logger.info(f"   {methods} {r.path}")
        except Exception as e:
            logger.warning(f"   Could not log route: {e}")

# ---- RUNTIME DEBUG ENDPOINT ----
@app.get("/__debug/routes")
def debug_routes():
    """Runtime route inspection endpoint"""
    routes = []
    for r in app.routes:
        try:
            methods = list(r.methods or []) if hasattr(r, 'methods') else []
            path = getattr(r, "path", None)
            if path:
                routes.append({"methods": methods, "path": path})
        except Exception as e:
            routes.append({"error": str(e)})
    return {
        "ok": True,
        "total_routes": len(routes),
        "routes": routes,
        "critical_check": {
            "scraper_start": any("/scraper/start" in r.get("path", "") for r in routes),
            "api_scraper_start": any("/api/scraper/start" in r.get("path", "") for r in routes),
            "health": any("/health" in r.get("path", "") for r in routes)
        }
    }

# Module 1: Botasaurus Scraper Endpoints - DIRECT APP DECORATORS
@app.post("/scraper/start")
@app.post("/api/scraper/start")  # alias для проксі з префіксом
async def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Start Botasaurus OLX scraping - GUARANTEED JSON-only response, never empty body"""

    # ENTRY LOG for diagnostics + request body details
    logger.info(f"🚪 HIT /scraper/start - listing_type={request.listing_type}, max_pages={request.max_pages}, delay_ms={request.delay_ms}")
    logger.info(f"📋 Request body parsed successfully: {request.model_dump()}")

    try:
        # Check if scraper is already running
        current_status = await task_manager.get_scraping_status()
        if current_status.get('status') == 'running':
            logger.info("🔁 RETURN /scraper/start 409 - already running")
            return JSONResponse(
                {"ok": False, "error": "Scraper already running", "status": "running"},
                status_code=409,
                headers={"Content-Type": "application/json", "Cache-Control": "no-cache"}
            )

        logger.info(f"🕷️ Starting scraper: {request.listing_type}, {request.max_pages} pages")

        # Start scraping task in background
        task_id = await task_manager.start_scraping_task(
            listing_type=request.listing_type,
            max_pages=request.max_pages,
            delay_ms=request.delay_ms
        )

        event_logger.log_event(
            "scraper",
            "start_scraping",
            f"Started scraping {request.listing_type} listings",
            "INFO"
        )

        # Prepare response body
        response_body = {
            "ok": True,
            "task": task_id,
            "status": "running",
            "message": f"Scraping started for {request.listing_type} listings",
            "estimated_time": f"{request.max_pages * 10} seconds",
            "parameters": {
                "listing_type": request.listing_type,
                "max_pages": request.max_pages,
                "delay_ms": request.delay_ms
            }
        }

        # LOG before return to ensure we reach this point
        logger.info(f"✅ RETURN /scraper/start 202 JSON - task={task_id}")

        # GUARANTEED JSON response
        return JSONResponse(
            response_body,
            status_code=202,
            headers={"Content-Type": "application/json", "Cache-Control": "no-cache"}
        )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"❌ Error starting scraper: {error_msg}")
        logger.error(f"🔄 RETURN /scraper/start 500 JSON - error={error_msg}")

        # GUARANTEED JSON error response - never empty
        return JSONResponse(
            {
                "ok": False,
                "error": error_msg,
                "status": "error",
                "timestamp": time.time()
            },
            status_code=500,
            headers={"Content-Type": "application/json", "Cache-Control": "no-cache"}
        )


@app.post("/scraper/stop")
@app.post("/api/scraper/stop")  # alias для проксі з префіксом
async def stop_scraping():
    """Stop current scraping task - returns JSON-only response"""
    try:
        success = await task_manager.stop_scraping_task()

        event_logger.log_event(
            "scraper",
            "stop_scraping",
            "Scraping stopped by user",
            "WARNING"
        )

        return JSONResponse(
            {
                "ok": success,
                "message": "Scraping stopped" if success else "No active scraping task"
            },
            status_code=200,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"❌ Error stopping scraper: {str(e)}")
        # Always return JSON, never raise HTTPException
        return JSONResponse(
            {"ok": False, "error": f"{type(e).__name__}: {str(e)}"},
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


@app.get("/scraper/status")
async def get_scraping_status():
    """Get current scraping status"""
    try:
        status = await task_manager.get_scraping_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting scraper status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scraper/logs")
async def get_scraping_logs(limit: int = 50):
    """Get recent scraping logs"""
    try:
        logs = await task_manager.get_scraping_logs(limit)
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"❌ Error getting scraper logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Module 2: LightAutoML Endpoints  
@app.post("/ml/train")
async def train_ml_model(request: MLTrainingRequest, background_tasks: BackgroundTasks):
    """Train LightAutoML model with real-time progress"""
    try:
        logger.info("🧠 Starting LightAutoML training...")
        
        # Start training task
        task_id = await task_manager.start_ml_training_task(
            target_mape=request.target_mape,
            timeout=request.timeout
        )
        
        event_logger.log_event(
            "ml",
            "start_training",
            f"Started ML training with MAPE target {request.target_mape}%",
            "INFO"
        )
        
        return {
            "success": True,
            "message": "ML training started",
            "task_id": task_id,
            "estimated_time": f"{request.timeout // 60} minutes",
            "target_mape": request.target_mape
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting ML training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/progress")
async def get_ml_training_progress():
    """Get real-time ML training progress (0-100%)"""
    try:
        progress = await task_manager.get_ml_training_progress()
        return progress
        
    except Exception as e:
        logger.error(f"❌ Error getting ML progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/progress/stream")
async def stream_ml_progress():
    """Server-Sent Events stream for real-time ML progress"""
    async def event_stream():
        try:
            while True:
                progress = await task_manager.get_ml_training_progress()
                
                # Format as SSE
                data = json.dumps(progress)
                yield f"data: {data}\n\n"
                
                # Break if training completed
                if progress.get('status') in ['completed', 'failed']:
                    break
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.post("/ml/predict")
async def predict_property_price(request: MLPredictionRequest):
    """Predict property price using trained ML model"""
    try:
        logger.info(f"🔮 Predicting price for {request.district} property")
        
        prediction = await task_manager.predict_property_price(request.dict())
        
        event_logger.log_event(
            "ml",
            "price_prediction",
            f"Price predicted for {request.district}: ${prediction.get('predicted_price', 0)}",
            "INFO"
        )
        
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Error in price prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/status")
async def get_ml_status():
    """Get ML model status and information"""
    try:
        status = await task_manager.get_ml_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting ML status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Module 3: Prophet Forecasting Endpoints
@app.post("/prophet/forecast")
async def generate_prophet_forecasts(request: ProphetForecastRequest, background_tasks: BackgroundTasks):
    """Generate Prophet forecasts for districts"""
    try:
        logger.info(f"📈 Starting Prophet forecasting for {request.forecast_months} months")
        
        task_id = await task_manager.start_prophet_forecasting_task(
            districts=request.districts,
            forecast_months=request.forecast_months
        )
        
        event_logger.log_event(
            "prophet",
            "start_forecasting",
            f"Started forecasting for {len(request.districts or [])} districts",
            "INFO"
        )
        
        return {
            "success": True,
            "message": "Prophet forecasting started",
            "task_id": task_id,
            "forecast_months": request.forecast_months,
            "districts": request.districts
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting Prophet forecasting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prophet/status")
async def get_prophet_status():
    """Get Prophet forecasting status"""
    try:
        status = await task_manager.get_prophet_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting Prophet status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prophet/forecasts")
async def get_prophet_forecasts():
    """Get latest Prophet forecast results"""
    try:
        forecasts = await task_manager.get_prophet_forecasts()
        return forecasts
        
    except Exception as e:
        logger.error(f"❌ Error getting Prophet forecasts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Module 4: Streamlit Control Endpoints
@app.post("/streamlit/control")
async def control_streamlit(request: StreamlitControlRequest):
    """Start or stop Streamlit application"""
    try:
        if request.action == "start":
            result = await task_manager.start_streamlit(port=request.port)
            message = f"Streamlit started on port {request.port}"
        elif request.action == "stop":
            result = await task_manager.stop_streamlit()
            message = "Streamlit stopped"
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")
        
        event_logger.log_event(
            "streamlit",
            request.action,
            message,
            "INFO"
        )
        
        return {
            "success": result,
            "message": message,
            "action": request.action
        }
        
    except Exception as e:
        logger.error(f"❌ Error controlling Streamlit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/streamlit/status")
async def get_streamlit_status():
    """Get Streamlit application status"""
    try:
        status = await task_manager.get_streamlit_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting Streamlit status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Module 5: Apache Superset Endpoints
@app.get("/superset/status")
async def get_superset_status():
    """Get Apache Superset status"""
    try:
        status = await task_manager.get_superset_status()
        return status
        
    except Exception as e:
        logger.error(f"�� Error getting Superset status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Street Management Endpoints
@app.get("/streets/mapping")
async def get_street_mappings():
    """Get all street to district mappings"""
    try:
        mappings = await task_manager.get_street_mappings()
        return {"street_mappings": mappings}
        
    except Exception as e:
        logger.error(f"❌ Error getting street mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/streets/add")
async def add_street_mapping(request: StreetMappingRequest):
    """Add new street to district mapping"""
    try:
        success = await task_manager.add_street_mapping(
            street=request.street,
            district=request.district
        )
        
        event_logger.log_event(
            "streets",
            "add_mapping",
            f"Added mapping: {request.street} -> {request.district}",
            "INFO"
        )
        
        return {
            "success": success,
            "message": f"Added mapping: {request.street} -> {request.district}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error adding street mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Event Log Endpoints
@app.get("/events/stream")
async def stream_events():
    """Server-Sent Events stream for real-time event log"""
    async def event_stream():
        try:
            last_event_id = 0

            while True:
                events = event_logger.get_recent_events(since_id=last_event_id, limit=10)

                for event in events:
                    data = json.dumps(event)
                    yield f"data: {data}\n\n"
                    last_event_id = max(last_event_id, event.get('id', 0))

                await asyncio.sleep(1)  # Check for new events every second

        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# Scraper Progress SSE Endpoints (multiple paths for compatibility)
@app.get("/progress/scrape")
async def stream_scraper_progress():
    """Server-Sent Events stream for real-time scraper progress"""
    async def progress_stream():
        try:
            while True:
                scraper_status = await task_manager.get_scraping_status()

                # Format progress data for SSE
                progress_data = {
                    "type": "progress",
                    "module": "scraper",
                    "status": scraper_status.get('status', 'idle'),
                    "progress": scraper_status.get('progress', 0),
                    "current_page": scraper_status.get('current_page', 0),
                    "total_pages": scraper_status.get('max_pages', 0),
                    "current_items": scraper_status.get('current_items', 0),
                    "total_items": scraper_status.get('total_items', 0),
                    "message": scraper_status.get('message', ''),
                    "timestamp": time.time()
                }

                data = json.dumps(progress_data)
                yield f"data: {data}\n\n"

                # Stop streaming if completed or failed
                if scraper_status.get('status') in ['completed', 'error', 'cancelled']:
                    break

                await asyncio.sleep(1)  # Update every second

        except Exception as e:
            error_data = json.dumps({
                "type": "error",
                "module": "scraper",
                "error": str(e)
            })
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/events/recent")
async def get_recent_events(limit: int = 50):
    """Get recent events from event log"""
    try:
        events = event_logger.get_recent_events(limit=limit)
        return {"events": events}
        
    except Exception as e:
        logger.error(f"❌ Error getting recent events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# System Status Endpoint
@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        status = await task_manager.get_system_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Properties Endpoints  
@app.get("/properties/recent")
async def get_recent_properties(limit: int = 20, district: str = None):
    """Get recent properties from database"""
    try:
        properties = await task_manager.get_recent_properties(limit=limit, district=district)
        return {"properties": properties}
        
    except Exception as e:
        logger.error(f"❌ Error getting recent properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/stats")
async def get_property_statistics():
    """Get property database statistics"""
    try:
        stats = await task_manager.get_property_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting property statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# CORS preflight for SSE
@app.options("/scraper/progress/stream")
async def scraper_progress_stream_options():
    """Handle CORS preflight for scraper progress stream"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Cache-Control, Content-Type"
        }
    )


@app.options("/events/stream")
async def events_stream_options():
    """Handle CORS preflight for events stream"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Cache-Control, Content-Type"
        }
    )


# Run server
def run_server(host: str = "0.0.0.0", port: int = 8080, debug: bool = True):
    """Run the FastAPI server"""
    logger.info(f"🌐 Starting API server on {host}:{port}")

    # LOG ALL ROUTES for debugging 404 issues
    logger.info("📍 AVAILABLE ROUTES:")
    for route in app.routes:
        try:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ','.join(route.methods) if route.methods else 'N/A'
                logger.info(f"   {methods} {route.path}")
        except Exception as e:
            logger.warning(f"   Could not log route: {e}")

    uvicorn.run(
        "cli.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
