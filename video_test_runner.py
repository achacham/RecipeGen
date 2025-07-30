"""
RECIPEGEN VIDEO TESTING HARNESS
Simple, fast interface for testing different video providers
"""
import json
import os
from pathlib import Path
from video_generator import VideoRecipeGenerator

class VideoTester:
    def __init__(self):
        self.config_path = Path(__file__).parent / "providers_config.json"
        self.load_provider_configs()
    
    def load_provider_configs(self):
        """Load provider configurations"""
        try:
            with open(self.config_path, 'r') as f:
                self.providers = json.load(f)
        except FileNotFoundError:
            print("⚠️ providers_config.json not found - using defaults")
            self.providers = self.get_default_configs()
    
    def get_default_configs(self):
        """Default provider configurations"""
        return {
            "fal": {
                "api_key_env": "FAL_KEY",
                "cost_per_second": 0.75,
                "model": "fal-ai/veo3",
                "description": "Current VEO3 Standard - High quality, expensive"
            },
            "fal_fast": {
                "api_key_env": "FAL_KEY", 
                "cost_per_second": 0.40,
                "model": "fal-ai/veo3/fast",
                "description": "VEO3 Fast - Lower quality, cheaper"
            },
            "kling": {
                "api_key_env": "KLING_KEY",
                "cost_per_second": 0.15,
                "model": "kling-ai/video",
                "description": "Kling AI - Cultural authenticity champion"
            },
            "laozhang": {
                "api_key_env": "LAOZHANG_KEY",
                "cost_per_second": 0.025,
                "model": "veo3-fast-cheap",
                "description": "LaoZhang VEO3 Fast - 80% cheaper!"
            }
        }
    
    def quick_test(self, provider="fal", cuisine="indonesian", ingredients=None, **kwargs):
        """ULTRA-SIMPLE TEST FUNCTION"""
        if ingredients is None:
            ingredients = ["salmon", "soy sauce", "scallions"]
        
        print(f"\n🧪 === TESTING {provider.upper()} ===")
        
        # Check if provider exists
        if provider not in self.providers:
            print(f"❌ Unknown provider: {provider}")
            print(f"Available: {list(self.providers.keys())}")
            return None
        
        config = self.providers[provider]
        print(f"📋 {config['description']}")
        print(f"💰 Cost: ${config['cost_per_second']}/second")
        print(f"🍽️ Testing: {cuisine} cuisine")
        print(f"🥘 Ingredients: {ingredients}")
        
        # Calculate estimated cost
        duration = kwargs.get('duration', 8)
        estimated_cost = config['cost_per_second'] * duration
        print(f"💸 Estimated cost: ${estimated_cost:.2f}")
        
        # Override provider in generator
        generator = VideoRecipeGenerator()
        generator.provider = provider
        
        # Run test
        try:
            result = generator.generate_video(cuisine, ingredients, **kwargs)
            
            print(f"\n🎯 === RESULTS ===")
            print(f"✅ Success: {result['success']}")
            if result['success']:
                print(f"🎵 Video URL: {result.get('video_url', 'None')}")
                print(f"💾 Local file: {result.get('local_path', 'None')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown')}")
            
            return result
            
        except Exception as e:
            print(f"💥 Test failed: {str(e)}")
            return None
    
    def compare_providers(self, providers_list, cuisine="indonesian", ingredients=None):
        """Compare multiple providers with same inputs"""
        if ingredients is None:
            ingredients = ["salmon", "soy sauce"]
        
        print(f"\n🆚 === COMPARING PROVIDERS ===")
        results = {}
        
        for provider in providers_list:
            print(f"\n" + "="*50)
            result = self.quick_test(provider, cuisine, ingredients)
            results[provider] = result
        
        print(f"\n📊 === COMPARISON SUMMARY ===")
        for provider, result in results.items():
            if result:
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                cost = self.providers[provider]['cost_per_second'] * 8
                print(f"{provider:10} | {status:10} | ${cost:.2f}")
        
        return results
    
    def list_providers(self):
        """Show all available providers"""
        print("\n🔍 === AVAILABLE PROVIDERS ===")
        for name, config in self.providers.items():
            print(f"{name:10} | ${config['cost_per_second']:.2f}/sec | {config['description']}")

# CONVENIENCE FUNCTIONS FOR RAPID TESTING
def test_fal():
    """Test current FAL VEO3"""
    tester = VideoTester()
    return tester.quick_test("fal")

def test_kling():
    """Test Kling AI"""
    tester = VideoTester()
    return tester.quick_test("kling")

def test_cheap():
    """Test LaoZhang cheap VEO3"""
    tester = VideoTester()
    return tester.quick_test("laozhang")

def compare_all():
    """Compare all providers"""
    tester = VideoTester()
    return tester.compare_providers(["fal", "fal_fast", "kling", "laozhang"])

def test_runway():
    """Test Runway (you have the key!)"""
    tester = VideoTester()
    return tester.quick_test("runway")

def test_piapi():
    """Test PIAPI (you have this key too!)"""
    tester = VideoTester()
    return tester.quick_test("piapi")

def test_runway():
    """Test Runway (you have the key!)"""
    tester = VideoTester()
    return tester.quick_test("runway")

def test_piapi():
    """Test PIAPI (you have this key too!)"""
    tester = VideoTester()
    return tester.quick_test("piapi")

if __name__ == "__main__":
    tester = VideoTester()
    
    # UNCOMMENT TO TEST:
    # tester.list_providers()
    # test_fal()
    # test_kling() 
    # test_cheap()
    # compare_all()
    
    # QUICK SINGLE TEST
    tester.quick_test("fal", "indonesian", ["salmon", "scallions", "soy sauce"])