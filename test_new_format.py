#!/usr/bin/env python3
"""
Test the NEW translation format for Partner Content Hub
Verifies the updated structure: Meta description → Sapo → Giới thiệu → ... → Kết luận
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://datascan.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_new_translation_format():
    """Test the new translation format with existing project"""
    print_test_header("Testing NEW Translation Format")
    
    try:
        # Get recent projects to find one with translated content
        response = requests.get(f"{BASE_URL}/projects", timeout=10)
        if response.status_code != 200:
            print_error(f"Failed to get projects: {response.status_code}")
            return False
            
        projects = response.json()
        
        # Find a project with translated content
        test_project = None
        for project in projects:
            if project.get('translated_content'):
                test_project = project
                break
        
        if not test_project:
            print_error("No project with translated content found")
            return False
            
        project_id = test_project['id']
        translated_content = test_project['translated_content']
        
        print_info(f"Testing project: {project_id}")
        print_info(f"Content length: {len(translated_content)} characters")
        
        # Verify NEW format structure
        checks_passed = 0
        total_checks = 8
        
        # Check 1: Content is in Vietnamese (contains Vietnamese characters)
        vietnamese_chars = any(char in translated_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
        if vietnamese_chars:
            print_success("✓ Content contains Vietnamese characters")
            checks_passed += 1
        else:
            print_error("✗ Content does not appear to be in Vietnamese")
        
        # Check 2: Contains Meta description section (should appear first)
        if "**Meta description**" in translated_content:
            print_success("✓ Contains Meta description section")
            checks_passed += 1
        else:
            print_error("✗ Missing Meta description section")
        
        # Check 3: Contains Sapo section (should appear after meta description)
        if "**Sapo**" in translated_content:
            print_success("✓ Contains Sapo section")
            checks_passed += 1
        else:
            print_error("✗ Missing Sapo section")
        
        # Check 4: Contains "Giới thiệu" section
        if "Giới thiệu" in translated_content:
            print_success("✓ Contains 'Giới thiệu' section")
            checks_passed += 1
        else:
            print_error("✗ Missing 'Giới thiệu' section")
        
        # Check 5: Contains "Kết luận" section
        if "Kết luận" in translated_content:
            print_success("✓ Contains 'Kết luận' section")
            checks_passed += 1
        else:
            print_error("✗ Missing 'Kết luận' section")
        
        # Check 6: Verify correct order (Meta description → Sapo → Giới thiệu → ... → Kết luận)
        meta_pos = translated_content.find("**Meta description**")
        sapo_pos = translated_content.find("**Sapo**")
        intro_pos = translated_content.find("Giới thiệu")
        conclusion_pos = translated_content.find("Kết luận")
        
        if (meta_pos < sapo_pos < intro_pos < conclusion_pos and 
            meta_pos != -1 and sapo_pos != -1 and intro_pos != -1 and conclusion_pos != -1):
            print_success("✓ Sections appear in correct order: Meta → Sapo → Giới thiệu → ... → Kết luận")
            checks_passed += 1
        else:
            print_error("✗ Sections not in correct order")
            print_info(f"Positions: Meta({meta_pos}), Sapo({sapo_pos}), Giới thiệu({intro_pos}), Kết luận({conclusion_pos})")
        
        # Check 7: Crypto terms preserved (check for some key terms)
        crypto_terms = ["Lightning Network", "Bitcoin", "blockchain", "Smart Contract", "Layer 2"]
        preserved_terms = [term for term in crypto_terms if term in translated_content]
        if len(preserved_terms) >= 2:
            print_success(f"✓ Crypto terms preserved: {', '.join(preserved_terms)}")
            checks_passed += 1
        else:
            print_error("✗ Crypto terms not properly preserved")
        
        # Check 8: Meta description and Sapo are approximately 100 words each
        meta_section = ""
        sapo_section = ""
        
        if meta_pos != -1 and sapo_pos != -1:
            meta_section = translated_content[meta_pos:sapo_pos].replace("**Meta description**", "").strip()
            
        if sapo_pos != -1 and intro_pos != -1:
            sapo_section = translated_content[sapo_pos:intro_pos].replace("**Sapo**", "").strip()
        
        meta_words = len(meta_section.split()) if meta_section else 0
        sapo_words = len(sapo_section.split()) if sapo_section else 0
        
        if 80 <= meta_words <= 120 and 80 <= sapo_words <= 120:
            print_success(f"✓ Meta description ({meta_words} words) and Sapo ({sapo_words} words) are appropriate length")
            checks_passed += 1
        else:
            print_error(f"✗ Meta description ({meta_words} words) or Sapo ({sapo_words} words) length not optimal (expected ~100 words each)")
        
        print_info(f"NEW FORMAT QUALITY: {checks_passed}/{total_checks} checks passed")
        
        # Show structure preview
        print_info("Content structure preview:")
        print("-" * 50)
        lines = translated_content.split('\n')
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            if line.strip():
                print(f"{i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
        print("-" * 50)
        
        return checks_passed >= 6  # Pass if at least 6/8 checks pass
        
    except Exception as e:
        print_error(f"Format test error: {str(e)}")
        return False

def test_social_content_format():
    """Test social content format"""
    print_test_header("Testing Social Content Format")
    
    try:
        # Get recent projects to find one with social content
        response = requests.get(f"{BASE_URL}/projects", timeout=10)
        if response.status_code != 200:
            print_error(f"Failed to get projects: {response.status_code}")
            return False
            
        projects = response.json()
        
        # Find a project with social content
        test_project = None
        for project in projects:
            if project.get('social_content') and project.get('social_content', {}).get('facebook'):
                test_project = project
                break
        
        if not test_project:
            print_error("No project with social content found")
            return False
            
        project_id = test_project['id']
        social_content = test_project['social_content']['facebook']
        
        print_info(f"Testing social content from project: {project_id}")
        
        # Verify social content quality
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Content exists and is not empty
        if social_content and len(social_content.strip()) > 0:
            print_success("✓ Social content exists")
            checks_passed += 1
        else:
            print_error("✗ No social content found")
        
        # Check 2: Content is in Vietnamese
        vietnamese_chars = any(char in social_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
        if vietnamese_chars:
            print_success("✓ Social content is in Vietnamese")
            checks_passed += 1
        else:
            print_error("✗ Social content does not appear to be in Vietnamese")
        
        # Check 3: Word count appropriate (50-150 words)
        word_count = len(social_content.split())
        if 50 <= word_count <= 150:
            print_success(f"✓ Word count appropriate: {word_count} words")
            checks_passed += 1
        else:
            print_error(f"✗ Word count out of range: {word_count} words (expected 50-150)")
        
        # Check 4: Contains CTA elements
        cta_phrases = ["đọc thêm", "tìm hiểu", "xem chi tiết", "GFI Research", "bài viết đầy đủ", "phân tích"]
        has_cta = any(phrase.lower() in social_content.lower() for phrase in cta_phrases)
        if has_cta:
            print_success("✓ Contains call-to-action elements")
            checks_passed += 1
        else:
            print_error("✗ Missing call-to-action elements")
        
        print_info(f"SOCIAL CONTENT QUALITY: {checks_passed}/{total_checks} checks passed")
        
        # Show social content
        print_info("Generated social content:")
        print("-" * 50)
        print(social_content)
        print("-" * 50)
        
        return checks_passed >= 3
        
    except Exception as e:
        print_error(f"Social content test error: {str(e)}")
        return False

def main():
    """Run format verification tests"""
    print("🚀 Partner Content Hub - NEW FORMAT Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    test_results = {
        'translation_format': False,
        'social_format': False
    }
    
    # Test 1: New Translation Format
    test_results['translation_format'] = test_new_translation_format()
    
    # Test 2: Social Content Format
    test_results['social_format'] = test_social_content_format()
    
    # Summary
    print_test_header("FINAL TEST SUMMARY")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print_success("🎉 NEW FORMAT is working perfectly! All requirements met.")
        return True
    else:
        print_error(f"⚠️  {total_tests - passed_tests} test(s) failed. Format needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)