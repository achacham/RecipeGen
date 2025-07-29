# RecipeGen Video Generation Flask Blueprint

**File:** `video_routes.py`  
**Version:** 2.0.0  
**Created:** 2025-01-29  
**Author:** RecipeGen Development Team  
**Module Type:** Flask Web Service Integration  

## Purpose
Provides RESTful API endpoints for AI-powered cooking video generation within the RecipeGen Flask application. Handles HTTP request processing, data validation, ingredient conversion, and video delivery with comprehensive error handling and logging.

## Architecture Overview
This module implements a clean Flask Blueprint that bridges web requests with the sophisticated FAL AI video generation system. It maintains separation of concerns by handling only HTTP-specific logic while delegating video generation to specialized classes.

## Core Components

### Data Loading Functions
- `load_ingredients()`: Loads ingredient definitions from `data/ingredients.json`
- `load_dish_types()`: Loads dish type configurations from `data/dish_types.json`
- Creates fast-lookup dictionaries for real-time request processing

### Global Data Structures
- `INGREDIENTS_BY_SLUG`: Dictionary mapping ingredient slugs to full metadata
- `DISH_TYPES_BY_ID`: Dictionary mapping dish type IDs to configuration data
- `FAL_AI_AVAILABLE`: Boolean flag indicating VideoRecipeGenerator availability

## API Endpoints

### `/generate_video` [POST]
**Primary video generation endpoint**

**Request Body:**
```json
{
  "ingredients": ["chicken", "tomatoes", "basil"],
  "cuisine": "italian",
  "dish_type": "pasta"
}
Processing Pipeline:

Request Validation: Validates required ingredients parameter
Ingredient Conversion: Converts slugs to human-readable names using lookup tables
Dish Type Resolution: Maps dish type IDs to display names for better prompts
Video Generation: Calls VideoRecipeGenerator with processed parameters
File Delivery: Streams generated video file to client with proper MIME types

Response Types:

200: MP4 video file with cooking demonstration
400: Missing or invalid ingredients list
500: Video generation failure or system unavailable

Performance Characteristics:

Processing time: Variable based on FAL AI queue status
File size: Depends on video content and compression
Memory usage: Streaming delivery minimizes server memory impact

/video [POST]
Legacy compatibility endpoint
Maintains backward compatibility by redirecting to /generate_video endpoint.
Request Processing Flow

HTTP Request Receipt: Flask receives POST request with JSON payload
Data Extraction: Parses ingredients, cuisine, and dish type parameters
Input Validation: Ensures required fields are present and properly formatted
Ingredient Resolution: Converts ingredient slugs to full names using data lookups
Dish Type Enhancement: Resolves dish type IDs to descriptive names
Video Generation: Instantiates VideoRecipeGenerator and processes request
Response Delivery: Streams video file or returns error JSON with proper HTTP status

Error Handling Framework
Client Errors (4xx)

400 Bad Request: Missing ingredients parameter
400 Bad Request: Malformed JSON request body
400 Bad Request: Empty ingredients array

Server Errors (5xx)

500 Internal Server Error: VideoRecipeGenerator unavailable
500 Internal Server Error: FAL AI system failures
500 Internal Server Error: File system or network issues

Error Response Format
json{
  "error": "Human-readable error description",
  "success": false,
  "details": "Technical error details (optional)"
}
Logging Strategy

INFO Level: Request initiation, ingredient conversion, success status
ERROR Level: System failures, API errors, file operation problems
Structured Format: Consistent emoji indicators for log scanning
Performance Tracking: Request processing time and outcome logging

Dependencies
Internal Modules

video_generator.VideoRecipeGenerator: Core AI video generation engine
Application data files: ingredients.json, dish_types.json
Flask application logging system

External Libraries

Flask: Web framework and Blueprint system
pathlib: Modern file path operations
datetime: Timestamp generation for unique filenames
Standard Python libraries: json, os, logging

Configuration Management

Import Safety: Graceful handling of missing VideoRecipeGenerator
Path Resolution: Dynamic Python path configuration for module imports
Environment Integration: Inherits configuration from main Flask application

Video Delivery Specifications

MIME Type: video/mp4 for universal browser compatibility
Download Behavior: Inline display (not forced download)
Filename Convention: recipegen_fal_cooking_YYYYMMDD_HHMMSS.mp4
Caching Headers: Default Flask file serving behavior

Performance Optimizations

Fast Lookups: Pre-loaded ingredient and dish type dictionaries
Streaming Delivery: Files served directly without buffering
Memory Efficiency: Minimal server-side video processing
Connection Handling: Proper HTTP connection management

Security Considerations

Input Validation: Comprehensive request parameter checking
Path Safety: Secure file serving without directory traversal
Error Information: Sanitized error messages prevent information leakage
Resource Limits: Inherits Flask application timeout and size limits

Integration Points

Main Application: Registered as Blueprint in main Flask app
Data Layer: Reads from centralized JSON configuration files
Logging System: Integrates with application-wide logging configuration
Error Handling: Consistent with application error response patterns

Maintenance Guidelines

Endpoint Testing: Regular testing with various ingredient combinations
Error Monitoring: Track error rates and failure patterns
Performance Metrics: Monitor request processing times
File Cleanup: Implement periodic cleanup of generated video files
API Versioning: Consider versioning strategy for future API changes

Future Enhancement Opportunities

Async Processing: Non-blocking video generation with status polling
Request Queuing: Handle multiple concurrent video generation requests
Caching Layer: Intelligent caching based on ingredient combinations
Rate Limiting: Protect against excessive API usage
Batch Operations: Support for multiple video generation in single request


// Frontend: Use the fastest endpoint
fetch('/generate_video_fast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        ingredients: ['chicken', 'tomatoes', 'basil'],
        dish_type: 'pasta',
        cuisine: 'Italian',
        stream_response: true  // Direct streaming
    })
}).then(response => {
    // Video streams directly - no waiting for download
    const videoBlob = response.blob();
    // Display immediately
});

// Frontend: Use async for even better UX
const asyncResponse = await fetch('/generate_video_async', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        ingredients: ['chicken', 'tomatoes', 'basil'],
        dish_type: 'pasta'
    })
});

const { request_id } = await asyncResponse.json();

// Poll for completion
const pollStatus = setInterval(async () => {
    const status = await fetch(`/video_status/${request_id}`);
    const result = await status.json();
    
    if (result.status === 'COMPLETED') {
        clearInterval(pollStatus);
        // Stream the completed video
        window.location.href = `/stream_video/${request_id}`;
    }
}, 2000);
