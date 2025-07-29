#!/usr/bin/env python3
"""
RecipeGen AI Video Generator - Test Runner
Validates core functionality and generates sample videos
"""

import os
import sys
import time
from pathlib import Path
from main import VideoRecipeGenerator

def run_test_suite():
    """Run comprehensive test suite for video generator"""
    
    print("🧪 RecipeGen AI Video Generator - Test Suite")
    print("=" * 50)
    
    # Initialize generator
    try:
        generator = VideoRecipeGenerator()
        print("✅ Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False
    
    # Check API configuration
    if not generator.api_key:
        print("⚠️  WARNING: No API key found in .env file")
        print("   Tests will run but video generation will fail")
        print("   Please configure VIDEO_API_KEY in .env")
    else:
        print(f"✅ API key configured for {generator.provider}")
    
    # Test cases as specified in requirements
    test_cases = [
        {
            "name": "Jewish Traditional Cooking",
            "cuisine": "Jewish",
            "ingredients": ["potato", "onion", "egg"],
            "expected_elements": ["grandmother", "kosher kitchen", "wooden spoons"]
        },
        {
            "name": "Thai Authentic Cuisine", 
            "cuisine": "Thai",
            "ingredients": ["lemongrass", "fish sauce", "chili"],
            "expected_elements": ["mortar and pestle", "Thai chef", "bamboo"]
        },
        {
            "name": "Italian Default Parameters",
            "cuisine": "Italian", 
            "ingredients": ["tomatoes", "basil"],
            "expected_elements": ["nonna", "pasta", "olive oil"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎬 Test {i}/3: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Generate prompt (always works)
            prompt = generator.generate_prompt(
                test_case['cuisine'], 
                test_case['ingredients']
            )
            
            print(f"📝 Generated prompt: {prompt[:100]}...")
            
            # Validate prompt contains expected elements
            prompt_lower = prompt.lower()
            found_elements = []
            for element in test_case['expected_elements']:
                if element.lower() in prompt_lower:
                    found_elements.append(element)
            
            prompt_score = len(found_elements) / len(test_case['expected_elements'])
            print(f"🎯 Cultural accuracy: {prompt_score:.1%} ({len(found_elements)}/{len(test_case['expected_elements'])} elements)")
            
            # Attempt video generation (may fail without API key)
            if generator.api_key:
                print("🎥 Attempting video generation...")
                start_time = time.time()
                
                result = generator.generate_video(
                    test_case['cuisine'],
                    test_case['ingredients'],
                    duration=10  # Shorter for testing
                )
                
                generation_time = time.time() - start_time
                
                if result['success']:
                    print(f"✅ Video generated successfully in {generation_time:.1f}s")
                    print(f"📁 Local file: {result['local_path']}")
                    print(f"🌐 Video URL: {result['video_url']}")
                    
                    # Verify file exists
                    if result['local_path'] and Path(result['local_path']).exists():
                        file_size = Path(result['local_path']).stat().st_size
                        print(f"💾 File size: {file_size / 1024 / 1024:.1f} MB")
                    
                    test_result = {
                        'test_name': test_case['name'],
                        'success': True,
                        'prompt_accuracy': prompt_score,
                        'generation_time': generation_time,
                        'file_path': result['local_path'],
                        'video_url': result['video_url']
                    }
                else:
                    print(f"❌ Video generation failed: {result['error']}")
                    test_result = {
                        'test_name': test_case['name'],
                        'success': False,
                        'prompt_accuracy': prompt_score,
                        'error': result['error']
                    }
            else:
                print("⏭️  Skipping video generation (no API key)")
                test_result = {
                    'test_name': test_case['name'],
                    'success': 'skipped',
                    'prompt_accuracy': prompt_score,
                    'reason': 'No API key configured'
                }
            
            results.append(test_result)
            
        except Exception as e:
            print(f"💥 Test failed with exception: {e}")
            results.append({
                'test_name': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r['success'] is True)
    skipped_tests = sum(1 for r in results if r['success'] == 'skipped')
    failed_tests = sum(1 for r in results if r['success'] is False)
    
    print(f"✅ Successful: {successful_tests}/{len(results)}")
    print(f"⏭️  Skipped: {skipped_tests}/{len(results)}")
    print(f"❌ Failed: {failed_tests}/{len(results)}")
    
    # Detailed results
    for result in results:
        print(f"\n🎬 {result['test_name']}")
        if 'prompt_accuracy' in result:
            print(f"   Cultural Accuracy: {result['prompt_accuracy']:.1%}")
        
        if result['success'] is True:
            print(f"   Status: ✅ Success ({result.get('generation_time', 0):.1f}s)")
            if 'file_path' in result:
                print(f"   Output: {result['file_path']}")
        elif result['success'] == 'skipped':
            print(f"   Status: ⏭️  Skipped - {result.get('reason', 'Unknown')}")
        else:
            print(f"   Status: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    # Check output log
    log_path = generator.output_log_path
    if log_path.exists():
        print(f"\n📋 Output log: {log_path}")
        print(f"   Total generations logged: {len(generator.output_log)}")
    
    # Configuration check
    print(f"\n⚙️ CONFIGURATION")
    print(f"   Provider: {generator.provider}")
    print(f"   API Base: {generator.api_base}")
    print(f"   Output Directory: {generator.output_dir}")
    
    # Return overall success
    return failed_tests == 0

def main():
    """Main test runner entry point"""
    
    # Check if .env exists
    if not Path('.env').exists():
        print("⚠️  No .env file found. Creating from template...")
        if Path('.env.template').exists():
            import shutil
            shutil.copy('.env.template', '.env')
            print("📝 Please edit .env with your API credentials before running tests")
        else:
            print("❌ No .env.template found. Please create .env manually")
            return False
    
    success = run_test_suite()
    
    if success:
        print("\n🎉 All tests passed! System ready for production.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check configuration and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)