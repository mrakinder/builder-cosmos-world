/**
 * Botasaurus OLX Scraper Integration Module
 * Real scraping integration instead of simulation
 */

import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';

export interface ScrapingProgress {
  status: 'idle' | 'running' | 'completed' | 'error';
  progressPercent: number;
  currentPage: number;
  totalPages: number;
  currentItems: number;
  totalItems: number;
  message: string;
  estimatedTimeLeft: number;
  lastUpdate: Date;
}

export interface ScrapingResult {
  success: boolean;
  stats: {
    total_processed: number;
    new_listings: number;
    updated_listings: number;
    errors: number;
    start_time: string;
    end_time: string;
  };
  error?: string;
}

class BotasaurusIntegration {
  private currentProcess: ChildProcess | null = null;
  private progressCallback: ((progress: ScrapingProgress) => void) | null = null;
  private logCallback: ((message: string) => void) | null = null;
  private currentProgress: ScrapingProgress = {
    status: 'idle',
    progressPercent: 0,
    currentPage: 0,
    totalPages: 0,
    currentItems: 0,
    totalItems: 0,
    message: '',
    estimatedTimeLeft: 0,
    lastUpdate: new Date()
  };

  /**
   * Start real Botasaurus scraping process
   */
  public async startScraping(
    listingType: string = 'sale',
    maxPages: number = 10,
    progressCallback?: (progress: ScrapingProgress) => void,
    logCallback?: (message: string) => void
  ): Promise<void> {
    if (this.currentProcess) {
      throw new Error('Scraping already in progress');
    }

    this.progressCallback = progressCallback;
    this.logCallback = logCallback;

    // Initialize progress
    this.currentProgress = {
      status: 'running',
      progressPercent: 0,
      currentPage: 0,
      totalPages: maxPages,
      currentItems: 0,
      totalItems: 0,
      message: 'Запуск Botasaurus scraper...',
      estimatedTimeLeft: maxPages * 30, // 30 seconds per page estimate
      lastUpdate: new Date()
    };

    this._emitProgress();
    this._emitLog('🤖 Ініціалізація Botasaurus OLX scraper...');

    try {
      // Create logs directory if not exists
      const logsDir = path.join(process.cwd(), 'scraper', 'logs');
      if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
      }

      // Create HTML snapshots directory for debugging
      const htmlDir = path.join(logsDir, 'html');
      if (!fs.existsSync(htmlDir)) {
        fs.mkdirSync(htmlDir, { recursive: true });
      }

      // Spawn Python Botasaurus process
      const pythonScript = path.join(process.cwd(), 'scraper', 'olx_scraper.py');
      
      this.currentProcess = spawn('python', [
        pythonScript,
        '--listing-type', listingType,
        '--max-pages', maxPages.toString(),
        '--output-format', 'json',
        '--real-time-logs', 'true',
        '--debug-html', 'true'
      ], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONPATH: process.cwd(),
          SCRAPER_DEBUG: 'true',
          SCRAPER_DISABLE_CACHE: 'true'
        }
      });

      this._setupProcessHandlers();

    } catch (error) {
      this.currentProgress.status = 'error';
      this.currentProgress.message = `Помилка запуску: ${error.message}`;
      this._emitProgress();
      this._emitLog(`❌ Критична помилка запуску Botasaurus: ${error.message}`);
      throw error;
    }
  }

  /**
   * Stop current scraping process
   */
  public stopScraping(): void {
    if (this.currentProcess) {
      this.currentProcess.kill('SIGTERM');
      this.currentProcess = null;
      
      this.currentProgress.status = 'idle';
      this.currentProgress.message = 'Парсинг зупинено користувачем';
      this._emitProgress();
      this._emitLog('⏹️ Парсинг зупинено користувачем');
    }
  }

  /**
   * Get current progress
   */
  public getProgress(): ScrapingProgress {
    return { ...this.currentProgress };
  }

  /**
   * Check if scraping is currently running
   */
  public isRunning(): boolean {
    return this.currentProgress.status === 'running';
  }

  private _setupProcessHandlers(): void {
    if (!this.currentProcess) return;

    // Handle stdout (progress updates and results)
    this.currentProcess.stdout?.on('data', (data) => {
      const output = data.toString();
      this._parseOutput(output);
    });

    // Handle stderr (errors and debug info)
    this.currentProcess.stderr?.on('data', (data) => {
      const error = data.toString();
      console.error('Botasaurus stderr:', error);
      this._emitLog(`🔍 Debug: ${error.trim()}`);
    });

    // Handle process completion
    this.currentProcess.on('close', (code) => {
      console.log(`Botasaurus process exited with code: ${code}`);
      
      if (code === 0) {
        this.currentProgress.status = 'completed';
        this.currentProgress.progressPercent = 100;
        this.currentProgress.message = 'Парсинг завершено успішно';
        this._emitLog(`✅ Botasaurus парсинг завершено! Оброблено ${this.currentProgress.totalItems} оголошень`);
      } else {
        this.currentProgress.status = 'error';
        this.currentProgress.message = `Парсинг завершено з помилкою (код: ${code})`;
        this._emitLog(`❌ Botasaurus завершився з помилкою (код: ${code})`);
      }
      
      this._emitProgress();
      this.currentProcess = null;
    });

    // Handle process errors
    this.currentProcess.on('error', (error) => {
      console.error('Botasaurus process error:', error);
      this.currentProgress.status = 'error';
      this.currentProgress.message = `Помилка процесу: ${error.message}`;
      this._emitProgress();
      this._emitLog(`❌ Помилка процесу Botasaurus: ${error.message}`);
      this.currentProcess = null;
    });
  }

  private _parseOutput(output: string): void {
    const lines = output.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      try {
        // Try to parse as JSON progress update
        if (line.startsWith('{')) {
          const progress = JSON.parse(line);
          this._updateProgress(progress);
        } else {
          // Regular log message
          this._emitLog(line.trim());
        }
      } catch (error) {
        // Regular log message if not JSON
        if (line.trim()) {
          this._emitLog(line.trim());
        }
      }
    }
  }

  private _updateProgress(progressData: any): void {
    if (progressData.type === 'progress') {
      const oldPercent = this.currentProgress.progressPercent;
      
      this.currentProgress.currentPage = progressData.current_page || this.currentProgress.currentPage;
      this.currentProgress.totalPages = progressData.total_pages || this.currentProgress.totalPages;
      this.currentProgress.currentItems = progressData.current_items || this.currentProgress.currentItems;
      this.currentProgress.totalItems = progressData.total_items || this.currentProgress.totalItems;
      this.currentProgress.progressPercent = progressData.progress_percent || 0;
      this.currentProgress.message = progressData.message || this.currentProgress.message;
      this.currentProgress.estimatedTimeLeft = progressData.estimated_time_left || 0;
      this.currentProgress.lastUpdate = new Date();

      // Emit progress only if significantly changed
      if (Math.abs(this.currentProgress.progressPercent - oldPercent) >= 5) {
        this._emitProgress();
      }

      // Log page completion
      if (progressData.page_completed) {
        this._emitLog(`📄 Сторінка ${progressData.current_page}/${progressData.total_pages}: знайдено ${progressData.page_items || 0} оголошень`);
      }
    }
  }

  private _emitProgress(): void {
    if (this.progressCallback) {
      this.progressCallback({ ...this.currentProgress });
    }
  }

  private _emitLog(message: string): void {
    if (this.logCallback) {
      this.logCallback(message);
    }
  }
}

// Singleton instance
export const botasaurusIntegration = new BotasaurusIntegration();
