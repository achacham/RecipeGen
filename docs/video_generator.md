# RecipeGen FAL AI Video Generator Module

**File:** `video_generator.py`  
**Version:** 2.0.0  
**Created:** 2025-01-29  
**Author:** RecipeGen Development Team  
**Module Type:** Core AI Video Generation Engine  

## Purpose
Handles sophisticated AI-powered cooking video generation using FAL AI's veo3 model. Converts user-selected ingredients into cinematic cooking demonstrations with ingredient-specific precision and professional quality output.

## Architecture Overview
This module implements a clean, focused video generation system that eliminates complexity while maintaining high performance. It provides direct integration with FAL AI services and handles the complete video generation pipeline from prompt creation to local file delivery.

## Core Components

### VideoRecipeGenerator Class
Primary class responsible for managing the entire video generation workflow:
- **API Management**: Secure FAL API key handling and provider configuration
- **Video Generation**: Direct integration with FAL AI's veo3 model
- **File Operations**: Video download, storage, and local path management
- **Error Handling**: Comprehensive exception management and logging

### Key Methods

#### `__init__()`
Initializes the video generator with environment-based configuration:
- Loads FAL API credentials from environment variables
- Configures output directory structure
- Sets up provider-specific parameters

#### `call_fal_api(prompt, duration, cuisine, ingredients)`
Core FAL AI integration method:
- Submits video generation requests to fal-ai/veo3 model
- Handles API authentication and request formatting
- Processes response and extracts video URLs
- Returns success status and video URL or error details

#### `download_video(url, filename)`
Video retrieval and storage system:
- Downloads generated videos from FAL AI servers
- Implements streaming download with timeout protection
- Saves videos to local output directory with unique filenames
- Returns local file path for serving

#### `generate_video(cuisine, ingredients, **kwargs)`
Primary public interface for video generation:
- Builds ingredient-specific cooking prompts
- Orchestrates the complete generation workflow
- Handles success/failure logging and reporting
- Returns comprehensive result dictionary with metadata

## Video Generation Pipeline
1. **Prompt Construction**: Creates detailed cooking scene descriptions based on selected ingredients
2. **API Submission**: Sends generation request to FAL AI with optimized parameters
3. **Response Processing**: Extracts video URL from API response
4. **File Download**: Retrieves generated video and stores locally
5. **Result Packaging**: Returns success status, file paths, and metadata

## Configuration Requirements

### Environment Variables
- `USE_PROVIDER`: Must be set to "fal" for FAL AI integration
- `FAL_KEY`: FAL AI API authentication key
- `FAL_API_BASE`: FAL AI service endpoint (optional)

### System Dependencies
- `fal_client`: Official FAL AI Python client library
- `requests`: HTTP client for video download operations
- `pathlib`: Modern file path handling
- Network access to FAL AI services and video storage

## Video Output Specifications
- **Model**: fal-ai/veo3 (Google's latest with audio support)
- **Duration**: Fixed 8 seconds (FAL API constraint)
- **Quality**: High-definition cinematic output
- **Format**: MP4 with standard web compatibility
- **Audio**: Integrated cooking sound effects
- **Content**: Ingredient-specific cooking demonstrations

## Performance Considerations
- Video generation time depends on FAL AI queue status
- Download time varies by video size and network conditions
- Local storage requirements grow with usage
- API rate limits may apply based on subscription tier

## Error Handling Strategy
- Comprehensive exception catching for API failures
- Graceful degradation when services are unavailable
- Detailed error logging for debugging and monitoring
- User-friendly error messages for frontend display

## File Management
- Unique filename generation prevents conflicts
- Automatic output directory creation
- Local video storage for immediate serving
- No automatic cleanup (manual maintenance required)

## Future Enhancement Opportunities
- Multiple FAL model support for speed/quality tradeoffs
- Batch processing for multiple ingredient combinations
- Intelligent caching based on ingredient similarity
- Streaming delivery without local storage
- Progress callbacks for real-time status updates

## Maintenance Notes
- Monitor FAL API usage and billing
- Clean up local video files periodically
- Update FAL client library as new versions release
- Test with various ingredient combinations regularly
- Verify API key validity and permissions

## Integration Points
- Called by `video_routes.py` Flask Blueprint
- Reads ingredient data from RecipeGen data structures
- Integrates with application logging system
- Supports dish type and cuisine parameter passing

# MPP (Maximum Possible Performane) USAGE EXAMPLES:

def example_mpp_usage():
    """
    Examples of using the MPP optimized generator
    """
    generator = VideoRecipeGenerator()
    
    # FASTEST GENERATION (Recommended for production)
    result_fast = generator.generate_video(
        cuisine="Italian",
        ingredients=["chicken", "tomatoes", "basil"],
        dish_type="pasta",
        use_fast_model=True,    # 2x speed boost
        enable_audio=False,     # 33% speed boost  
        enhance_prompt=False,   # Additional speed boost
        async_mode=False        # Sync for immediate result
    )
    
    # ASYNC MODE (For even better user experience)
    result_async = generator.generate_video(
        cuisine="Italian", 
        ingredients=["chicken", "tomatoes", "basil"],
        dish_type="pasta",
        use_fast_model=True,
        enable_audio=False,
        async_mode=True         # Non-blocking processing
    )
    
    if result_async["success"]:
        request_id = result_async["request_id"]
        
        # Check status later
        status = generator.check_async_status(request_id)
        print(f"Async status: {status}")

if __name__ == "__main__":
    example_mpp_usage()