import os
import json
import uuid
import requests
import time  # ADDED: Missing import
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from dotenv import load_dotenv
from prompt_manager import PromptManager

# FIXED: Make path relative/configurable
env_path = os.getenv('ENV_PATH', '.env')  # Allow override via environment
load_dotenv(dotenv_path=env_path)

# Optional debug mode
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

if DEBUG_MODE:
    print("✅ .env file loaded.")
    print("🔍 DEBUG: USE_PROVIDER =", os.getenv('USE_PROVIDER'))
    print("🔍 DEBUG: VIDEO_API_KEY =", os.getenv('VIDEO_API_KEY')[:10] if os.getenv('VIDEO_API_KEY') else "None")
    print("🔍 DEBUG: RUNWAY_API_KEY =", os.getenv('RUNWAY_API_KEY')[:10] if os.getenv('RUNWAY_API_KEY') else "None")

class PromptBuilder:
    def __init__(self, cuisine_character_map, prompt_templates):
        self.cuisine_character_map = cuisine_character_map
        self.prompt_templates = prompt_templates

    def generate_prompt(self, cuisine: str, ingredients: List[str], **kwargs) -> str:
        if DEBUG_MODE:
            print(f"📋 Generating prompt for cuisine: {cuisine} and ingredients: {ingredients}")
        
        cuisine_key = cuisine.strip().title()
        cuisine_config = self.cuisine_character_map.get(cuisine_key) or {
            "cook_type": f"traditional {cuisine_key} cook",
            "props": ["traditional cookware"],
            "music": "regional music",
            "kitchen_style": "standard kitchen",
            "gestures": "standard cooking gestures",
            "clothing": "standard cooking attire"
        }

        scene_style = kwargs.get('scene_style', 'cinematic')
        lighting = kwargs.get('lighting', 'warm studio')
        music = kwargs.get('music') or cuisine_config.get('music', 'traditional instrumental')
        cook_type = kwargs.get('cook_type') or cuisine_config.get('cook_type', f'traditional {cuisine_key} cook')

        ingredients_str = (
            " and ".join(ingredients) if len(ingredients) <= 2
            else ", ".join(ingredients[:-1]) + f", and {ingredients[-1]}"
        )
        cultural_props = ", ".join(cuisine_config.get('props', ['traditional cookware']))

        template = self.prompt_templates.get('base_template',
            "A {scene_style} cooking scene featuring a {cook_type} preparing {cuisine} cuisine with {ingredients}."
        )
        scene_descriptions = self.prompt_templates.get('scene_styles', {})
        lighting_descriptions = self.prompt_templates.get('lighting_styles', {})

        scene_style_desc = scene_descriptions.get(scene_style, scene_style)
        lighting_desc = lighting_descriptions.get(lighting, lighting)

        prompt = template.format(
            scene_style=scene_style_desc,
            lighting=lighting_desc,
            cook_type=cook_type,
            cuisine=cuisine_key,
            ingredients=ingredients_str,
            cultural_props=cultural_props,
            music=music,
            visual_style="Photorealistic, high-quality"
        )
        return prompt.strip()


class VideoRecipeGenerator:
    def __init__(self):
        provider = os.getenv('USE_PROVIDER')
        if not provider:
            raise ValueError("❌ USE_PROVIDER is not set in your .env file!")
        self.provider = provider.lower()
        
        # FIXED: Centralized API key management
        self.api_keys = {
            'runway': os.getenv('RUNWAY_API_KEY'),
            'video': os.getenv('VIDEO_API_KEY'), 
            'kling': os.getenv('K_LING_API_KEY'),
            'fal': os.getenv('FAL_API_KEY'),
            'piapi': os.getenv('VIDEO_API_KEY')  # PiAPI uses VIDEO_API_KEY
        }
        
        # Get the appropriate API key for the provider
        self.api_key = self.api_keys.get(self.provider) or self.api_keys.get('video')
        
        if self.provider in ['runway', 'higgsfield', 'fal', 'kling']:
            self.api_base = os.getenv('VIDEO_API_BASE') or os.getenv('FAL_API_BASE')
            if not self.api_base:
                raise ValueError(f"❌ VIDEO_API_BASE or FAL_API_BASE not set for {self.provider}!")
        else:
            self.api_base = None

        print(f"🔌 Loaded video provider: {self.provider}")

        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / "output"
        self.prompts_dir = self.base_dir / "prompts"
        self.ingredients_dir = self.base_dir / "ingredients"
        for directory in [self.output_dir, self.prompts_dir, self.ingredients_dir]:
            directory.mkdir(exist_ok=True)

        # Initialize prompt manager (replaces old prompt system)
        self.prompt_manager = PromptManager()
        
        # Keep sample ingredients loading (still needed)
        self.sample_ingredients = self._load_json_config('sample_ingredients.json', from_ingredients=True, warn_on_fallback=True)
        
        self.output_log_path = self.output_dir / "output_log.json"
        self.output_log = self._load_output_log()

    def _load_output_log(self):
        # FIXED: Properly load existing log file
        if self.output_log_path.exists():
            try:
                with open(self.output_log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not load output log: {e}")
                return []
        return []

    def _save_output_log(self):
        try:
            with open(self.output_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.output_log, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️  Warning: Could not save output log: {e}")

    def _load_json_config(self, filename: str, from_ingredients: bool = False, warn_on_fallback: bool = False) -> Dict:
        base_path = self.ingredients_dir if from_ingredients else self.prompts_dir
        file_path = base_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                if warn_on_fallback:
                    print(f"⚠️  Warning: Could not load {filename}: {e}. Using fallback defaults.")
        elif warn_on_fallback:
            print(f"⚠️  Warning: {filename} not found, using fallback defaults.")
        return self._get_default_config(filename)

    def _get_default_config(self, filename: str) -> Dict:
        if 'prompt_templates' in filename:
            return {
            "base_template": "A {scene_style} cooking scene showing a {cook_type} preparing {dish_type} using ONLY AND EXACTLY these ingredients: {ingredient_list}. The cook MUST use ALL of these ingredients and NO OTHER ingredients. Show close-ups of EACH ingredient being prepared and added. The chef is shown lighting burners, heating cooking oil in a sizzling pan, adding ONLY {ingredient_list} to the hot pan, stirring ONLY these specific ingredients while they cook over flame. No other ingredients visible anywhere in the scene. Steam rises from hot pans, oil sizzles audibly, flames are visible under cookware. The scene features {cultural_props} with VERY LOUD, DOMINANT {music} as the primary audio track. Dynamic cooking movements showing ONLY the selected ingredients. Photorealistic, high-quality cinematography.",
            "ingredient_emphasis_template": "CRITICAL: Show ONLY these exact ingredients being cooked: {ingredient_list}. Do NOT show any other ingredients. Each selected ingredient MUST be clearly visible and used in the cooking process.",
            "scene_styles": {
                "cinematic": "cinematic wide-angle cooking scene",
                "top-down": "top-down instructional food video",
                "close-up": "close-up slow-motion kitchen view"
            },
            "lighting_styles": {
                "warm studio": "warm, professional studio lighting",
                "natural morning": "bright, natural morning light",
                "dramatic night": "low-key, dramatic night lighting"
            }
        }
        elif 'cuisine_character_map' in filename:
            return {
            "Persian": {
                "music": "Persian classical instrumental with tar and santur",
                "cook_type": "elegant Persian cook with graceful movements",
                "props": ["ornate serving dishes", "saffron container", "traditional mortar and pestle", "copper pots", "Persian carpets visible"]
            }
        }
        elif 'sample_ingredients' in filename:
            return {
            "Persian": ["saffron", "barberries", "basmati rice", "lamb", "eggplant"]
        }
        return {}

    def _make_api_request(self, url: str, headers: Dict, payload: Dict, timeout: int = 60) -> Tuple[bool, Dict]:
        """Centralized API request handling with consistent error handling"""
        try:
            if DEBUG_MODE:
                print(f"🚀 REQUEST URL: {url}")
                print(f"🚀 REQUEST PAYLOAD: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            if DEBUG_MODE:
                print(f"◀️ RESPONSE STATUS: {response.status_code}")
                print(f"◀️ RESPONSE BODY: {response.text}")
            
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timed out"}
        except requests.exceptions.HTTPError as e:
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
        except json.JSONDecodeError:
            return False, {"error": f"Invalid JSON response: {response.text}"}

    def call_runway_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
        headers = {
            "Authorization": f"Bearer {self.api_keys['runway']}",
            "Content-Type": "application/json"
        }

        fps = 24
        num_frames = duration * fps
        payload = {
            "prompt": prompt,
            "num_frames": num_frames,
            "fps": fps,
            "width": 1024,
            "height": 576,
            "guidance_scale": 7.5,
            "seed": 42,
            "motion": "cooking"
        }

        success, result = self._make_api_request(self.api_base, headers, payload)
        
        if success:
            video_url = result.get("video_url") or result.get("url")
            return (True, video_url) if video_url else (False, "No video URL in response")
        else:
            return False, result.get("error", "Unknown error")

    def call_higgsfield_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
        headers = {
            "Authorization": f"Bearer {self.api_keys['video']}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "duration": duration,
            "width": 576,
            "height": 1024,
            "seed": 42
        }
        
        success, result = self._make_api_request(self.api_base, headers, payload)
        
        if success:
            video_url = result.get("video_url") or result.get("url")
            return (True, video_url) if video_url else (False, "No video URL in response")
        else:
            return False, result.get("error", "Unknown error")

    def call_piapi_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
        api_key = self.api_keys['piapi']
        if not api_key:
            return False, "Missing VIDEO_API_KEY for PiAPI"

        url = os.getenv("VIDEO_API_BASE", "https://api.piapi.xyz/framepack/video")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Host": "api.piapi.xyz"
        }

        num_frames = duration * 24
        payload = {
            "prompt": prompt,
            "frame_count": num_frames,
            "width": 1024,
            "height": 576,
            "fps": 24,
            "enable_camera": False,
            "enable_lora": False
        }

        success, result = self._make_api_request(url, headers, payload)
        
        if success:
            video_url = result.get("video_url") or result.get("url")
            return (True, video_url) if video_url else (False, "No video URL in response")
        else:
            return False, result.get("error", "Unknown error")

    def call_kling_api(self, prompt: str, duration: int) -> Tuple[bool, str]:
        headers = {
            "x-api-key": self.api_keys['kling'],
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "prompt": prompt,
                "duration": duration
            },
            "model": "kling-v2"
        }
        
        success, result = self._make_api_request(
            "https://pollo.ai/api/platform/generation/kling-ai/kling-v2",
            headers, payload
        )
        
        if success:
            video_url = result.get("video_url")
            return (True, video_url) if video_url else (False, "No video_url in response")
        else:
            return False, result.get("error", "Unknown error")

    def call_fal_api(self, prompt: str, duration: int, cuisine: str = "", ingredients: List[str] = None) -> Tuple[bool, str]:
        try:
            import fal_client
            import threading
            
            if ingredients is None:
                ingredients = []
            
            # Configure fal client with your API key
            fal_client.api_key = self.api_keys['fal']
            
            # Progress messages
            progress_messages = [
                f"🎬 Preparing {cuisine} cooking scene...",
                f"📸 Setting up traditional {cuisine} kitchen backdrop...",
                f"👩‍🍳 Chef reviewing the {', '.join(ingredients)} recipe...",
                f"🎥 Recording authentic {cuisine} cooking techniques...",
                f"🎨 Adding cinematic lighting and cultural ambiance...",
                f"✨ Final video processing... Almost ready!"
            ]
            
            # Start progress animation in a separate thread
            progress_active = {"value": True}
            
            def show_progress():
                message_index = 0
                dots = 0
                while progress_active["value"]:
                    if message_index < len(progress_messages):
                        dot_animation = "." * (dots % 4)
                        print(f"\r{progress_messages[message_index]}{dot_animation}   ", end="", flush=True)
                        time.sleep(0.5)
                        dots += 1
                        # Longer time for each phase - 20 seconds each instead of 4 seconds
                        if dots % 40 == 0:  # Change message every 20 seconds
                            message_index += 1
                            print("")  # New line for next message
                    else:
                        print(f"\r🔄 Processing video{('.' * (dots % 4))}   ", end="", flush=True)
                        time.sleep(0.5)
                        dots += 1
            
            # Start progress thread
            progress_thread = threading.Thread(target=show_progress)
            progress_thread.daemon = True
            progress_thread.start()
            
            # Call the working fal model
            result = fal_client.submit(
            "fal-ai/veo3",  # Google's latest with audio
            arguments={
                "prompt": prompt,
                "duration": duration
            }
        )
            
            # Get the result
            output = result.get()
            
            # Stop progress animation
            progress_active["value"] = False
            time.sleep(0.1)  # Give thread time to finish
            print("\r" + " " * 80 + "\r", end="")  # Clear progress line
            
            video_url = output.get("video", {}).get("url")
            
            if video_url:
                return True, video_url
            else:
                return False, "No video URL in response"
                
        except Exception as e:
            if 'progress_active' in locals():
                progress_active["value"] = False
            return False, f"Fal API error: {str(e)}"

    def download_video(self, url: str, filename: str) -> Tuple[bool, str]:
        try:
            output_path = self.output_dir / filename
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            
            return True, str(output_path)
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def generate_video(self, cuisine: str, ingredients: List[str], **kwargs) -> Dict:
        generation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        prompt = self.prompt_manager.generate_prompt(cuisine, ingredients, **kwargs)
        duration = kwargs.get('duration', 12)

        print(f"🎬 Generating {cuisine} video")
        print(f"📝 Prompt: {prompt}")
        print(f"⏱️  Duration: {duration}s")

        success = False
        video_url = ""
        error_message = ""

        # Call appropriate API method
        api_methods = {
            'runway': self.call_runway_api,
            'higgsfield': self.call_higgsfield_api,
            'piapi': self.call_piapi_api,
            'kling': self.call_kling_api,
            'fal': self.call_fal_api
        }
        
        api_method = api_methods.get(self.provider)
        if api_method:
            if self.provider == 'fal':
                success, result = api_method(prompt, duration, cuisine, ingredients)
            else:
                success, result = api_method(prompt, duration)
            if success:
                video_url = result
                print(f"✅ Video generated! URL: {video_url}")
                
                # Step 2: Enhance audio if using fal provider
                if self.provider == 'fal':
                    print("🎵 Enhancing audio with cultural music...")
                    audio_success, enhanced_result = self.prompt_manager.enhance_audio(
                        video_url, cuisine, self.api_keys['fal']
                    )
                    if audio_success:
                        video_url = enhanced_result  # Use enhanced video
                        print(f"✅ Audio enhanced! New URL: {video_url}")
                    else:
                        print(f"⚠️ Audio enhancement failed: {enhanced_result}. Using original video.")
            else:
                error_message = result
                print(f"❌ Generation failed: {error_message}")
        else:
            error_message = f"Unsupported provider: {self.provider}"
            print(f"❌ {error_message}")

        # Download video if successful
        filename = f"{cuisine.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{generation_id[:8]}.mp4"
        local_path = ""
        
        if success and video_url:
            print("📥 Downloading video...")
            dl_success, local_path_or_err = self.download_video(video_url, filename)
            if dl_success:
                local_path = local_path_or_err
                print(f"💾 Saved to: {local_path}")
            else:
                print(f"⚠️  Download failed: {local_path_or_err}")

        # Create log entry
        log_entry = {
            "generation_id": generation_id,
            "timestamp": timestamp,
            "cuisine": cuisine,
            "ingredients": ingredients,
            "parameters": kwargs,
            "prompt": prompt,
            "success": success,
            "video_url": video_url if success else None,
            "local_path": local_path or None,
            "error": error_message if not success else None,
            "provider": self.provider
        }

        self.output_log.append(log_entry)
        self._save_output_log()
        return log_entry


if __name__ == "__main__":
    import argparse
    print("✅ Script started")
    
    parser = argparse.ArgumentParser(description='RecipeGen AI Video Generator')
    parser.add_argument("--cuisine", required=True, help="Cuisine type")
    parser.add_argument("--ingredients", required=True, help="Comma-separated ingredients")
    parser.add_argument("--style", choices=["top-down", "close-up", "cinematic"], 
                       default="cinematic", help="Camera style")
    parser.add_argument("--lighting", choices=["warm studio", "natural morning", "dramatic night"], 
                       default="warm studio", help="Lighting style")
    parser.add_argument("--music", default=None, help="Music style")
    parser.add_argument("--cook", default=None, help="Cook type override")
    parser.add_argument("--duration", type=int, default=12, help="Video duration in seconds")
    
    args = parser.parse_args()

    try:
        generator = VideoRecipeGenerator()
        ingredients_list = [i.strip() for i in args.ingredients.split(",")]
        
        prompt_kwargs = {
            "scene_style": args.style,
            "lighting": args.lighting,
            "duration": args.duration
        }
        
        # Only add optional parameters if they're provided
        if args.music:
            prompt_kwargs["music"] = args.music
        if args.cook:
            prompt_kwargs["cook_type"] = args.cook
        
        result = generator.generate_video(
            cuisine=args.cuisine, 
            ingredients=ingredients_list, 
            **prompt_kwargs
        )
        
        print("\n📋 Final Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)