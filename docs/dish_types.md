# RecipeGen Dish Types Configuration

**File:** `dish_types.json`  
**Version:** 1.0.0  
**Created:** 2025-01-29  
**Author:** RecipeGen Development Team  

## Purpose
Central data source for all dish type definitions used throughout RecipeGen. This file eliminates hardcoding by providing a single source of truth for dish type metadata, cooking actions, and visual assets.

## Usage
- **Frontend:** Populates dish type selection grid on home screen
- **Backend:** Provides cooking actions for video generation prompts  
- **Data Integrity:** Single source prevents inconsistencies between components

## Structure
Each dish type object contains:
- `id`: Unique identifier (kebab-case, matches frontend expectations)
- `name`: Display name for user interface
- `description`: Brief description shown on dish type cards
- `cooking_action`: Detailed cooking process description for video generation
- `image`: Unsplash URL for visual representation

## Maintenance Notes
- When adding new dish types: ensure `id` matches frontend expectations
- Cooking actions should be descriptive enough for video generation prompts
- Image URLs should be high-quality, food-appropriate, and load reliably  
- Maintain consistency in description tone and length
- All 12 dish types must have corresponding cooking actions to avoid hardcoded fallbacks

## Dependencies
- Read by: `video_routes.py` (video generation)
- Read by: `index.html` (frontend dish type grid)
- Related files: `ingredients.json`, `recipes.json`