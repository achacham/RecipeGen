import os
import json
import uuid
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import threading
from prompt_evolution import prompt_evolution
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Provider configurations
PROVIDER_CONFIGS = {
   'fal': {
       'name': 'FAL AI',
       'base_url': 'https://queue.fal.run',
       'headers': {
           'Authorization': 'Key {api_key}',
           'Content-Type': 'application/json'
       },
       'cost_per_second': 0.75,  # $6.00 for 8s
       'supports_audio': True,
       'max_duration': 8,
       'models': ['veo3', 'veo3/fast']
   },
   'kie': {
       'name': 'KIE AI',
       'base_url': 'https://api.kie.ai/api/v1',
       'headers': {
           'Authorization': 'Bearer {api_key}',
           'Content-Type': 'application/json'
       },
       'cost_per_second': 0.05,  # $0.40 for 8s (Fast mode)
       'supports_audio': True,
       'max_duration': 8,
       'models': ['veo3-fast', 'veo3-quality'],
       'endpoints': {
           'veo3-fast': '/veo/generate',
           'veo3-quality': '/veo/generate'
       }
   },
   'runway': {
       'name': 'Runway AI',
       'base_url': 'https://api.runwayml.com/v1',
       'headers': {
           'Authorization': 'Bearer {api_key}',
           'Content-Type': 'application/json'
       },
       'cost_per_second': 0.30,  # Estimated
       'supports_audio': True,
       'max_duration': 10
   },
   'piapi': {
       'name': 'PIAPI',
       'base_url': 'https://api.piapi.xyz/v1',
       'headers': {
           'Authorization': 'Bearer {api_key}',
           'Content-Type': 'application/json'
       },
       'cost_per_second': 0.25,  # Estimated
       'supports_audio': True,
       'max_duration': 10
   },
   'veo3api': {
       'name': 'VEO3API',
       'base_url': 'https://api.veo3api.ai/v1',
       'headers': {
           'Authorization': 'Bearer {api_key}',
           'Content-Type': 'application/json'
       },
       'cost_per_second': 0.05,  # $0.40 for 8s (Fast mode)
       'supports_audio': True,
       'max_duration': 8,
       'models': ['veo3-fast', 'veo3-quality']
   }
}

class VideoRecipeGenerator:

   def __init__(self):
       provider = os.getenv('USE_PROVIDER', 'fal')
       self.provider = provider.lower()
       
       # API key management - EXPANDED
       self.api_keys = {
           'fal': os.getenv('FAL_KEY'),
           'runway': os.getenv('RUNWAY_API_KEY'),
           'piapi': os.getenv('PIAPI_API_KEY'),
           'kie': os.getenv('KIE_API_KEY'),
           'veo3api': os.getenv('VEO3API_KEY')
       }
       
       self.api_key = self.api_keys.get(self.provider)
       
       print(f"🔌 Loaded video provider: {self.provider}")

       self.base_dir = Path(__file__).parent
       self.output_dir = self.base_dir / "output"
       self.output_dir.mkdir(exist_ok=True)
       
       # Clear any previous state
       self.last_ingredients = []
       self.last_cuisine = ""

       self.current_template_id = None

   def set_provider(self, provider_name):
       """Dynamically switch providers"""
       self.provider = provider_name.lower()
       
       # Load provider-specific configurations
       if provider_name == "runway":
           self.api_key = os.getenv('RUNWAY_API_KEY')
       elif provider_name == "piapi":
           self.api_key = os.getenv('PIAPI_API_KEY')
       elif provider_name == "kie":
           self.api_key = os.getenv('KIE_API_KEY')
       elif provider_name == "veo3api":
           self.api_key = os.getenv('VEO3API_KEY')
       else:
           self.api_key = self.api_keys.get(provider_name)
       
       print(f"🔄 Switched to provider: {self.provider}")

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

   def enhance_audio_with_mmaudio(self, video_url: str, cuisine: str) -> Tuple[bool, str]:
       """
       FIXED: Add enhanced audio with BALANCED music and cooking sounds
       """
       try:
           import fal_client
           
           # Configure fal client
           fal_client.api_key = self.api_keys['fal']
           
           # Create BALANCED audio enhancement prompt
           cuisine_lower = cuisine.lower()
           audio_prompt = f"Traditional {cuisine_lower} background music playing softly with PROMINENT cooking sound effects: intense sizzling, rhythmic chopping, aromatic steaming, flames crackling, oil bubbling, vigorous stirring. The cooking sounds should be clear and dominant while traditional {cuisine_lower} music provides cultural ambiance in the background."
           
           print(f"🎵 Enhancing audio with BALANCED {cuisine_lower} music and cooking sounds...")
           print(f"🎵 Audio prompt: {audio_prompt}")
           
           # Call MMAudio with balanced audio approach
           result = fal_client.submit(
               "fal-ai/mmaudio-v2",
               arguments={
                   "video_url": video_url,
                   "prompt": audio_prompt
               }
           )
           
           # Get the result
           output = result.get()
           enhanced_video_url = output.get("video", {}).get("url")
           
           if enhanced_video_url:
               print(f"✅ Audio enhanced with balanced music and cooking sounds!")
               return True, enhanced_video_url
           else:
               print(f"❌ No enhanced video URL in response: {output}")
               return False, "No enhanced video URL in response"
               
       except Exception as e:
           print(f"💥 Audio enhancement error: {str(e)}")
           return False, f"Audio enhancement error: {str(e)}"

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
    Build cuisine-specific prompts - OPTIMIZED FOR PROVIDER
    """
 # Try to get evolved prompt first
    template_id, template_text = prompt_evolution.get_best_prompt(self.provider, cuisine)
    
    if template_text:
        # Use evolved template
        ingredient_list = ", ".join(ingredients)
        cooking_steps = ". ".join(self.generate_ingredient_specific_actions(ingredients, dish_type))
        
        # Replace variables in template
        prompt = template_text.format(
            cuisine=cuisine.title() if cuisine else "International",
            dish_type=dish_type,
            ingredients=ingredient_list,
            cooking_steps=cooking_steps
        )
        
        print(f"🧬 Using evolved prompt (template #{template_id})")
        
        # Store the template_id for tracking
        self.current_template_id = template_id
        
        return prompt

    ingredient_list = ", ".join(ingredients)
    
    print(f"🏗️ BUILDING PROMPT FOR: {cuisine} with {ingredient_list}")
    
    # Generate ingredient actions using existing method
    ingredient_actions = self.generate_ingredient_specific_actions(ingredients, dish_type)
    
    # KIE OPTIMIZATION: Shorter, action-focused prompts
    if self.provider == 'kie':
        print("⚡ Using KIE-optimized prompt (action-focused)")
        
        # Add emphasis and additional cooking verbs for KIE
        emphasized_actions = []
        for action in ingredient_actions:
            # Add emphasis to key verbs
            emphasized_action = action.replace('adding', 'ADD').replace('drizzling', 'DRIZZLE').replace('tossing', 'TOSS')
            emphasized_actions.append(emphasized_action)
        
        # Add extended cooking sequence
        emphasized_actions.extend([
            'STIR-FRY vigorously multiple times',
            'FLIP ingredients high in wok',
            'CONTINUE cooking with sizzling sounds',
            'FINISH with final stirring motions'
        ])
        
        # KIE-optimized prompt
        prompt = (
            f"{cuisine.title()} chef in traditional kitchen preparing {dish_type} with {ingredient_list}. "
            f"COMPLETE COOKING SEQUENCE showing EVERY step: "
            f"{'. '.join(emphasized_actions)}. "
            f"Show CONTINUOUS cooking action from start to finish. "
            f"Traditional {cuisine} setting with proper cookware. "
        )
        
        if enable_audio:
            prompt += f"LOUD sizzling sounds throughout, kitchen ambiance, traditional {cuisine} music."
            
    else:
        # FAL prompt - detailed cultural representation
        print("📝 Using standard FAL prompt (cultural detail)")
        
        # DYNAMIC cuisine description
        cuisine_name = cuisine.title() if cuisine else "International"
        
        # TRADITIONAL AUTHENTIC character and environment descriptions
        if cuisine and cuisine.lower() != "international":
            character_desc = f"an authentic traditional {cuisine_name} cook with traditional {cuisine_name} clothing, headwear, and cultural appearance, FULL BODY visible with warm facial expressions"
            kitchen_desc = f"traditional {cuisine_name} home kitchen with authentic cookware, cultural tools, traditional utensils, and cultural elements"
            style_desc = f"traditional {cuisine_name} cooking techniques with cultural hand movements and authentic preparation methods"
            
            if enable_audio:
                audio_desc = self.generate_cuisine_audio(cuisine.lower())
                audio_section = f"MANDATORY AUDIO: {audio_desc}. "
            else:
                audio_section = ""
        else:
            character_desc = "a traditional home cook with FULL BODY visible, warm facial expressions and authentic cooking movements"
            kitchen_desc = "traditional home kitchen with authentic cookware and cultural cooking tools"
            style_desc = "traditional home cooking techniques with authentic preparation methods"
            if enable_audio:
                audio_section = "MANDATORY AUDIO: home kitchen sounds: intense sizzling, aromatic steaming, gentle cooking ambiance. "
            else:
                audio_section = ""
        
        # TRADITIONAL AUTHENTIC PROMPT
        prompt = (
            f"A traditional cooking scene in {kitchen_desc} showing FULL-BODY {character_desc} "
            f"preparing {dish_type} using {ingredient_list}. "
            f"Wide angle view showing complete traditional kitchen setting and full cook from head to toe. "
            f"COOK CLEARLY VISIBLE throughout in traditional cultural attire with authentic cooking movements. "
            f"Traditional cooking sequence: {', '.join(ingredient_actions[:3])} "
            f"in traditional cookware with intense sizzling and aromatic steam. "
            f"Cook expertly prepares ingredients using {style_desc}, "
            f"showing COMPLETE TRADITIONAL COOKING PROCESS in authentic cultural setting. "
            f"Warm traditional lighting, authentic cultural atmosphere, and traditional cooking methods. "
            f"Cook's cultural identity and expertise clearly visible through traditional dress and movements. "
            f"{audio_section}"
            f"Authentic cultural cooking, traditional home atmosphere, complete traditional cooking demonstration."
        )
    
    print(f"📝 GENERATED PROMPT: {prompt}")
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
               "enhance_prompt": True,
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

   def call_kie_api(self, prompt: str, duration: int, cuisine: str = "", ingredients: List[str] = None,
                 use_fast_model: bool = True, enable_audio: bool = True, async_mode: bool = False) -> Tuple[bool, str]:
    """Call KIE AI API for video generation with VEO3"""
    try:
        config = PROVIDER_CONFIGS['kie']
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Determine model and endpoint
        model = 'veo3'  # They only have one model name!
        endpoint = config['endpoints'].get('veo3-fast', '/veo/generate')
        
        payload = {
             "prompt": prompt,
             "model": model,
             "duration": duration,
             "audio_enabled": enable_audio,
             "waterMark": "KieAI",
             "aspectRatio": "16:9"
        }
        
        print(f"🎬 CALLING KIE AI ({model})")
        print(f"💰 Cost: ${0.40 if use_fast_model else 2.00} vs FAL's $6.00!")
        print(f"🔧 PAYLOAD: {payload}")
        
        url = f"{config['base_url']}{endpoint}"
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📦 KIE RESPONSE: {result}")
            
            # KIE returns 200 even for errors! Check the actual response content
            if result.get("code") == 200:
                task_id = result.get("data", {}).get("taskId")
                if task_id:
                    print(f"✅ Task created with ID: {task_id}")
                    
                    # ASYNC MODE FIX: Return task_id immediately for async!
                    if async_mode:
                        return True, task_id
                    else:
                        # Only poll if NOT in async mode
                        return self.poll_kie_result(task_id)
                else:
                    return False, "No task ID in response"
            else:
                # They returned HTTP 200 but internal error code
                return False, f"KIE API error: {result.get('msg', 'Unknown error')}"
        else:
            return False, f"API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"KIE API error: {str(e)}"

   def poll_kie_result(self, task_id: str, max_attempts: int = 60) -> Tuple[bool, str]:
       """Poll KIE AI for video generation result"""
       try:
           config = PROVIDER_CONFIGS['kie']
           headers = {
               'Authorization': f'Bearer {self.api_key}',
               'Content-Type': 'application/json'
           }
           
           url = f"{config['base_url']}/veo/record-info?taskId={task_id}"
           
           for attempt in range(max_attempts):
               response = requests.get(url, headers=headers)
               print(f"⏳ Polling attempt {attempt + 1}/{max_attempts}...")
               
               if response.status_code == 200:
                   result = response.json()
                   print(f"📊 Poll response: {result}")
                   
                   if result.get("code") == 200:
                       data = result.get("data", {})
                       
                       # Check successFlag instead of status
                       if data.get("successFlag") == 1:
                           # Get video URLs from response structure
                           response_data = data.get("response", {})
                           video_urls = response_data.get("resultUrls", [])
                           
                           if video_urls:
                               print(f"✅ KIE AI video ready!")
                               return True, video_urls[0]
                       elif data.get("successFlag") in [0, None]:
                           # Still processing
                           print(f"⏳ Still generating...")
                       else:
                           # Failed
                           return False, f"Generation failed: {data.get('errorMessage', 'Unknown error')}"
               
               time.sleep(5)
           
           return False, "Timeout waiting for video generation"
           
       except Exception as e:
           return False, f"Polling error: {str(e)}"

   def call_runway_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
       """Call Runway API for video generation"""
       try:
           headers = {
               "Authorization": f"Bearer {os.getenv('RUNWAY_API_KEY')}",
               "Content-Type": "application/json"
           }
           
           payload = {
               "prompt": prompt,
               "duration": duration,
               "width": 1024,
               "height": 576
           }
           
           print(f"🎬 CALLING RUNWAY API")
           print(f"🔧 PAYLOAD: {payload}")
           
           # You'll need the actual Runway API endpoint
           response = requests.post("https://api.runwayml.com/v1/generate", 
                                  json=payload, headers=headers, timeout=120)
           
           if response.status_code == 200:
               result = response.json()
               video_url = result.get("video_url")
               return (True, video_url) if video_url else (False, "No video URL")
           else:
               return False, f"API error: {response.status_code} - {response.text}"
               
       except Exception as e:
           return False, f"Runway API error: {str(e)}"

   def call_piapi_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
       """Call PIAPI for video generation"""
       try:
           headers = {
               "Authorization": f"Bearer {os.getenv('PIAPI_API_KEY')}",
               "Content-Type": "application/json"
           }
           
           payload = {
               "prompt": prompt,
               "duration": duration
           }
           
           print(f"🎬 CALLING PIAPI")
           print(f"🔧 PAYLOAD: {payload}")
           
           # You'll need the actual PIAPI endpoint
           response = requests.post("https://api.piapi.xyz/v1/video/generate", 
                                  json=payload, headers=headers, timeout=120)
           
           if response.status_code == 200:
               result = response.json()
               video_url = result.get("video_url")
               return (True, video_url) if video_url else (False, "No video URL")
           else:
               return False, f"API error: {response.status_code} - {response.text}"
               
       except Exception as e:
           return False, f"PIAPI error: {str(e)}"

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
    MULTI-PROVIDER: Generate video with different providers + MMAudio enhancement
    """
    print(f"\n🚀 === STARTING VIDEO GENERATION ===")
    print(f"🌍 CUISINE: {cuisine}")
    print(f"🥘 RAW INGREDIENTS: {ingredients}")
    print(f"🔌 PROVIDER: {self.provider}")
    
    # CRITICAL: Validate and clean ingredients to prevent contamination
    validated_ingredients = self.validate_and_clean_ingredients(ingredients)
    
    generation_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Parameters - DEFAULT TO STANDARD VEO3 FOR MPP
    dish_type = kwargs.get('dish_type', 'dish')
    use_fast_model = kwargs.get('use_fast_model', False)  # CHANGED: Default to False for MPP
    enable_audio = kwargs.get('enable_audio', True)  # MANDATORY for cuisine-specific audio

    # FORCE AUDIO FOR KIE - IT REQUIRES IT!
    if self.provider == 'kie':
        enable_audio = True  # KIE needs audio enabled
        use_fast_model = True  # KIE is the fast model

    enhance_prompt = kwargs.get('enhance_prompt', False)
    async_mode = kwargs.get('async_mode', False)
    
    # Build COOKING-FOCUSED cuisine-specific prompt with CONDITIONAL audio
    prompt = self.build_dynamic_cuisine_prompt(cuisine, validated_ingredients, dish_type, enable_audio)
    
    print(f"⚡ GENERATION SETTINGS:")
    print(f"   - Cuisine: {cuisine}")
    print(f"   - Ingredients: {validated_ingredients}")
    print(f"   - Audio: {enable_audio}")
    print(f"   - Provider: {self.provider}")

    success = False
    video_url = ""
    error_message = ""
    request_id = None
    
    # Generate video based on provider
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
                print(f"🎉 VIDEO GENERATED! Now adding magical background music...")
            else:
                error_message = result
                print(f"💥 GENERATION FAILED: {error_message}")
    elif self.provider == 'kie':
        success, result = self.call_kie_api(
            prompt, 8, cuisine, validated_ingredients,
            use_fast_model=use_fast_model,
            enable_audio=enable_audio,
            async_mode=async_mode
        )
        if success:
            if async_mode:
                request_id = result  # In async mode, result is the task_id
                print(f"📋 KIE task submitted for async processing: {request_id}")
            else:
                video_url = result
                print(f"🎉 KIE AI VIDEO GENERATED! 93% cost savings achieved!")
                video_url = result
            print(f"🎉 KIE AI VIDEO GENERATED! 93% cost savings achieved!")
        else:
            error_message = result
            print(f"💥 KIE AI FAILED: {error_message}")
    elif self.provider == 'runway':
        success, result = self.call_runway_api(prompt, 8)
        if success:
            video_url = result
            print(f"🎉 RUNWAY VIDEO GENERATED!")
        else:
            error_message = result
            print(f"💥 RUNWAY FAILED: {error_message}")
    elif self.provider == 'piapi':
        success, result = self.call_piapi_api(prompt, 8)
        if success:
            video_url = result
            print(f"🎉 PIAPI VIDEO GENERATED!")
        else:
            error_message = result
            print(f"💥 PIAPI FAILED: {error_message}")
    else:
        error_message = f"Unsupported provider: {self.provider}"
        print(f"❌ {error_message}")

    # THE MISSING PIECE: Add MMAudio enhancement for beautiful background music (FAL only)!
    if success and video_url and not async_mode and self.provider == 'fal':
        print("🎵 Enhancing video with cultural background music...")
        audio_success, enhanced_result = self.enhance_audio_with_mmaudio(video_url, cuisine)
        if audio_success:
            video_url = enhanced_result  # Use enhanced video with music
            print(f"✅ Audio enhanced! Using enhanced video with beautiful {cuisine} music!")
        else:
            print(f"⚠️ Audio enhancement failed: {enhanced_result}. Using original video.")

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
            "provider_mode": f"{self.provider.upper()} with multi-provider support"
        }
    }

   def check_async_status(self, request_id: str, use_fast_model: bool = False) -> Dict:
    """Check the status with correct provider"""
    
    # Handle KIE provider
    if self.provider == 'kie':
        try:
            config = PROVIDER_CONFIGS['kie']
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{config['base_url']}/veo/record-info?taskId={request_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 200:
                    data = result.get("data", {})
                    
                    if data.get("successFlag") == 1:
                        # Video is ready!
                        response_data = data.get("response", {})
                        video_urls = response_data.get("resultUrls", [])
                        
                        if video_urls:
                            return {
                                "status": "COMPLETED",
                                "video_url": video_urls[0]
                            }
                    elif data.get("successFlag") in [0, None]:
                        # Still processing
                        return {
                            "status": "IN_PROGRESS",
                            "request_id": request_id
                        }
                    else:
                        # Failed
                        return {
                            "status": "ERROR",
                            "error": data.get('errorMessage', 'Unknown error')
                        }
            
            return {
                "status": "ERROR",
                "error": f"Status check failed: {response.status_code}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": f"Status check error: {str(e)}"
            }
    
    # Handle FAL provider (existing code)
    else:
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
       