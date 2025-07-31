from prompt_evolution import prompt_evolution
from video_generator import VideoRecipeGenerator

print("Testing Prompt Evolution System...")

# Test getting a prompt
template_id, template_text = prompt_evolution.get_best_prompt('kie', 'indonesian')

print(f"\nRetrieved template #{template_id}")
print(f"Template text: {template_text[:100]}...")

# Test the video generator integration
generator = VideoRecipeGenerator()

# Generate a test prompt
prompt = generator.build_dynamic_cuisine_prompt(
    'indonesian',
    ['Salmon', 'Soy Sauce', 'Chili Peppers'],
    'pasta',
    enable_audio=True
)

print(f"\nGenerated prompt: {prompt[:100]}...")
print(f"Template ID stored: {generator.current_template_id}")

print("\n✅ Prompt evolution system is connected!")