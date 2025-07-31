import ffmpeg
import requests
import json
import os
import logging
from flask import Blueprint, request, jsonify, send_file, Response, stream_template
from datetime import datetime
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from database import db
import uuid

# Add the current directory to Python path to import your AI modules
sys.path.append(str(Path(__file__).parent))

try:
    from video_generator import VideoRecipeGenerator
    FAL_AI_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import VideoRecipeGenerator: {e}")
    FAL_AI_AVAILABLE = False
    
video_bp = Blueprint('video', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# MPP OPTIMIZATION: Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

# MPP OPTIMIZATION: Cache for pending async requests
pending_requests = {}
request_lock = threading.Lock()

# Load ingredients data for slug-to-name conversion
def load_ingredients():
    try:
        with open("data/ingredients.json", "r", encoding="utf-8") as f:
            ingredients_list = json.load(f)
            return {item["slug"]: item for item in ingredients_list}
    except Exception as e:
        logger.error(f"Failed to load ingredients: {e}")
        return {}

# Load dish types data for cooking actions
def load_dish_types():
    try:
        with open("data/dish_types.json", "r", encoding="utf-8") as f:
            dish_types_list = json.load(f)
            return {item["id"]: item for item in dish_types_list}
    except Exception as e:
        logger.error(f"Failed to load dish types: {e}")
        return {}

INGREDIENTS_BY_SLUG = load_ingredients()
DISH_TYPES_BY_ID = load_dish_types()

def convert_ingredients(ingredient_slugs):
    """MPP HELPER: Efficiently convert ingredient slugs to names"""
    ingredient_names = []
    for slug in ingredient_slugs:
        ing = INGREDIENTS_BY_SLUG.get(slug)
        if ing:
            ingredient_names.append(ing['name'])
        else:
            ingredient_names.append(slug.title())  # Fallback formatting
    return ingredient_names

def stream_video_from_url(video_url):
    """MPP OPTIMIZATION: Stream video directly without local storage"""
    try:
        response = requests.get(video_url, stream=True, timeout=120)
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
                
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        yield b""

# === MPP OPTIMIZED FLASK ROUTES ===

@video_bp.route('/generate_video_fast', methods=['POST'])
def generate_video_fast():
    """
    MPP OPTIMIZED: Generate video using VEO3/FAST model with maximum performance settings
    - 2x faster generation speed
    - 80% cost reduction
    - 33% speed boost with audio disabled
    """
    
    try:
        data = request.get_json(force=True) or {}
        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine", "")
        dish_type = data.get("dish_type", "")
        
        # Generate unique IDs for tracking
        recipe_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        logger.info(f"🎬 Legacy FAL AI Video generation (MPP enabled): "
                   f"ingredients={ingredients}, cuisine={cuisine}, dish_type={dish_type}")
        
        if not ingredients:
            return jsonify({"error": "Missing ingredients list", "success": False}), 400
        
        if not FAL_AI_AVAILABLE:
            return jsonify({"error": "FAL AI system not available", "success": False}), 500
        
        # Convert ingredient slugs to names efficiently
        ingredient_names = convert_ingredients(ingredients)
        logger.info(f"🥘 Converted ingredients: {ingredient_names}")
        
        # Use dish type name for better prompts
        dish_name = dish_type
        if dish_type and DISH_TYPES_BY_ID.get(dish_type):
            dish_name = DISH_TYPES_BY_ID[dish_type]['name']
        
        # Initialize generator with MPP settings
        try:
            generator = VideoRecipeGenerator()
            
            # Build prompt first (we'll need it for the database)
            prompt = generator.build_dynamic_cuisine_prompt(
                cuisine or "international",
                ingredient_names,
                dish_name,
                enable_audio=True  # KIE needs this
            )
            
            # CREATE DATABASE RECORD BEFORE GENERATION
            db_id = db.create_video_task(
                task_id=task_id,
                recipe_id=recipe_id,
                cuisine=cuisine or "international",
                ingredients=ingredient_names,
                dish_type=dish_name,
                prompt=prompt,
                provider=generator.provider  # 'kie' or 'fal'
            )
            
            logger.info(f"📊 Created database task: {task_id}")
            
            # Update status to processing
            db.update_task_status(task_id, 'processing')
            
            # MPP ENABLED FOR LEGACY COMPATIBILITY
            result = generator.generate_video(
                cuisine=cuisine or "international",
                ingredients=ingredient_names,
                dish_type=dish_name,
                use_fast_model=True,      # MPP: Use fast model
                enable_audio=True,        # Force True for KIE
                enhance_prompt=False,     # MPP: Disable enhancement for speed
                async_mode=False          # Sync for legacy compatibility
            )
            
            logger.info(f"🎯 MPP FAL AI generation result: {result['success']}")
            
            if result['success']:
                # Update database with success
                generation_time = result.get('generation_time_seconds', 0)
                db.update_task_status(
                    task_id, 
                    'completed',
                    video_url=result.get('video_url'),
                    local_path=result.get('local_path'),
                    generation_time_seconds=generation_time,
                    credits_used=400 if generator.provider == 'kie' else 0  # KIE uses 400 credits
                )
                
                if result.get('local_path'):
                    logger.info(f"✅ Video ready at: {result['local_path']}")
                    return send_file(
                        result['local_path'], 
                        mimetype='video/mp4',
                        as_attachment=False,
                        download_name=f'recipegen_mpp_cooking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
                    )
                elif result.get('video_url'):
                    # If no local path but we have URL, stream it
                    video_url = result['video_url']
                    return Response(
                        stream_video_from_url(video_url),
                        mimetype='video/mp4',
                        headers={
                            'Content-Disposition': f'inline; filename=recipegen_mpp_cooking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                            'X-Generation-Mode': 'MPP-Legacy',
                            'X-Task-ID': task_id
                        }
                    )
            else:
                error_msg = result.get('error', 'Unknown FAL AI error')
                logger.error(f"❌ FAL AI generation failed: {error_msg}")
                
                # Update database with failure
                db.update_task_status(
                    task_id,
                    'failed',
                    error_message=error_msg
                )
                
                return jsonify({
                    "error": f"FAL AI generation failed: {error_msg}",
                    "success": False,
                    "task_id": task_id
                }), 500
            
        except Exception as e:
            logger.error(f"❌ FAL AI system error: {e}")
            
            # Update database with error
            if 'task_id' in locals():
                db.update_task_status(
                    task_id,
                    'failed',
                    error_message=str(e)
                )
            
            return jsonify({
                "error": f"FAL AI system unavailable: {str(e)}", 
                "success": False
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        return jsonify({
            "error": "Video generation failed", 
            "details": str(e),
            "success": False
        }), 500

@video_bp.route('/generate_video_async', methods=['POST'])
def generate_video_async():
    """
    MPP OPTIMIZATION: Async video generation with webhooks for maximum performance
    """
    
    try:
        data = request.get_json(force=True) or {}
        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine", "")
        dish_type = data.get("dish_type", "")
        
        # MPP OPTIONS
        enable_audio = data.get("enable_audio", False)
        use_fast_model = data.get("use_fast_model", True)
        
        logger.info(f"🚀 MPP Async Video generation: ingredients={ingredients}")
        
        if not ingredients:
            return jsonify({"error": "Missing ingredients list", "success": False}), 400
        
        if not FAL_AI_AVAILABLE:
            return jsonify({"error": "FAL AI system not available", "success": False}), 500
        
        # Convert ingredients efficiently
        ingredient_names = convert_ingredients(ingredients)
        
        # Use dish type name
        dish_name = dish_type
        if dish_type and DISH_TYPES_BY_ID.get(dish_type):
            dish_name = DISH_TYPES_BY_ID[dish_type]['name']
        
        # Initialize generator and submit async request
        try:
            generator = VideoRecipeGenerator()
            
            # Submit async request
            result = generator.generate_video(
                cuisine=cuisine or "international",
                ingredients=ingredient_names,
                dish_type=dish_name,
                use_fast_model=use_fast_model,
                enable_audio=enable_audio,
                enhance_prompt=False,
                async_mode=True  # Enable async processing
            )
            
            if result['success'] and result.get('request_id'):
                request_id = result['request_id']
                
                # Store request info for status checking
                with request_lock:
                    pending_requests[request_id] = {
                        'ingredients': ingredient_names,
                        'cuisine': cuisine,
                        'dish_type': dish_name,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'QUEUED'
                    }
                
                logger.info(f"📋 Async request submitted: {request_id}")
                
                return jsonify({
                    "success": True,
                    "request_id": request_id,
                    "status": "QUEUED",
                    "message": "Video generation queued for processing"
                })
            else:
                error_msg = result.get('error', 'Failed to queue request')
                return jsonify({
                    "error": error_msg,
                    "success": False
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Async submission failed: {e}")
            return jsonify({
                "error": f"Async submission failed: {str(e)}",
                "success": False
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Async video generation failed: {e}")
        return jsonify({
            "error": "Async video generation failed",
            "details": str(e),
            "success": False
        }), 500

@video_bp.route('/video_status/<request_id>', methods=['GET'])
def get_video_status(request_id):
    """
    MPP OPTIMIZATION: Check status of async video generation
    """
    
    try:
        if not FAL_AI_AVAILABLE:
            return jsonify({"error": "FAL AI system not available", "success": False}), 500
        
        # Check if request exists in our pending list
        with request_lock:
            request_info = pending_requests.get(request_id)
        
        if not request_info:
            return jsonify({
                "error": "Request ID not found",
                "success": False
            }), 404
        
        # Check actual status from FAL AI
        try:
            generator = VideoRecipeGenerator()
            status_result = generator.check_async_status(request_id)
            
            if status_result['status'] == 'COMPLETED':
                # Video is ready
                video_url = status_result.get('video_url')
                
                # Update our tracking
                with request_lock:
                    if request_id in pending_requests:
                        pending_requests[request_id]['status'] = 'COMPLETED'
                        pending_requests[request_id]['video_url'] = video_url
                
                return jsonify({
                    "success": True,
                    "status": "COMPLETED",
                    "video_url": video_url,
                    "request_id": request_id,
                    "request_info": request_info
                })
            
            elif status_result['status'] == 'ERROR':
                # Generation failed
                with request_lock:
                    if request_id in pending_requests:
                        pending_requests[request_id]['status'] = 'ERROR'
                
                return jsonify({
                    "success": False,
                    "status": "ERROR",
                    "error": status_result.get('error', 'Generation failed'),
                    "request_id": request_id
                })
            
            else:
                # Still processing
                return jsonify({
                    "success": True,
                    "status": status_result['status'],
                    "request_id": request_id,
                    "message": "Video generation in progress"
                })
                
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return jsonify({
                "error": f"Status check failed: {str(e)}",
                "success": False
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Video status check failed: {e}")
        return jsonify({
            "error": "Status check failed",
            "details": str(e),
            "success": False
        }), 500

@video_bp.route('/generate_video', methods=['POST'])
def generate_video():
    """
    LEGACY ENDPOINT: Updated with MPP optimizations for backward compatibility
    """
    
    try:
        data = request.get_json(force=True) or {}
        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine", "")
        dish_type = data.get("dish_type", "")
        
        # Enable MPP optimizations by default for legacy endpoint
        logger.info(f"🎬 Legacy FAL AI Video generation (MPP enabled): "
                   f"ingredients={ingredients}, cuisine={cuisine}, dish_type={dish_type}")
        
        if not ingredients:
            return jsonify({"error": "Missing ingredients list", "success": False}), 400
        
        if not FAL_AI_AVAILABLE:
            return jsonify({"error": "FAL AI system not available", "success": False}), 500
        
        # Convert ingredient slugs to names efficiently
        ingredient_names = convert_ingredients(ingredients)
        logger.info(f"🥘 Converted ingredients: {ingredient_names}")
        
        # Use dish type name for better prompts
        dish_name = dish_type
        if dish_type and DISH_TYPES_BY_ID.get(dish_type):
            dish_name = DISH_TYPES_BY_ID[dish_type]['name']
        
        # Initialize generator with MPP settings
        try:
            generator = VideoRecipeGenerator()
            
            # MPP ENABLED FOR LEGACY COMPATIBILITY
            result = generator.generate_video(
                cuisine=cuisine or "international",
                ingredients=ingredient_names,
                dish_type=dish_name,
                use_fast_model=True,      # MPP: Use fast model
                enable_audio=False,       # MPP: Disable audio for speed
                enhance_prompt=False,     # MPP: Disable enhancement for speed
                async_mode=False          # Sync for legacy compatibility
            )
            
            logger.info(f"🎯 MPP FAL AI generation result: {result['success']}")
            
            if result['success'] and result.get('local_path'):
                logger.info(f"✅ Video ready at: {result['local_path']}")
                return send_file(
                    result['local_path'], 
                    mimetype='video/mp4',
                    as_attachment=False,
                    download_name=f'recipegen_mpp_cooking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
                )
            elif result['success'] and result.get('video_url'):
                # If no local path but we have URL, stream it
                video_url = result['video_url']
                return Response(
                    stream_video_from_url(video_url),
                    mimetype='video/mp4',
                    headers={
                        'Content-Disposition': f'inline; filename=recipegen_mpp_cooking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                        'X-Generation-Mode': 'MPP-Legacy'
                    }
                )
            else:
                error_msg = result.get('error', 'Unknown FAL AI error')
                logger.error(f"❌ FAL AI generation failed: {error_msg}")
                return jsonify({
                    "error": f"FAL AI generation failed: {error_msg}",
                    "success": False
                }), 500
            
        except Exception as e:
            logger.error(f"❌ FAL AI system error: {e}")
            return jsonify({
                "error": f"FAL AI system unavailable: {str(e)}", 
                "success": False
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        return jsonify({
            "error": "Video generation failed", 
            "details": str(e),
            "success": False
        }), 500

@video_bp.route('/stream_video/<request_id>', methods=['GET'])
def stream_video_result(request_id):
    """
    MPP OPTIMIZATION: Stream completed async video directly
    """
    try:
        with request_lock:
            request_info = pending_requests.get(request_id)
        
        if not request_info:
            return jsonify({"error": "Request ID not found"}), 404
        
        if request_info['status'] != 'COMPLETED':
            return jsonify({"error": "Video not ready yet"}), 202
        
        video_url = request_info.get('video_url')
        if not video_url:
            return jsonify({"error": "Video URL not available"}), 500
        
        return Response(
            stream_video_from_url(video_url),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'inline; filename=recipegen_async_{request_id[:8]}.mp4',
                'X-Generation-Mode': 'MPP-Async'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Stream video failed: {e}")
        return jsonify({"error": "Stream failed", "details": str(e)}), 500

# Fallback route for legacy compatibility
@video_bp.route('/video', methods=['POST'])
def generate_video_legacy():
    """Legacy endpoint - redirects to optimized generate_video"""
    return generate_video()

# MPP WEBHOOK ENDPOINT (Optional for advanced async processing)
@video_bp.route('/webhook/video_complete', methods=['POST'])
def handle_video_webhook():
    """
    MPP OPTIMIZATION: Handle webhook notifications from FAL AI
    """
    try:
        webhook_data = request.get_json()
        request_id = webhook_data.get('request_id')
        status = webhook_data.get('status')
        
        logger.info(f"📨 Webhook received for {request_id}: {status}")
        
        if request_id and status == 'COMPLETED':
            video_url = webhook_data.get('data', {}).get('video', {}).get('url')
            
            # Update our tracking
            with request_lock:
                if request_id in pending_requests:
                    pending_requests[request_id]['status'] = 'COMPLETED'
                    pending_requests[request_id]['video_url'] = video_url
                    pending_requests[request_id]['completed_at'] = datetime.now().isoformat()
            
            # Here you could implement real-time notifications to frontend
            # via WebSocket, Server-Sent Events, etc.
            
        return '', 200
        
    except Exception as e:
        logger.error(f"❌ Webhook handling failed: {e}")
        return '', 500

# MPP STATUS ENDPOINT
@video_bp.route('/mpp_status', methods=['GET'])
def get_mpp_status():
    """
    MPP OPTIMIZATION: Get overall system performance status
    """
    try:
        with request_lock:
            total_requests = len(pending_requests)
            completed = len([r for r in pending_requests.values() if r['status'] == 'COMPLETED'])
            in_progress = len([r for r in pending_requests.values() if r['status'] in ['QUEUED', 'IN_PROGRESS']])
        
        return jsonify({
            "mpp_enabled": True,
            "fal_ai_available": FAL_AI_AVAILABLE,
            "total_requests": total_requests,
            "completed": completed,
            "in_progress": in_progress,
            "performance_mode": "Maximum Possible Performance (MPP)",
            "optimizations": [
                "VEO3/FAST Model (2x speed)",
                "Audio Disabled (33% speed boost)",
                "Prompt Enhancement Disabled",
                "Direct Streaming",
                "Async Processing Available"
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500