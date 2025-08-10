# test_ai_chef_quality.py
"""
A.I. Chef Quality Testing Suite
Generates multiple recipes and creates a quality report
"""

import json
from datetime import datetime
from ai_chef_generator import AIChefGenerator

def run_ai_chef_tests():
    """Run comprehensive tests on A.I. Chef"""
    
    chef = AIChefGenerator()
    
    test_cases = [
        # Simple cases (2-3 ingredients)
        ("ethiopian", "stir-fry", ["plantain", "onions"], "Impossible combo #1"),
        ("mexican", "stir-fry", ["chicken", "peppers", "onions"], "Non-traditional Mexican"),
        ("italian", "curry", ["tomatoes", "chicken"], "Italian curry fusion"),
        
        # Medium complexity (4-5 ingredients)
        ("chinese", "baked-dish", ["pork", "cabbage", "carrots", "potatoes"], "Chinese baking"),
        ("indian", "pasta", ["chicken", "tomatoes", "cream", "pasta"], "Indian pasta fusion"),
        ("japanese", "soup", ["tofu", "mushrooms", "seaweed", "noodles"], "Traditional Japanese"),
        
        # Complex (6+ ingredients)
        ("thai", "curry", ["shrimp", "coconut_milk", "bamboo_shoots", "peppers", "basil", "eggplant"], "Complex Thai"),
        ("french", "baked-dish", ["chicken", "potatoes", "carrots", "onions", "mushrooms", "wine"], "Complex French"),
        
        # Extreme fusion tests
        ("korean", "pasta", ["kimchi", "pork", "pasta", "cheese"], "Korean-Italian fusion"),
        ("moroccan", "stir-fry", ["lamb", "dates", "almonds", "couscous"], "Moroccan stir-fry"),
        
        # Vegetarian/Vegan tests
        ("indian", "curry", ["chickpeas", "spinach", "tomatoes", "potatoes"], "Vegetarian Indian"),
        ("ethiopian", "stew", ["lentils", "carrots", "potatoes"], "Ethiopian vegetarian"),
    ]
    
    report = {
        "test_date": datetime.now().isoformat(),
        "total_tests": len(test_cases),
        "results": []
    }
    
    print("A.I. CHEF QUALITY TEST REPORT")
    print("=" * 60)
    print(f"Testing {len(test_cases)} recipe combinations...")
    print("=" * 60)
    
    for cuisine, dish_type, ingredients, description in test_cases:
        print(f"\n🍳 Testing: {description}")
        print(f"   Input: {cuisine} {dish_type} with {ingredients}")
        
        # Generate recipe
        recipe = chef.generate_recipe(cuisine, dish_type, ingredients)
        
        # Evaluate quality
        evaluation = evaluate_recipe_quality(recipe, cuisine, dish_type, ingredients)
        
        # Add to report
        report["results"].append({
            "description": description,
            "input": {
                "cuisine": cuisine,
                "dish_type": dish_type,
                "ingredients": ingredients
            },
            "recipe": recipe,
            "evaluation": evaluation
        })
        
        # Print summary
        print(f"   ✅ Generated: {recipe.get('title', 'FAILED')}")
        print(f"   Quality Score: {evaluation['overall_score']}/100")
        if evaluation['issues']:
            print(f"   ⚠️  Issues: {', '.join(evaluation['issues'])}")
    
    # Save full report
    with open('ai_chef_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_score = sum(r['evaluation']['overall_score'] for r in report['results'])
    avg_score = total_score / len(report['results'])
    
    print(f"Average Quality Score: {avg_score:.1f}/100")
    
    # Count issues
    all_issues = []
    for r in report['results']:
        all_issues.extend(r['evaluation']['issues'])
    
    if all_issues:
        print(f"\nCommon Issues:")
        from collections import Counter
        issue_counts = Counter(all_issues)
        for issue, count in issue_counts.most_common(5):
            print(f"  - {issue}: {count} occurrences")
    
    print(f"\n📄 Full report saved to: ai_chef_quality_report.json")
    
    return report

def evaluate_recipe_quality(recipe, cuisine, dish_type, ingredients):
    """Evaluate a recipe's quality"""
    
    evaluation = {
        "overall_score": 100,  # Start perfect, deduct for issues
        "issues": [],
        "strengths": []
    }
    
    # Check 1: Has all required fields
    required_fields = ['title', 'ingredients', 'instructions', 'prep_time', 'cook_time']
    for field in required_fields:
        if field not in recipe or not recipe[field]:
            evaluation['issues'].append(f"Missing {field}")
            evaluation['overall_score'] -= 20
    
    # Check 2: Uses original ingredients
    recipe_ingredients = [ing.get('item', '').lower() for ing in recipe.get('ingredients', [])]
    for orig_ing in ingredients:
        if not any(orig_ing.lower() in ring for ring in recipe_ingredients):
            evaluation['issues'].append(f"Missing required ingredient: {orig_ing}")
            evaluation['overall_score'] -= 15
    
    # Check 3: Instructions make sense
    instructions = recipe.get('instructions', [])
    if len(instructions) < 3:
        evaluation['issues'].append("Too few instruction steps")
        evaluation['overall_score'] -= 10
    elif len(instructions) > 15:
        evaluation['issues'].append("Too many instruction steps")
        evaluation['overall_score'] -= 5
    
    # Check 4: Reasonable times
    try:
        prep = recipe.get('prep_time', '0')
        cook = recipe.get('cook_time', '0')
        prep_mins = int(''.join(filter(str.isdigit, prep)))
        cook_mins = int(''.join(filter(str.isdigit, cook)))
        
        if dish_type == 'stir-fry' and cook_mins > 30:
            evaluation['issues'].append("Stir-fry taking too long")
            evaluation['overall_score'] -= 10
        elif dish_type == 'soup' and cook_mins < 20:
            evaluation['issues'].append("Soup cooking too quickly")
            evaluation['overall_score'] -= 10
    except:
        pass
    
    # Check 5: Title creativity
    title = recipe.get('title', '')
    if cuisine.lower() not in title.lower() and not any(ing in title.lower() for ing in ingredients):
        evaluation['issues'].append("Title doesn't reflect cuisine or ingredients")
        evaluation['overall_score'] -= 5
    else:
        evaluation['strengths'].append("Good title")
    
    # Ensure score doesn't go below 0
    evaluation['overall_score'] = max(0, evaluation['overall_score'])
    
    return evaluation

if __name__ == "__main__":
    report = run_ai_chef_tests()
    