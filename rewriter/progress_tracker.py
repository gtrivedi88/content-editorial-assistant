"""
World-Class Real-Time Progress Tracker
Advanced progress tracking for assembly line AI rewriting with real-time WebSocket updates.
Provides accurate progress percentages, station tracking, and performance metrics.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

class WorldClassProgressTracker:
    """
    World-class progress tracking system with real-time updates and performance metrics.
    Handles multi-pass, multi-station assembly line processing with precise progress calculation.
    """
    
    def __init__(self, session_id: str, block_id: str, progress_callback: Optional[Callable] = None):
        print(f"\n🔍 DEBUG PROGRESS TRACKER INIT:")
        print(f"   📋 session_id: {session_id}")
        print(f"   📋 block_id: {block_id}")
        print(f"   📋 progress_callback: {progress_callback}")
        print(f"   📋 progress_callback type: {type(progress_callback)}")
        
        self.session_id = session_id
        self.block_id = block_id
        self.progress_callback = progress_callback
        
        # Progress state
        self.total_stations = 0
        self.completed_stations = 0
        self.current_station = ""
        self.current_station_index = 0
        self.station_progress = {}
        
        # Multi-pass tracking
        self.total_passes = 1
        self.current_pass = 1
        self.pass_progress = {}
        
        # Performance metrics
        self.start_time = time.time()
        self.station_start_times = {}
        self.station_durations = {}
        
        # Thread safety
        self._lock = Lock()
        
        # WebSocket integration
        print(f"   📡 Attempting to import WebSocket handlers...")
        self._websocket_available = True
        try:
            from app_modules.websocket_handlers import emit_progress, emit_station_progress_update
            self.emit_progress = emit_progress
            self.emit_station_progress = emit_station_progress_update
            print(f"   ✅ WebSocket handlers imported successfully")
        except ImportError as e:
            logger.warning("WebSocket handlers not available - progress will be callback-only")
            self._websocket_available = False
            self.emit_progress = self._fallback_emit
            self.emit_station_progress = self._fallback_emit
            print(f"   ⚠️  WebSocket handlers import failed: {e}")
        
        print(f"   ✅ WorldClassProgressTracker initialized successfully")
        logger.info(f"🎯 World-class progress tracker initialized for {block_id}")
    
    def _fallback_emit(self, *args, **kwargs):
        """Fallback for when WebSocket is not available."""
        pass
    
    def initialize_multi_pass_processing(self, stations: List[str], total_passes: int = 1):
        """Initialize multi-pass processing with station tracking."""
        with self._lock:
            self.total_stations = len(stations)
            self.total_passes = total_passes
            self.station_progress = {station: {'status': 'pending', 'progress': 0} for station in stations}
            
            # Calculate total work units (stations × passes)
            total_work_units = self.total_stations * self.total_passes
            
            logger.info(f"🏭 Initialized {total_passes}-pass processing with {self.total_stations} stations ({total_work_units} total work units)")
            
            # Emit initial progress
            self._emit_overall_progress(0, "Initializing assembly line processing...", "Setting up multi-pass pipeline")
    
    def start_pass(self, pass_number: int, pass_name: str):
        """Start a new processing pass."""
        with self._lock:
            self.current_pass = pass_number
            self.pass_progress[pass_number] = {
                'name': pass_name,
                'start_time': time.time(),
                'stations_completed': 0,
                'status': 'processing'
            }
            
            # Calculate progress based on completed passes
            previous_passes_progress = ((pass_number - 1) / self.total_passes) * 100
            
            logger.info(f"🚀 Starting Pass {pass_number}/{self.total_passes}: {pass_name}")
            
            # Emit progress update
            self._emit_overall_progress(
                int(previous_passes_progress),
                f"Pass {pass_number}: {pass_name}",
                f"Starting {pass_name.lower()} processing..."
            )
    
    def start_station(self, station: str, station_name: str, errors_count: int):
        """Start processing a station with detailed tracking."""
        with self._lock:
            self.current_station = station
            self.current_station_index = list(self.station_progress.keys()).index(station) if station in self.station_progress else 0
            self.station_start_times[station] = time.time()
            
            # Update station status
            self.station_progress[station] = {
                'status': 'processing',
                'progress': 0,
                'errors_count': errors_count,
                'start_time': time.time()
            }
            
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress()
            
            logger.info(f"🏗️ Station {station_name}: Processing {errors_count} errors (Station {self.current_station_index + 1}/{self.total_stations})")
            
            # Emit BOTH types of progress updates for frontend compatibility
            # 1. General progress update
            self._emit_overall_progress(
                overall_progress,
                f"Pass {self.current_pass}: {station_name}",
                f"Processing {errors_count} {station} issue(s)..."
            )
            
            # 2. Station-specific progress update for assembly line UI
            if self._websocket_available:
                self.emit_station_progress(
                    self.session_id, 
                    self.block_id, 
                    station, 
                    'processing',
                    f"Processing {errors_count} {station} issue(s)..."
                )
    
    def update_station_progress(self, station: str, progress: int, status_message: str = ""):
        """Update progress within a station (0-100%)."""
        with self._lock:
            if station in self.station_progress:
                self.station_progress[station]['progress'] = progress
                
                # Calculate overall progress
                overall_progress = self._calculate_overall_progress()
                
                # Emit BOTH types of progress updates
                if status_message:
                    # 1. General progress update
                    self._emit_overall_progress(
                        overall_progress,
                        f"Pass {self.current_pass}: {station}",
                        status_message
                    )
                
                # 2. Station-specific progress update for assembly line UI
                if self._websocket_available:
                    self.emit_station_progress(
                        self.session_id, 
                        self.block_id, 
                        station, 
                        'processing',
                        status_message
                    )
    
    def complete_station(self, station: str, station_name: str, errors_fixed: int, improvements: List[Dict] = None):
        """Complete a station with results tracking."""
        with self._lock:
            # Record completion time
            if station in self.station_start_times:
                duration = time.time() - self.station_start_times[station]
                self.station_durations[station] = duration
            else:
                duration = 0
            
            # Update station status
            self.station_progress[station] = {
                'status': 'completed',
                'progress': 100,
                'errors_fixed': errors_fixed,
                'duration': duration,
                'improvements': improvements or []
            }
            
            self.completed_stations += 1
            
            # Update pass progress
            if self.current_pass in self.pass_progress:
                self.pass_progress[self.current_pass]['stations_completed'] += 1
            
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress()
            
            logger.info(f"✅ Station {station_name} completed: {errors_fixed} errors fixed in {duration:.2f}s")
            
            # Emit BOTH types of completion updates
            # 1. General progress update
            self._emit_overall_progress(
                overall_progress,
                f"Pass {self.current_pass}: {station_name}",
                f"Completed - {errors_fixed} errors fixed"
            )
            
            # 2. Station-specific completion update for assembly line UI
            if self._websocket_available:
                self.emit_station_progress(
                    self.session_id, 
                    self.block_id, 
                    station, 
                    'complete',
                    f"Completed - {errors_fixed} errors fixed"
                )
    
    def complete_pass(self, pass_number: int):
        """Complete a processing pass."""
        with self._lock:
            if pass_number in self.pass_progress:
                self.pass_progress[pass_number]['status'] = 'completed'
                self.pass_progress[pass_number]['end_time'] = time.time()
                duration = self.pass_progress[pass_number]['end_time'] - self.pass_progress[pass_number]['start_time']
                
                pass_name = self.pass_progress[pass_number]['name']
                stations_completed = self.pass_progress[pass_number]['stations_completed']
                
                logger.info(f"🎉 Pass {pass_number} ({pass_name}) completed: {stations_completed} stations in {duration:.2f}s")
                
                # Calculate progress after pass completion
                overall_progress = self._calculate_overall_progress()
                
                self._emit_overall_progress(
                    overall_progress,
                    f"Pass {pass_number} Complete",
                    f"{pass_name} completed - {stations_completed} stations processed"
                )
    
    def complete_processing(self, total_errors_fixed: int, final_improvements: List[Dict] = None):
        """Complete all processing with final results."""
        with self._lock:
            total_duration = time.time() - self.start_time
            
            # Ensure all stations are marked as completed in station progress
            for station_key in self.station_progress.keys():
                if self.station_progress[station_key]['status'] != 'completed':
                    self.station_progress[station_key]['status'] = 'completed'
                    self.station_progress[station_key]['progress'] = 100
                    
                    # Send final completion signal for each station to UI
                    if self._websocket_available:
                        self.emit_station_progress(
                            self.session_id, 
                            self.block_id, 
                            station_key, 
                            'complete',
                            "Processing complete"
                        )
            
            # Generate performance summary
            performance_summary = {
                'total_duration': total_duration,
                'passes_completed': len([p for p in self.pass_progress.values() if p['status'] == 'completed']),
                'stations_completed': self.completed_stations,
                'total_errors_fixed': total_errors_fixed,
                'average_station_duration': sum(self.station_durations.values()) / len(self.station_durations) if self.station_durations else 0,
                'station_durations': self.station_durations,
                'improvements': final_improvements or []
            }
            
            logger.info(f"🏆 Processing complete: {total_errors_fixed} errors fixed across {self.completed_stations} stations in {total_duration:.2f}s")
            
            # Emit final completion with 100% progress
            self._emit_overall_progress(
                100,
                "Processing Complete",
                f"World-class AI rewriting complete - {total_errors_fixed} errors fixed"
            )
            
            return performance_summary
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle processing errors with progress updates."""
        with self._lock:
            error_message = f"Error in {context}: {str(error)}"
            logger.error(error_message)
            
            # Emit error progress
            self._emit_overall_progress(
                self._calculate_overall_progress(),
                "Processing Error",
                error_message
            )
            
            if self._websocket_available and self.current_station:
                self.emit_station_progress(
                    self.session_id, 
                    self.block_id, 
                    self.current_station, 
                    'error',
                    error_message
                )
    
    def _calculate_overall_progress(self) -> int:
        """Calculate overall progress percentage across all passes and stations."""
        if self.total_stations == 0 or self.total_passes == 0:
            return 0
        
        # Calculate progress within current pass
        pass_progress = 0
        if self.total_stations > 0:
            completed_stations_in_pass = sum(1 for station in self.station_progress.values() if station['status'] == 'completed')
            
            # Add progress from current station if it's processing
            current_station_progress = 0
            if self.current_station and self.current_station in self.station_progress:
                station_info = self.station_progress[self.current_station]
                if station_info['status'] == 'processing':
                    # For processing station, add 50% to show it's started
                    current_station_progress = 0.5
                elif station_info['status'] == 'completed':
                    # If current station is completed but not yet counted, count it
                    if completed_stations_in_pass == 0 or station_info not in [s for s in self.station_progress.values() if s['status'] == 'completed'][:-1]:
                        current_station_progress = 1.0
            
            pass_progress = (completed_stations_in_pass + current_station_progress) / self.total_stations
        
        # Calculate overall progress across all passes
        # For single-pass processing (which we're using), this is just the pass progress
        completed_passes = self.current_pass - 1
        overall_progress = ((completed_passes + pass_progress) / self.total_passes) * 100
        
        # Debug logging to help track progress calculation
        logger.debug(f"📊 Progress calculation: completed_stations={sum(1 for s in self.station_progress.values() if s['status'] == 'completed')}, current_station={self.current_station}, pass_progress={pass_progress:.2f}, overall={overall_progress:.1f}%")
        
        return min(int(overall_progress), 100)
    
    def _emit_overall_progress(self, progress: int, step: str, detail: str):
        """Emit overall progress update through multiple channels."""
        print(f"\n🔍 DEBUG PROGRESS EMIT:")
        print(f"   📊 Emitting progress: {progress}% - {step} - {detail}")
        print(f"   📋 session_id: {self.session_id} {'(will broadcast to all)' if not self.session_id else ''}")
        print(f"   📋 progress_callback available: {self.progress_callback is not None}")
        print(f"   📋 websocket_available: {self._websocket_available}")
        
        # Progress callback with correct signature
        if self.progress_callback:
            try:
                print(f"   📞 Calling progress_callback...")
                self.progress_callback(self.session_id, step, 'processing', detail, progress)
                print(f"   ✅ Progress callback executed successfully")
            except Exception as e:
                print(f"   ❌ Progress callback error: {e}")
                logger.error(f"Progress callback error: {e}")
        else:
            print(f"   ⚠️  No progress callback - skipping")
        
        # WebSocket progress - use empty string for broadcast if no session_id
        if self._websocket_available:
            try:
                print(f"   📡 Calling emit_progress WebSocket...")
                target_session = self.session_id if self.session_id else ''
                self.emit_progress(target_session, step, 'processing', detail, progress)
                print(f"   ✅ WebSocket progress emitted successfully to {'all sessions' if not target_session else target_session}")
            except Exception as e:
                print(f"   ❌ WebSocket progress error: {e}")
                logger.error(f"WebSocket progress error: {e}")
        else:
            print(f"   ⚠️  WebSocket not available - skipping")
        
        # Debug logging
        logger.debug(f"📊 Progress: {progress}% - {step} - {detail}")
        print(f"   ✅ Progress emit complete\n")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self._lock:
            current_time = time.time()
            return {
                'total_duration': current_time - self.start_time,
                'completed_stations': self.completed_stations,
                'total_stations': self.total_stations,
                'current_pass': self.current_pass,
                'total_passes': self.total_passes,
                'station_durations': self.station_durations.copy(),
                'pass_progress': {k: dict(v) for k, v in self.pass_progress.items()},
                'station_progress': {k: dict(v) for k, v in self.station_progress.items()},
                'overall_progress': self._calculate_overall_progress()
            }
