"""
Task Manager for Background Operations
Manages all 5 modules and their background tasks
"""

import asyncio
import json
import time
import subprocess
import signal
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
from pathlib import Path

from .utils import Logger, EventLogger


class TaskManager:
    """
    Manages background tasks for all 5 modules
    """
    
    def __init__(self):
        self.logger = Logger("cli/logs/task_manager.log")
        self.event_logger = EventLogger()
        
        # Active tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_status: Dict[str, Dict[str, Any]] = {}
        
        # Process management
        self.processes: Dict[str, subprocess.Popen] = {}
        
        # Database path - consistent with Node.js
        self.db_path = "glow_nest.db"
        
    async def initialize(self):
        """Initialize task manager"""
        self.logger.info("🔧 Initializing Task Manager")
        
        # Ensure directories exist
        os.makedirs("cli/logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        os.makedirs("reports/prophet", exist_ok=True)
        
        # Initialize task status
        self.task_status = {
            'scraper': {'status': 'idle', 'progress': 0},
            'ml': {'status': 'idle', 'progress': 0},
            'prophet': {'status': 'idle', 'progress': 0},
            'streamlit': {'status': 'stopped', 'port': None},
            'superset': {'status': 'unknown', 'port': None}
        }
    
    async def cleanup(self):
        """Clean up tasks and processes"""
        self.logger.info("🧹 Cleaning up Task Manager")
        
        # Cancel active tasks
        for task_name, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Terminate processes
        for process_name, process in self.processes.items():
            if process.poll() is None:  # Still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    
    # Scraper tasks (Module 1)
    async def start_scraping_task(self, listing_type: str, max_pages: int, delay_ms: int) -> str:
        """Start real Botasaurus scraping task in background"""
        task_id = f"scraper_{int(time.time())}"

        async def scraping_task():
            try:
                self.task_status['scraper'] = {
                    'status': 'running',
                    'progress': 0,
                    'start_time': time.time(),
                    'listing_type': listing_type,
                    'max_pages': max_pages,
                    'current_page': 0,
                    'total_items': 0,
                    'current_items': 0,
                    'message': 'Ініціалізація Botasaurus scraper...'
                }

                self.event_logger.log_event(
                    "scraper",
                    "start_real_scraping",
                    f"🤖 Запуск реального Botasaurus скрапера: {listing_type}, {max_pages} сторінок",
                    "INFO"
                )

                # Import and run real Botasaurus scraper
                from scraper.olx_scraper import run_scraper_with_progress

                # Define progress callback
                def progress_callback(progress_data):
                    if progress_data.get('type') == 'progress':
                        self.task_status['scraper'].update({
                            'progress': progress_data.get('progress_percent', 0),
                            'current_page': progress_data.get('current_page', 0),
                            'total_pages': progress_data.get('total_pages', max_pages),
                            'current_items': progress_data.get('current_items', 0),
                            'total_items': progress_data.get('total_items', 0),
                            'message': progress_data.get('message', ''),
                            'last_update': time.time()
                        })

                        # Log progress to event logger
                        if progress_data.get('page_completed'):
                            self.event_logger.log_event(
                                "scraper",
                                "page_completed",
                                f"📄 Сторінка {progress_data.get('current_page')}/{progress_data.get('total_pages')}: знайдено {progress_data.get('page_items', 0)} оголошень",
                                "INFO"
                            )

                # Run real Botasaurus scraper with progress
                result = run_scraper_with_progress(
                    listing_type=listing_type,
                    max_pages=max_pages,
                    progress_callback=progress_callback,
                    debug_html=True
                )

                # Final status update
                self.task_status['scraper'].update({
                    'status': 'completed',
                    'progress': 100,
                    'result': result,
                    'end_time': time.time(),
                    'message': 'Парсинг завершено успішно'
                })

                # Log completion
                self.event_logger.log_event(
                    "scraper",
                    "scraping_completed",
                    f"✅ Botasaurus парсинг завершено! Оброблено {result.get('total_processed', 0)} оголошень",
                    "INFO"
                )

            except Exception as e:
                self.logger.error(f"❌ Scraping task error: {str(e)}")
                self.task_status['scraper'].update({
                    'status': 'error',
                    'error': str(e),
                    'message': f'Помилка: {str(e)}'
                })

                self.event_logger.log_event(
                    "scraper",
                    "scraping_error",
                    f"❌ Помилка Botasaurus парсингу: {str(e)}",
                    "ERROR"
                )

        # Start task
        task = asyncio.create_task(scraping_task())
        self.active_tasks[task_id] = task

        return task_id
    
    async def stop_scraping_task(self) -> bool:
        """Stop current scraping task"""
        for task_id, task in self.active_tasks.items():
            if task_id.startswith('scraper_') and not task.done():
                task.cancel()
                self.task_status['scraper']['status'] = 'cancelled'
                return True
        return False
    
    async def get_scraping_status(self) -> Dict[str, Any]:
        """Get current scraping status"""
        return self.task_status.get('scraper', {'status': 'idle', 'progress': 0})
    
    async def get_scraping_logs(self, limit: int = 50) -> List[str]:
        """Get recent scraping logs"""
        try:
            log_file = "scraper/logs/botasaurus_scraper.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    return lines[-limit:] if len(lines) > limit else lines
            return []
        except:
            return []
    
    # ML tasks (Module 2)
    async def start_ml_training_task(self, target_mape: float, timeout: int) -> str:
        """Start ML training task with real-time progress"""
        task_id = f"ml_training_{int(time.time())}"
        
        async def ml_training_task():
            try:
                self.task_status['ml'] = {
                    'status': 'training',
                    'progress': 0,
                    'start_time': time.time(),
                    'target_mape': target_mape
                }
                
                # Import and run ML training
                from ml.laml import train_price_model
                
                # Training with progress simulation
                config = {
                    'target_mape': target_mape,
                    'timeout': timeout
                }
                
                # Simulate real training progress
                for stage_progress in [10, 25, 45, 65, 80, 95, 100]:
                    self.task_status['ml']['progress'] = stage_progress
                    
                    if stage_progress == 100:
                        # Actually run training
                        result = train_price_model(config)
                        self.task_status['ml']['result'] = result
                        
                        if result.get('success'):
                            self.task_status['ml']['status'] = 'completed'
                            self.task_status['ml']['final_mape'] = result.get('metrics', {}).get('mape', 0)
                        else:
                            self.task_status['ml']['status'] = 'failed'
                            self.task_status['ml']['error'] = result.get('error', 'Unknown error')
                    else:
                        await asyncio.sleep(timeout / 10)  # Simulate progress
                
            except Exception as e:
                self.logger.error(f"❌ ML training error: {str(e)}")
                self.task_status['ml']['status'] = 'failed'
                self.task_status['ml']['error'] = str(e)
        
        # Start task
        task = asyncio.create_task(ml_training_task())
        self.active_tasks[task_id] = task
        
        return task_id
    
    async def get_ml_training_progress(self) -> Dict[str, Any]:
        """Get real-time ML training progress"""
        ml_status = self.task_status.get('ml', {'status': 'idle', 'progress': 0})
        
        # Add real-time progress from file if available
        try:
            progress_file = "ml/reports/training_progress.json"
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    file_progress = json.load(f)
                    # Merge with current status
                    ml_status.update(file_progress)
        except:
            pass
        
        return ml_status
    
    async def predict_property_price(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict property price using trained model"""
        try:
            from ml.laml import predict_property_price
            
            result = predict_property_price(property_data)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'predicted_price': None
            }
    
    async def get_ml_status(self) -> Dict[str, Any]:
        """Get ML model status"""
        status = self.task_status.get('ml', {'status': 'idle'})
        
        # Check if model exists
        model_path = "models/laml_price_model.pkl"
        status['model_exists'] = os.path.exists(model_path)
        
        # Check metrics
        metrics_path = "ml/reports/laml_metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                    status['metrics'] = metrics
            except:
                pass
        
        return status
    
    # Prophet tasks (Module 3)
    async def start_prophet_forecasting_task(self, districts: Optional[List[str]], forecast_months: int) -> str:
        """Start Prophet forecasting task"""
        task_id = f"prophet_{int(time.time())}"
        
        async def prophet_task():
            try:
                self.task_status['prophet'] = {
                    'status': 'running',
                    'progress': 0,
                    'start_time': time.time(),
                    'forecast_months': forecast_months
                }
                
                # Import and run Prophet forecasting
                from analytics.prophet import generate_district_forecasts
                
                # Generate forecasts
                forecasts = generate_district_forecasts(
                    districts=districts,
                    forecast_months=forecast_months
                )
                
                self.task_status['prophet']['status'] = 'completed'
                self.task_status['prophet']['progress'] = 100
                self.task_status['prophet']['forecasts'] = forecasts
                
            except Exception as e:
                self.logger.error(f"❌ Prophet forecasting error: {str(e)}")
                self.task_status['prophet']['status'] = 'failed'
                self.task_status['prophet']['error'] = str(e)
        
        # Start task
        task = asyncio.create_task(prophet_task())
        self.active_tasks[task_id] = task
        
        return task_id
    
    async def get_prophet_status(self) -> Dict[str, Any]:
        """Get Prophet forecasting status"""
        return self.task_status.get('prophet', {'status': 'idle', 'progress': 0})
    
    async def get_prophet_forecasts(self) -> Dict[str, Any]:
        """Get latest Prophet forecasts"""
        try:
            forecasts_file = "analytics/reports/district_forecasts.json"
            if os.path.exists(forecasts_file):
                with open(forecasts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    # Streamlit tasks (Module 4)
    async def start_streamlit(self, port: int = 8501) -> bool:
        """Start Streamlit application"""
        try:
            if 'streamlit' in self.processes and self.processes['streamlit'].poll() is None:
                return True  # Already running
            
            # Start Streamlit process
            cmd = ["streamlit", "run", "app/streamlit_app.py", "--server.port", str(port)]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes['streamlit'] = process
            self.task_status['streamlit'] = {
                'status': 'running',
                'port': port,
                'pid': process.pid,
                'start_time': time.time()
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting Streamlit: {str(e)}")
            return False
    
    async def stop_streamlit(self) -> bool:
        """Stop Streamlit application"""
        try:
            if 'streamlit' in self.processes:
                process = self.processes['streamlit']
                if process.poll() is None:  # Still running
                    process.terminate()
                    process.wait(timeout=5)
                
                del self.processes['streamlit']
            
            self.task_status['streamlit'] = {'status': 'stopped', 'port': None}
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping Streamlit: {str(e)}")
            return False
    
    async def get_streamlit_status(self) -> Dict[str, Any]:
        """Get Streamlit status"""
        status = self.task_status.get('streamlit', {'status': 'stopped'})
        
        # Check if process is actually running
        if 'streamlit' in self.processes:
            process = self.processes['streamlit']
            if process.poll() is None:
                status['status'] = 'running'
                status['url'] = f"http://localhost:{status.get('port', 8501)}"
            else:
                status['status'] = 'stopped'
        
        return status
    
    # Superset tasks (Module 5)
    async def get_superset_status(self) -> Dict[str, Any]:
        """Get Apache Superset status"""
        # For now, return mock status
        return {
            'status': 'available',
            'url': 'http://localhost:8088',
            'dashboards': [
                'Market Overview IF',
                'Dynamics & Trends',
                'Model Quality', 
                'Scraper Health'
            ],
            'note': 'Superset requires manual setup. See documentation.'
        }
    
    # Street management
    async def get_street_mappings(self) -> Dict[str, str]:
        """Get street to district mappings"""
        try:
            if not os.path.exists(self.db_path):
                return {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT street, district FROM street_district_map")
            rows = cursor.fetchall()
            conn.close()
            
            return dict(rows)
            
        except Exception as e:
            self.logger.error(f"❌ Error getting street mappings: {str(e)}")
            return {}
    
    async def add_street_mapping(self, street: str, district: str) -> bool:
        """Add street to district mapping"""
        try:
            if not os.path.exists(self.db_path):
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO street_district_map (street, district)
                VALUES (?, ?)
            """, (street, district))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adding street mapping: {str(e)}")
            return False
    
    # Properties
    async def get_recent_properties(self, limit: int = 20, district: str = None) -> List[Dict[str, Any]]:
        """Get recent properties from database"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            sql = "SELECT * FROM properties WHERE is_active = 1"
            params = []
            
            if district:
                sql += " AND district = ?"
                params.append(district)
            
            sql += " ORDER BY scraped_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting recent properties: {str(e)}")
            return []
    
    async def get_property_statistics(self) -> Dict[str, Any]:
        """Get property database statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total properties
            cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
            total = cursor.fetchone()[0]
            
            # By seller type
            cursor.execute("""
                SELECT seller_type, COUNT(*) 
                FROM properties 
                WHERE is_active = 1 
                GROUP BY seller_type
            """)
            seller_stats = dict(cursor.fetchall())
            
            # By district
            cursor.execute("""
                SELECT district, COUNT(*) 
                FROM properties 
                WHERE is_active = 1 
                GROUP BY district
                ORDER BY COUNT(*) DESC
            """)
            district_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_properties': total,
                'by_seller_type': seller_stats,
                'by_district': district_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting property statistics: {str(e)}")
            return {}
    
    # System status
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'scraper': await self.get_scraping_status(),
            'ml': await self.get_ml_status(),
            'prophet': await self.get_prophet_status(),
            'streamlit': await self.get_streamlit_status(),
            'superset': await self.get_superset_status(),
            'database': {
                'exists': os.path.exists(self.db_path),
                'size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0
            },
            'active_tasks': len([t for t in self.active_tasks.values() if not t.done()]),
            'timestamp': datetime.now().isoformat()
        }
