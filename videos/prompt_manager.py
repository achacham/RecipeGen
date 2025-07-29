import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class PromptManager:
   """Manages prompt templates and cuisine configurations for video generation"""
   
   def __init__(self):
       # Set up paths relative to the videos folder
       self.base_dir = Path(__file__).parent
       self.config_dir = self.base_dir / "config"
       
       # Create config directory if it doesn't exist
       self.config_dir.mkdir(exist_ok=True)
       
       # Initialize configuration files
       self.templates_file = self.config_dir / "templates.json"
       self.cuisines_file = self.config_dir / "cuisines.json"
       
       # Load configurations
       self.templates = self._load_templates()
       self.cuisines = self._load_cuisines()
       
       print(f"✅ PromptManager initialized with config directory: {self.config_dir}")

   def _load_templates(self) -> Dict:
       """Load prompt templates from file or create the file with defaults if it doesn't exist"""
       if not self.templates_file.exists():
           # Create the default templates file on first run
           default_templates = {
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
           
           # Write the default file
           try:
               with open(self.templates_file, 'w', encoding='utf-8') as f:
                   json.dump(default_templates, f, indent=2, ensure_ascii=False)
               print(f"✅ Created default templates.json at {self.templates_file}")
           except IOError as e:
               print(f"❌ Failed to create templates.json: {e}")
               # Return minimal fallback if file creation fails
               return {"base_template": "A cooking scene showing {cook_type} preparing {dish_type} with {ingredient_list}."}
       
       # Load from file
       try:
           with open(self.templates_file, 'r', encoding='utf-8') as f:
               return json.load(f)
       except (json.JSONDecodeError, IOError) as e:
           print(f"⚠️  Warning: Could not load templates.json: {e}")
           # Return minimal fallback
           return {"base_template": "A cooking scene showing {cook_type} preparing {dish_type} with {ingredient_list}."}

   def _load_cuisines(self) -> Dict:
       """Load cuisine character maps from file or return empty dict"""
       if self.cuisines_file.exists():
           try:
               with open(self.cuisines_file, 'r', encoding='utf-8') as f:
                   return json.load(f)
           except (json.JSONDecodeError, IOError) as e:
               print(f"⚠️  Warning: Could not load cuisines.json: {e}. Using fallback.")
       
       # Return empty dict - the smart fallback in generate_prompt() handles everything
       return {}

   def generate_prompt(self, cuisine: str, ingredients: List[str], dish_type: str = None, **kwargs) -> str:
       """Generate a prompt using templates and cuisine configurations with strict ingredient control"""
       cuisine_key = cuisine.strip().title()
       
       # Get cuisine configuration or create default
       cuisine_config = self.cuisines.get(cuisine_key) or {
           "cook_type": f"traditional {cuisine_key} cook",
           "props": ["traditional cookware"],
           "music": "regional music"
       }

       # Extract parameters
       scene_style = kwargs.get('scene_style', 'cinematic')
       lighting = kwargs.get('lighting', 'warm studio')
       music = kwargs.get('music') or cuisine_config.get('music', 'traditional instrumental')
       cook_type = kwargs.get('cook_type') or cuisine_config.get('cook_type', f'traditional {cuisine_key} cook')

       # Format ingredients as explicit list
       ingredient_list = ", ".join(ingredients)
       
       # Use dish_type if provided, otherwise default to "dish"
       dish_type = dish_type or "dish"
       
       cultural_props = ", ".join(cuisine_config.get('props', ['traditional cookware']))

       # Get template and style descriptions
       template = self.templates.get('base_template')
       scene_descriptions = self.templates.get('scene_styles', {})
       lighting_descriptions = self.templates.get('lighting_styles', {})

       scene_style_desc = scene_descriptions.get(scene_style, scene_style)
       lighting_desc = lighting_descriptions.get(lighting, lighting)

       # Build prompt data dictionary
       prompt_data = {
           'scene_style': scene_style_desc,
           'lighting': lighting_desc,
           'cook_type': cook_type,
           'dish_type': dish_type,
           'cuisine': cuisine_key,
           'ingredient_list': ingredient_list,
           'cultural_props': cultural_props,
           'music': music,
           'visual_style': "Photorealistic, high-quality"
       }

       # Generate base prompt
       base_prompt = template.format(**prompt_data)
       
       # Add ingredient emphasis layer if template exists
       if 'ingredient_emphasis_template' in self.templates:
           emphasis = self.templates['ingredient_emphasis_template'].format(
               ingredient_list=ingredient_list
           )
           base_prompt = f"{base_prompt} {emphasis}"
       
       return base_prompt.strip()

   def save_templates(self) -> None:
       """Save current templates to file (for your wife's editor)"""
       try:
           with open(self.templates_file, 'w', encoding='utf-8') as f:
               json.dump(self.templates, f, indent=2, ensure_ascii=False)
           print(f"✅ Templates saved to {self.templates_file}")
       except IOError as e:
           print(f"❌ Failed to save templates: {e}")

   def save_cuisines(self) -> None:
       """Save current cuisines to file (for your wife's editor)"""
       try:
           with open(self.cuisines_file, 'w', encoding='utf-8') as f:
               json.dump(self.cuisines, f, indent=2, ensure_ascii=False)
           print(f"✅ Cuisines saved to {self.cuisines_file}")
       except IOError as e:
           print(f"❌ Failed to save cuisines: {e}")

   def enhance_audio(self, video_url: str, cuisine: str, api_key: str) -> tuple[bool, str]:
       """Add enhanced audio to existing video using MMAudio"""
       try:
           import fal_client
           
           # Configure fal client
           fal_client.api_key = api_key
           
           # Get cuisine audio description
           cuisine_config = self.cuisines.get(cuisine.strip().title(), {})
           music_description = cuisine_config.get('music', 'traditional cooking music')
           
           # Create audio enhancement prompt
           audio_prompt = f"Authentic {cuisine} kitchen cooking sounds with PROMINENT, LOUD {music_description} playing as the primary soundtrack. The music should be clearly audible and dominant over cooking sounds, creating an immersive cultural ambiance."
           
           print(f"🎵 Enhancing audio with: {music_description}")
           
           # Call MMAudio to add enhanced audio
           result = fal_client.submit(
               "fal-ai/mmaudio-v2",
               arguments={
                   "video_path": video_url,
                   "text_prompt": audio_prompt
               }
           )
           
           # Get the result
           output = result.get()
           enhanced_video_url = output.get("video", {}).get("url")
           
           if enhanced_video_url:
               return True, enhanced_video_url
           else:
               return False, "No enhanced video URL in response"
               
       except Exception as e:
           return False, f"Audio enhancement error: {str(e)}"
       