"""
Async Worker for Video Generation
Polls pending tasks and manages background video generation
"""

import time
import threading
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from database import db
from video_generator import VideoRecipeGenerator

logger = logging.getLogger(__name__)

class AsyncVideoWorker:
    def __init__(self, poll_interval=5):
        self.poll_interval = poll_interval
        self.running = False
        self.thread = None
        self.generator = VideoRecipeGenerator()
        
    def start(self):
        """Start the async worker thread"""
        if self.running:
            logger.warning("Async worker already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        logger.info("🚀 Async video worker started")
        
    def stop(self):
        """Stop the async worker"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("🛑 Async video worker stopped")
        
    def _worker_loop(self):
        """Main worker loop - polls for pending tasks"""
        print("🔍 DEBUG: Worker loop started!")
        while self.running:
            try:
                # Get pending tasks
                pending_tasks = db.get_pending_tasks()
                
                # Safe debug print
                task_count = len(pending_tasks) if pending_tasks else 0
                print(f"🔍 DEBUG: Check complete - found {task_count} tasks")
                
                if pending_tasks:
                    logger.info(f"📋 Found {len(pending_tasks)} pending tasks")
                    
                    for task in pending_tasks:
                        if not self.running:
                            break
                            
                        self._process_task(task)
                        
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                    
            # Sleep before next poll
            time.sleep(self.poll_interval)
    
    def _process_task(self, task):
        """Process a single video generation task"""
        task_id = task['task_id']
        print(f"🔍 DEBUG: Processing task {task_id}, status: {task.get('status')}")
        
        try:
            # Check if task is stuck (processing for too long)
            if task['status'] == 'processing':
                started_at = datetime.fromisoformat(task['started_at'])
                if datetime.now() - started_at > timedelta(minutes=10):
                    logger.warning(f"Task {task_id} stuck, resetting to pending")
                    db.update_task_status(task_id, 'pending')
                    return
            
            # For KIE provider - check if already submitted
            if task['status'] == 'processing' and task.get('provider_task_id'):
                # Poll KIE for status
                self._check_kie_status(task)
                return
            
            # Start new generation
            if task['status'] == 'pending':
                self._start_generation(task)
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            db.update_task_status(
                task_id, 
                'failed',
                error_message=str(e)
            )
    
    def _start_generation(self, task):
        """Start video generation for a task"""
        task_id = task['task_id']
        recipe_id = task['recipe_id']
        
        print(f"🔍 DEBUG: Starting generation for {task_id}")
        logger.info(f"🎬 Starting generation for task {task_id}")
        
        # Update status
        db.update_task_status(task_id, 'processing')
        
        try:
            # Parse ingredients from JSON
            import json
            ingredients = json.loads(task['ingredients'])
            
            # STEP 1: Generate recipe text with SIMPLE TEMPLATE (skip OpenAI)
            logger.info(f"📝 Generating recipe text for {task_id}")
            
            ingredient_names = ingredients  # Already a list of names
            recipe_text = f"""
{task['cuisine'].title()} {task.get('dish_type', 'Dish')}

Ingredients:
{chr(10).join(f'- {ing}' for ing in ingredient_names)}

Instructions:
1. Prepare all ingredients
2. Heat oil in a pan
3. Cook {ingredient_names[0]} until golden
4. Add remaining ingredients
5. Season to taste
6. Serve hot

Enjoy your delicious {task['cuisine']} {task.get('dish_type', 'dish')}!
"""
            
            logger.info(f"✅ Recipe template created (skipping OpenAI)")
            
            # STEP 2: Update recipe in database
            logger.info(f"💾 Saving recipe text for {recipe_id}")
            with sqlite3.connect('recipegen.db') as conn:
                conn.execute('''
                    UPDATE recipes 
                    SET recipe_text = ?
                    WHERE recipe_id = ?
                ''', (recipe_text, recipe_id))
            
            # STEP 3: Generate video
            logger.info(f"🎥 Generating video for task {task_id}")
            result = self.generator.generate_video(
                cuisine=task['cuisine'],
                ingredients=ingredients,
                dish_type=task.get('dish_type', 'dish'),
                use_fast_model=True,
                enable_audio=True,
                async_mode=True  # Use async mode for KIE
            )

            # Track prompt usage
            if self.generator.current_template_id:
                from prompt_evolution import prompt_evolution
                prompt_evolution.record_video_result(task_id, self.generator.current_template_id)
                logger.info(f"📊 Tracking prompt template #{self.generator.current_template_id}")
            
            if result['success'] and result.get('request_id'):
                # Store provider's task ID for polling
                db.update_task_status(
                    task_id,
                    'processing',
                    provider_task_id=result['request_id']
                )
                logger.info(f"📝 Task {task_id} submitted to provider: {result['request_id']}")
            else:
                raise Exception(result.get('error', 'Unknown error'))
                
        except Exception as e:
            logger.error(f"Generation failed for {task_id}: {e}")
            db.update_task_status(
                task_id,
                'failed',
                error_message=str(e)
            )
    
    def _check_kie_status(self, task):
        """Check status of KIE generation"""
        task_id = task['task_id']
        provider_task_id = task['provider_task_id']
        
        try:
            # Check status with provider
            status_result = self.generator.check_async_status(provider_task_id)
            
            if status_result['status'] == 'COMPLETED':
                video_url = status_result.get('video_url')
                print(f"🎥 DEBUG: Video ready at URL: {video_url}")
                
                # Download video
                import uuid
                filename = f"{task['cuisine']}_{task_id[:8]}.mp4"
                print(f"💾 DEBUG: Attempting download to: {filename}")
                
                success, local_path = self.generator.download_video(video_url, filename)
                
                if success:
                    print(f"✅ DEBUG: Download successful to: {local_path}")
                    # Update database
                    db.update_task_status(
                        task_id,
                        'completed',
                        video_url=video_url,
                        local_path=local_path,
                        credits_used=400  # KIE uses 400 credits
                    )
                    logger.info(f"✅ Task {task_id} completed!")
                    # Update prompt success metrics
                    from prompt_evolution import prompt_evolution
                    prompt_evolution.update_video_success(task_id, True)
                else:
                    print(f"❌ DEBUG: Download failed with error: {local_path}")
                    raise Exception(f"Download failed: {local_path}")
                        
            elif status_result['status'] == 'ERROR':
                raise Exception(status_result.get('error', 'Generation failed'))
                    
            # Still processing - will check again next poll
                
        except Exception as e:
            logger.error(f"Status check failed for {task_id}: {e}")
            db.update_task_status(
                task_id,
                'failed',
                error_message=str(e)
            )

# Global worker instance
worker = AsyncVideoWorker()