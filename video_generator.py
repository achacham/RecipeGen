import os
import json
import uuid
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import threading

from dotenv import load_dotenv

# Load environment
load_dotenv()

class VideoRecipeGenerator:
    def __init__(self):
        provider = os.getenv('USE_PROVIDER', 'fal')
        self.provider = provider.lower()
        
        # API key management
        self.api_keys = {
             'fal': os.getenv('FAL_KEY'),
        }
        
        self.api_key = self.api_keys.get('fal')
        
        print(f"🔌 Loaded video provider: {self.provider}")

        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Clear any previous state
        self.last_ingredients = []
        self.last_cuisine = ""

    def validate_and_clean_ingredients(self, ingredients: List[str]) -> List[str]:
        """
        VALIDATE and CLEAN ingredient list to prevent contamination
        """
        print(f"🧹 CLEANING INGREDIENTS INPUT: {ingredients}")
        
        # Clear previous state
        self.last_ingredients = []
        
        cleaned_ingredients = []
        
        for ingredient in ingredients:
            # Basic validation and cleaning
            ingredient = ingredient.strip()
            if ingredient:
                cleaned_ingredients.append(ingredient)
                print(f"✅ Validated ingredient: {ingredient}")
        
        self.last_ingredients = cleaned_ingredients
        print(f"🥘 FINAL VALIDATED INGREDIENTS: {cleaned_ingredients}")
        return cleaned_ingredients

    def generate_ingredient_specific_actions(self, ingredients: List[str], dish_type: str = "") -> List[str]:
        """
        DYNAMICALLY generate BRIEF cooking actions focused on cooking, not prep
        """
        actions = []

        # FUSION FIX: Ensure pasta is visible in pasta dishes
        if dish_type and 'pasta' in dish_type.lower():
            actions.append("cooking pasta noodles until al dente")
            
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # BRIEF actions focused on cooking application, not prep
            if any(fish in ingredient_lower for fish in ['salmon', 'tuna', 'cod', 'fish', 'trout']):
                actions.append(f"adding {ingredient} pieces to hot pan")
            elif any(liquid in ingredient_lower for liquid in ['sauce', 'oil', 'vinegar', 'wine', 'broth']):
                actions.append(f"drizzling {ingredient} over ingredients")
            elif any(herb in ingredient_lower for herb in ['scallion', 'onion', 'chive', 'green onion']):
                actions.append(f"tossing in chopped {ingredient}")
            elif any(spice in ingredient_lower for spice in ['garlic', 'ginger', 'shallot']):
                actions.append(f"adding minced {ingredient} to sizzling pan")
            elif any(veg in ingredient_lower for veg in ['tomato', 'pepper', 'carrot', 'celery']):
                actions.append(f"stirring in diced {ingredient}")
            elif any(meat in ingredient_lower for meat in ['chicken', 'beef', 'pork', 'lamb']):
                actions.append(f"searing {ingredient} pieces in hot oil")
            else:
                actions.append(f"incorporating {ingredient} into the cooking")
        
        # FUSION FIX: Add pasta combining step for pasta dishes
        if dish_type and 'pasta' in dish_type.lower():
            actions.append("tossing cooked pasta with all the prepared ingredients")
        
        return actions

    def generate_cuisine_audio(self, cuisine: str) -> str:
        """
        EXACT WORKING PATTERN: Match successful examples dynamically
        """
        cuisine_lower = cuisine.lower()
        
        # Specific cooking sound effects
        cooking_sounds = f"sizzling, rhythmic chopping, aromatic steam rising, {cuisine_lower} cooking ambiance"
        
        # Descriptive orchestral score with cultural mood (like the working examples)
        orchestral_score = f"a warm, traditional {cuisine_lower} orchestral score with cultural instruments, melodic and inviting rhythm"
        
        return f"Audio: sizzling, rhythmic chopping, aromatic steam rising, a warm, traditional {cuisine_lower} orchestral score with cultural instruments, melodic and inviting rhythm"
    
    def build_dynamic_cuisine_prompt(self, cuisine: str, ingredients: List[str], dish_type: str, enable_audio: bool = True) -> str:
        """
        BUILD COOKING-FOCUSED cuisine-specific prompts with CONDITIONAL audio
        """
        ingredient_list = ", ".join(ingredients)
        
        print(f"🏗️  BUILDING COOKING-FOCUSED PROMPT FOR: {cuisine} with {ingredient_list} (Audio: {enable_audio})")
        
        # Store dish_type for pasta fusion fix
        self._current_dish_type = dish_type
        
        # Generate BRIEF ingredient actions focused on cooking
        ingredient_actions = self.generate_ingredient_specific_actions(ingredients, dish_type)
        
        # DYNAMIC cuisine description
        cuisine_name = cuisine.title() if cuisine else "International"
        
        # Build dynamic character and environment descriptions
        if cuisine and cuisine.lower() != "international":
            character_desc = f"an experienced {cuisine_name} chef with visible warm face and traditional cooking attire"
            kitchen_desc = f"authentic {cuisine_name} kitchen with traditional cookware and cultural elements"
            style_desc = f"traditional {cuisine_name} cooking techniques"
            # CONDITIONAL AUDIO: Only generate if audio enabled
            if enable_audio:
                audio_desc = self.generate_cuisine_audio(cuisine.lower())
                audio_section = f"MANDATORY AUDIO: {audio_desc}. "
            else:
                audio_section = ""
        else:
            character_desc = "a skilled professional chef with clearly visible face and expert movements"
            kitchen_desc = "modern professional kitchen with quality equipment"
            style_desc = "expert international cooking techniques"
            if enable_audio:
                audio_section = "MANDATORY AUDIO: professional kitchen sounds: intense sizzling, aromatic steaming, gentle cooking ambiance. "
            else:
                audio_section = ""
        
        # BUILD COOKING-FOCUSED PROMPT with CONDITIONAL AUDIO
        prompt = (
            f"A cinematic cooking scene in {kitchen_desc} showing {character_desc} "
            f"preparing {dish_type} using {ingredient_list}. "
            f"BRIEF ingredient prep, then IMMEDIATE cooking: {', '.join(ingredient_actions[:3])} "
            f"in hot wok/pan with intense sizzling and steam. "
            f"Chef expertly tosses and stirs ingredients with {style_desc}. "
            f"Video focuses on the active cooking with beautiful sizzling sounds and aromatic steam rising. "
            f"Ends with gorgeous bubbling, sizzling cooking scene showing perfectly cooked dish. "
            f"Chef's face clearly visible with focused cooking expression. "
            f"{audio_section}"
            f"Warm lighting, authentic cultural atmosphere, professional cooking action."
        )
        
        print(f"📝 GENERATED CONDITIONAL PROMPT: {prompt}")
        return prompt

    def call_fal_api(self, prompt: str, duration: int, cuisine: str = "", ingredients: List[str] = None, 
                    use_fast_model: bool = False, enable_audio: bool = True, 
                    enhance_prompt: bool = False) -> Tuple[bool, str]:
        """
        FIXED: Correct model selection and dynamic audio parameters for MPP
        """
        try:
            import fal_client
            
            if ingredients is None:
                ingredients = []
            
            # Configure fal client
            fal_client.api_key = self.api_keys['fal']
            
            # FIXED: Correct model selection logic
            if use_fast_model:
                model = "fal-ai/veo3/fast"
                audio_param = "audio_enabled"
            else:
                model = "fal-ai/veo3"  # Standard VEO3 for MPP
                audio_param = "generate_audio"
            
            # === DEBUGGING SECTION ===
            print(f"\n🔍 === MPP AUDIO FIX DEBUG ===")
            print(f"INPUT CUISINE: '{cuisine}'")
            print(f"INPUT INGREDIENTS: {ingredients}")
            print(f"MODEL: {model}")
            print(f"AUDIO PARAMETER: {audio_param} = {enable_audio}")
            print(f"PROMPT LENGTH: {len(prompt)} characters")
            print(f"=== END DEBUG ===\n")

            print(f"🎬 CALLING FAL AI ({model}) FOR MPP")
            print(f"🌍 FOR CUISINE: {cuisine}")
            print(f"🥘 WITH INGREDIENTS: {ingredients}")
            print(f"🔊 AUDIO: {enable_audio} using {audio_param}")

            # FIXED: Dynamic audio parameter based on model
            arguments = {
                "prompt": prompt,
                "duration": "8s",
                "aspect_ratio": "16:9",
                "enhance_prompt": enhance_prompt,
            }
            
            # Add correct audio parameter based on model
            arguments[audio_param] = enable_audio
            
            print(f"🔧 MPP PARAMETERS: {arguments}")
            
            # PERFORMANCE MEASUREMENT + API CALL
            start_time = time.time()
            result = fal_client.submit(model, arguments=arguments)
            output = result.get()
            generation_time = time.time() - start_time
            
            print(f"⏱️ TOTAL GENERATION TIME: {generation_time:.2f} seconds")
            print(f"📦 API RESPONSE KEYS: {list(output.keys()) if isinstance(output, dict) else type(output)}")
            
            video_url = output.get("video", {}).get("url") if isinstance(output, dict) else None
            
            if video_url:
                print(f"✅ MPP SUCCESS! Video URL: {video_url}")
                print(f"🎵 AUDIO TEST: Check if video has sound with {audio_param}")
                return True, video_url
            else:
                print(f"❌ NO VIDEO URL IN RESPONSE: {output}")
                return False, f"No video URL in response: {output}"
                
        except Exception as e:
            print(f"💥 API ERROR: {str(e)}")
            return False, f"Fal API error: {str(e)}"

    def call_fal_api_async(self, prompt: str, webhook_url: Optional[str] = None, 
                          use_fast_model: bool = False, enable_audio: bool = True) -> Tuple[bool, str]:
        """
        FIXED: Async processing with correct model selection and audio parameters
        """
        try:
            import fal_client
            
            fal_client.api_key = self.api_keys['fal']
            
            # FIXED: Correct model selection logic
            if use_fast_model:
                model = "fal-ai/veo3/fast"
                audio_param = "audio_enabled"
            else:
                model = "fal-ai/veo3"  # Standard VEO3 for MPP
                audio_param = "generate_audio"
            
            print(f"🚀 Submitting async request to {model} for MPP...")
            
            arguments = {
                "prompt": prompt,
                "duration": "8s",
                "aspect_ratio": "16:9",
                "enhance_prompt": False,
            }
            
            # Add correct audio parameter based on model
            arguments[audio_param] = enable_audio
            
            queue_result = fal_client.queue.submit(
                model,
                arguments=arguments,
                webhook_url=webhook_url
            )
            
            request_id = queue_result.get("request_id")
            
            if request_id:
                print(f"📋 Request queued with ID: {request_id}")
                return True, request_id
            else:
                return False, "Failed to queue request"
                
        except Exception as e:
            return False, f"Async API error: {str(e)}"

    def get_async_result(self, request_id: str, use_fast_model: bool = False) -> Tuple[bool, Dict]:
        """
        FIXED: Check status with correct model endpoint
        """
        try:
            import fal_client
            
            fal_client.api_key = self.api_keys['fal']
            
            # Use correct model endpoint
            model = "fal-ai/veo3/fast" if use_fast_model else "fal-ai/veo3"
            
            status = fal_client.queue.status(model, request_id=request_id)
            
            if status.get("status") == "COMPLETED":
                result = fal_client.queue.result(model, request_id=request_id)
                return True, result
            else:
                return False, {"status": status.get("status", "UNKNOWN"), "request_id": request_id}
                
        except Exception as e:
            return False, {"error": f"Status check failed: {str(e)}"}

    def download_video(self, url: str, filename: str) -> Tuple[bool, str]:
        """Download video with progress tracking"""
        try:
            output_path = self.output_dir / filename
            print(f"📥 Downloading {filename}...")
            
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)  
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📊 Download progress: {progress:.1f}%", end="", flush=True)
            
            print(f"\n💾 Download complete: {output_path}")
            return True, str(output_path)
            
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def generate_video(self, cuisine: str, ingredients: List[str], **kwargs) -> Dict:
        """
        MPP: Generate video with STANDARD VEO3 by default for maximum audio performance
        """
        print(f"\n🚀 === STARTING MPP VIDEO GENERATION ===")
        print(f"🌍 CUISINE: {cuisine}")
        print(f"🥘 RAW INGREDIENTS: {ingredients}")
        
        # CRITICAL: Validate and clean ingredients to prevent contamination
        validated_ingredients = self.validate_and_clean_ingredients(ingredients)
        
        generation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Parameters - DEFAULT TO STANDARD VEO3 FOR MPP
        dish_type = kwargs.get('dish_type', 'dish')
        use_fast_model = kwargs.get('use_fast_model', False)  # CHANGED: Default to False for MPP
        enable_audio = kwargs.get('enable_audio', True)  # MANDATORY for cuisine-specific audio
        enhance_prompt = kwargs.get('enhance_prompt', False)
        async_mode = kwargs.get('async_mode', False)
        
        # Build COOKING-FOCUSED cuisine-specific prompt with CONDITIONAL audio
        prompt = self.build_dynamic_cuisine_prompt(cuisine, validated_ingredients, dish_type, enable_audio)
        
        print(f"⚡ MPP SETTINGS:")
        print(f"   - Cuisine: {cuisine}")
        print(f"   - Ingredients: {validated_ingredients}")
        print(f"   - Audio: {enable_audio} (MANDATORY)")
        print(f"   - Fast Model: {use_fast_model} (MPP uses Standard VEO3)")

        success = False
        video_url = ""
        error_message = ""
        request_id = None
        
        # Generate video
        if self.provider == 'fal':
            if async_mode:
                success, result = self.call_fal_api_async(
                    prompt, 
                    use_fast_model=use_fast_model, 
                    enable_audio=enable_audio
                )
                if success:
                    request_id = result
                    print(f"📋 Async request submitted: {request_id}")
                else:
                    error_message = result
            else:
                success, result = self.call_fal_api(
                    prompt, 8, cuisine, validated_ingredients,
                    use_fast_model=use_fast_model,
                    enable_audio=enable_audio,
                    enhance_prompt=enhance_prompt
                )
                if success:
                    video_url = result
                    print(f"🎉 MPP VIDEO WITH FULL AUDIO GENERATED!")
                else:
                    error_message = result
                    print(f"💥 GENERATION FAILED: {error_message}")

        # Download if successful (sync mode only)
        local_path = ""
        if success and video_url and not async_mode:
            filename = f"{cuisine}_{'-'.join(validated_ingredients[:2])}_{generation_id[:8]}.mp4"
            dl_success, local_path_or_err = self.download_video(video_url, filename)
            if dl_success:
                local_path = local_path_or_err

        # Return comprehensive result
        return {
            "generation_id": generation_id,
            "timestamp": timestamp,
            "cuisine": cuisine,
            "ingredients": validated_ingredients,
            "parameters": kwargs,
            "prompt": prompt,
            "success": success,
            "video_url": video_url if success and not async_mode else None,
            "request_id": request_id if async_mode else None,
            "local_path": local_path or None,
            "error": error_message if not success else None,
            "provider": self.provider,
            "performance_settings": {
                "fast_model": use_fast_model,
                "audio_enabled": enable_audio,
                "prompt_enhanced": enhance_prompt,
                "async_mode": async_mode,
                "mpp_mode": "Standard VEO3 for Maximum Audio Performance"
            }
        }

    def check_async_status(self, request_id: str, use_fast_model: bool = False) -> Dict:
        """
        FIXED: Check the status with correct model endpoint
        """
        success, result = self.get_async_result(request_id, use_fast_model)
        
        if success:
            if isinstance(result, dict) and "video" in result:
                video_url = result["video"]["url"]
                return {
                    "status": "COMPLETED",
                    "video_url": video_url,
                    "result": result
                }
            else:
                return {
                    "status": result.get("status", "IN_PROGRESS"),
                    "request_id": request_id
                }
        else:
            return {
                "status": "ERROR",
                "error": result.get("error", "Unknown error"),
                "request_id": request_id
            }