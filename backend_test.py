#!/usr/bin/env python3
"""
Backend API Testing for Partner Content Hub
Tests the crypto content translation and social media generation endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://article-manager-7.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Sample English crypto content for testing
SAMPLE_CRYPTO_CONTENT = """
# Bitcoin's Lightning Network: Scaling Solutions for Mass Adoption

The Lightning Network represents one of the most promising scaling solutions for Bitcoin, enabling instant and low-cost transactions through off-chain payment channels. As Bitcoin continues to face scalability challenges with its base layer processing only 7 transactions per second, Layer 2 solutions like Lightning Network have become crucial for mainstream adoption.

## How Lightning Network Works

Lightning Network operates by creating payment channels between users, allowing them to conduct multiple transactions without broadcasting each one to the Bitcoin blockchain. These channels use smart contracts to ensure security and enable instant settlements. When users want to close a channel, the final balance is recorded on the main Bitcoin blockchain.

The network uses a routing mechanism that allows payments between users who don't have direct channels with each other. This creates a web of interconnected payment channels that can facilitate transactions across the entire network.

## Benefits and Challenges

The main advantages of Lightning Network include:
- Instant transactions with near-zero fees
- Improved privacy through onion routing
- Scalability to millions of transactions per second
- Micropayment capabilities

However, the network also faces several challenges:
- Liquidity management requirements
- Channel management complexity
- Need for users to be online for payments
- Centralization risks with large routing nodes

## Market Impact and Adoption

Major companies like Strike, Cash App, and various cryptocurrency exchanges have integrated Lightning Network support. El Salvador's adoption of Bitcoin as legal tender has also driven Lightning Network usage, with the government's Chivo wallet supporting Lightning payments.

The Total Value Locked (TVL) in Lightning Network has grown significantly, though exact measurements remain challenging due to the network's private nature. Recent developments include improved user interfaces and automated channel management tools that make Lightning more accessible to everyday users.

## Future Outlook

As Bitcoin's price volatility stabilizes and Lightning Network infrastructure matures, we can expect broader adoption among merchants and consumers. The development of Lightning-native applications and improved wallet experiences will likely drive the next wave of growth.

The success of Lightning Network could serve as a blueprint for other blockchain scaling solutions, demonstrating how Layer 2 technologies can address the blockchain trilemma of scalability, security, and decentralization.
"""

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

def test_api_health():
    """Test if the API is accessible"""
    print_test_header("API Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print_success(f"API is accessible: {response.json()}")
            return True
        else:
            print_error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API connection failed: {str(e)}")
        return False

def create_test_project():
    """Create a test project with crypto content"""
    print_test_header("Creating Test Project")
    
    try:
        payload = {
            "raw_text": SAMPLE_CRYPTO_CONTENT
        }
        
        response = requests.post(
            f"{BASE_URL}/projects",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            project = response.json()
            project_id = project.get('id')
            print_success(f"Project created successfully")
            print_info(f"Project ID: {project_id}")
            print_info(f"Project Title: {project.get('title', 'N/A')}")
            return project_id
        else:
            print_error(f"Project creation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Project creation error: {str(e)}")
        return None

def test_translate_endpoint(project_id):
    """Test the crypto content translation endpoint"""
    print_test_header("Testing Translation Endpoint")
    
    try:
        payload = {
            "content": SAMPLE_CRYPTO_CONTENT
        }
        
        print_info("Sending translation request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/translate",
            json=payload,
            headers=HEADERS,
            timeout=120  # Increased timeout for LLM processing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            translated_content = result.get('translated_content', '')
            
            print_success(f"Translation completed in {processing_time:.2f} seconds")
            
            # Verify Vietnamese content structure
            checks_passed = 0
            total_checks = 6
            
            # Check 1: Content is in Vietnamese (contains Vietnamese characters)
            vietnamese_chars = any(char in translated_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
            if vietnamese_chars:
                print_success("✓ Content contains Vietnamese characters")
                checks_passed += 1
            else:
                print_error("✗ Content does not appear to be in Vietnamese")
            
            # Check 2: Contains "Giới thiệu" section
            if "Giới thiệu" in translated_content:
                print_success("✓ Contains 'Giới thiệu' section")
                checks_passed += 1
            else:
                print_error("✗ Missing 'Giới thiệu' section")
            
            # Check 3: Contains "Kết luận" section
            if "Kết luận" in translated_content:
                print_success("✓ Contains 'Kết luận' section")
                checks_passed += 1
            else:
                print_error("✗ Missing 'Kết luận' section")
            
            # Check 4: Contains [SAPO] section
            if "[SAPO]" in translated_content:
                print_success("✓ Contains [SAPO] section")
                checks_passed += 1
            else:
                print_error("✗ Missing [SAPO] section")
            
            # Check 5: Contains [META] section
            if "[META]" in translated_content:
                print_success("✓ Contains [META] section")
                checks_passed += 1
            else:
                print_error("✗ Missing [META] section")
            
            # Check 6: Crypto terms preserved (check for some key terms)
            crypto_terms = ["Lightning Network", "Bitcoin", "blockchain", "smart contract"]
            preserved_terms = [term for term in crypto_terms if term in translated_content]
            if len(preserved_terms) >= 2:
                print_success(f"✓ Crypto terms preserved: {', '.join(preserved_terms)}")
                checks_passed += 1
            else:
                print_error("✗ Crypto terms not properly preserved")
            
            print_info(f"Translation quality: {checks_passed}/{total_checks} checks passed")
            
            # Show sample of translated content
            print_info("Sample of translated content:")
            print("-" * 40)
            print(translated_content[:500] + "..." if len(translated_content) > 500 else translated_content)
            print("-" * 40)
            
            return translated_content if checks_passed >= 4 else None
            
        else:
            print_error(f"Translation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Translation test error: {str(e)}")
        return None

def test_social_endpoint(project_id, translated_content):
    """Test the social media content generation endpoint"""
    print_test_header("Testing Social Content Generation")
    
    try:
        payload = {
            "content": translated_content
        }
        
        print_info("Sending social content generation request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/social",
            json=payload,
            headers=HEADERS,
            timeout=120  # Increased timeout for LLM processing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            facebook_content = result.get('facebook', '')
            
            print_success(f"Social content generated in {processing_time:.2f} seconds")
            
            # Verify Vietnamese social content structure
            checks_passed = 0
            total_checks = 5
            
            # Check 1: Content exists and is not empty
            if facebook_content and len(facebook_content.strip()) > 0:
                print_success("✓ Facebook content generated")
                checks_passed += 1
            else:
                print_error("✗ No Facebook content generated")
            
            # Check 2: Content is approximately 100 words (50-150 words acceptable)
            word_count = len(facebook_content.split())
            if 50 <= word_count <= 150:
                print_success(f"✓ Word count appropriate: {word_count} words")
                checks_passed += 1
            else:
                print_error(f"✗ Word count out of range: {word_count} words (expected 50-150)")
            
            # Check 3: Content is in Vietnamese
            vietnamese_chars = any(char in facebook_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
            if vietnamese_chars:
                print_success("✓ Content is in Vietnamese")
                checks_passed += 1
            else:
                print_error("✗ Content does not appear to be in Vietnamese")
            
            # Check 4: Contains call-to-action elements (common Vietnamese CTA phrases)
            cta_phrases = ["đọc thêm", "tìm hiểu", "xem chi tiết", "GFI Research", "bài viết đầy đủ"]
            has_cta = any(phrase.lower() in facebook_content.lower() for phrase in cta_phrases)
            if has_cta:
                print_success("✓ Contains call-to-action elements")
                checks_passed += 1
            else:
                print_error("✗ Missing call-to-action elements")
            
            # Check 5: Professional tone (no excessive exclamation marks or informal language)
            exclamation_count = facebook_content.count('!')
            if exclamation_count <= 2:
                print_success("✓ Professional tone maintained")
                checks_passed += 1
            else:
                print_error("✗ Tone appears too informal or promotional")
            
            print_info(f"Social content quality: {checks_passed}/{total_checks} checks passed")
            
            # Show the generated social content
            print_info("Generated social media content:")
            print("-" * 40)
            print(facebook_content)
            print("-" * 40)
            
            return checks_passed >= 3
            
        else:
            print_error(f"Social content generation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Social content test error: {str(e)}")
        return False

def test_project_retrieval(project_id):
    """Test retrieving the updated project"""
    print_test_header("Testing Project Retrieval")
    
    try:
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            project = response.json()
            
            has_translated = bool(project.get('translated_content'))
            has_social = bool(project.get('social_content'))
            
            print_success("Project retrieved successfully")
            print_info(f"Has translated content: {has_translated}")
            print_info(f"Has social content: {has_social}")
            
            if has_translated and has_social:
                print_success("✓ All content types are stored in database")
                return True
            else:
                print_error("✗ Some content missing from database")
                return False
                
        else:
            print_error(f"Project retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Project retrieval error: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("🚀 Partner Content Hub - Backend API Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {
        'api_health': False,
        'project_creation': False,
        'translation': False,
        'social_generation': False,
        'project_retrieval': False
    }
    
    # Test 1: API Health Check
    test_results['api_health'] = test_api_health()
    if not test_results['api_health']:
        print_error("API is not accessible. Stopping tests.")
        return False
    
    # Test 2: Create Test Project
    project_id = create_test_project()
    test_results['project_creation'] = project_id is not None
    if not project_id:
        print_error("Cannot create test project. Stopping tests.")
        return False
    
    # Test 3: Translation Endpoint
    translated_content = test_translate_endpoint(project_id)
    test_results['translation'] = translated_content is not None
    
    # Test 4: Social Content Generation (only if translation succeeded)
    if translated_content:
        test_results['social_generation'] = test_social_endpoint(project_id, translated_content)
    else:
        print_error("Skipping social content test due to translation failure")
    
    # Test 5: Project Retrieval
    test_results['project_retrieval'] = test_project_retrieval(project_id)
    
    # Summary
    print_test_header("TEST SUMMARY")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print_success("🎉 All tests passed! Backend APIs are working correctly.")
        return True
    else:
        print_error(f"⚠️  {total_tests - passed_tests} test(s) failed. Backend needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)