#!/usr/bin/env python3
"""
News Distributor Auto-Extract Feature Testing
Focused testing for the auto-extract functionality as requested in the review
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://news-sync-debug.preview.emergentagent.com/api"
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

def test_news_distributor_articles():
    """Test if RSS articles exist in database"""
    print_test_header("Step 1: Check if RSS articles exist in database")
    
    try:
        response = requests.get(
            f"{BASE_URL}/news-distributor/articles",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            articles = result.get('articles', [])
            total = result.get('total', 0)
            
            print_success(f"Articles endpoint working: {total} articles found")
            
            if total > 0:
                sample_article = articles[0]
                print_info(f"Sample article: {sample_article.get('title', 'N/A')[:50]}...")
                print_info(f"Article ID: {sample_article.get('id', 'N/A')}")
                print_info(f"Published date: {sample_article.get('published_date', 'N/A')}")
                return True, articles
            else:
                print_error("No articles found in database")
                return False, []
                
        else:
            print_error(f"Articles endpoint failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, []
            
    except Exception as e:
        print_error(f"Articles test error: {str(e)}")
        return False, []

def test_available_dates():
    """Test available dates endpoint"""
    print_test_header("Step 2: Check if available dates endpoint works")
    
    try:
        response = requests.get(
            f"{BASE_URL}/news-distributor/available-dates",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            dates = result.get('dates', [])
            
            print_success(f"Available dates endpoint working: {len(dates)} dates found")
            
            if len(dates) > 0:
                print_info(f"Available dates: {dates[:5]}{'...' if len(dates) > 5 else ''}")
                return True, dates
            else:
                print_error("No dates available")
                return False, []
                
        else:
            print_error(f"Available dates endpoint failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, []
            
    except Exception as e:
        print_error(f"Available dates test error: {str(e)}")
        return False, []

def test_auto_extract_no_date():
    """Test auto-extract endpoint without date filter"""
    print_test_header("Step 3: Test auto-extract endpoint without date filter")
    
    try:
        print_info("Testing auto-extract without date parameter...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/news-distributor/auto-extract",
            headers=HEADERS,
            timeout=300  # Extended timeout for processing multiple articles
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print_info(f"Auto-extract request completed in {processing_time:.2f} seconds")
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print_success("Auto-extract (no date) completed successfully")
            
            # Show detailed results
            total_articles = result.get('total_articles', 0)
            processed_articles = result.get('processed_articles', 0)
            new_vocab_count = result.get('new_vocab_count', 0)
            total_vocab_count = result.get('total_vocab_count', 0)
            output_content = result.get('output_content', '')
            
            print_info(f"Total articles: {total_articles}")
            print_info(f"Processed articles: {processed_articles}")
            print_info(f"New vocabulary: {new_vocab_count}")
            print_info(f"Total vocabulary: {total_vocab_count}")
            
            if output_content:
                print_info("Sample output content:")
                print("-" * 40)
                print(output_content[:500] + "..." if len(output_content) > 500 else output_content)
                print("-" * 40)
            
            return True, result
            
        else:
            print_error(f"Auto-extract (no date) failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Auto-extract (no date) test error: {str(e)}")
        return False, None

def test_auto_extract_with_date(selected_date):
    """Test auto-extract endpoint with specific date filter"""
    print_test_header("Step 4: Test auto-extract with specific date filter")
    
    if not selected_date:
        print_error("No date available for testing")
        return False, None
    
    try:
        print_info(f"Testing auto-extract with date: {selected_date}")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/news-distributor/auto-extract?selected_date={selected_date}",
            headers=HEADERS,
            timeout=300
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print_info(f"Auto-extract with date request completed in {processing_time:.2f} seconds")
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print_success("Auto-extract (with date) completed successfully")
            
            # Show detailed results
            total_articles = result.get('total_articles', 0)
            processed_articles = result.get('processed_articles', 0)
            new_vocab_count = result.get('new_vocab_count', 0)
            total_vocab_count = result.get('total_vocab_count', 0)
            output_content = result.get('output_content', '')
            
            print_info(f"Total articles for {selected_date}: {total_articles}")
            print_info(f"Processed articles: {processed_articles}")
            print_info(f"New vocabulary: {new_vocab_count}")
            print_info(f"Total vocabulary: {total_vocab_count}")
            
            if output_content:
                print_info("Sample output content:")
                print("-" * 40)
                print(output_content[:500] + "..." if len(output_content) > 500 else output_content)
                print("-" * 40)
            
            return True, result
            
        else:
            print_error(f"Auto-extract (with date) failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Auto-extract (with date) test error: {str(e)}")
        return False, None

def check_backend_logs():
    """Check backend logs for auto-extract errors"""
    print_test_header("Step 5: Check backend logs for errors")
    
    try:
        import subprocess
        
        print_info("Checking backend logs for auto-extract related errors...")
        
        # Get recent logs
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for specific error patterns
            error_patterns = [
                "Auto-extraction error",
                "Failed to auto-extract",
                "AIzaSyDWdYyrmShutcw7LID_MFeKWl2tWhwBccc",
                "rate limit",
                "quota",
                "overload",
                "503",
                "UNAVAILABLE"
            ]
            
            found_errors = []
            relevant_lines = []
            
            lines = log_content.split('\n')
            for line in lines:
                if any(pattern.lower() in line.lower() for pattern in error_patterns):
                    found_errors.append(line)
                    relevant_lines.append(line)
            
            if found_errors:
                print_error(f"Found {len(found_errors)} error-related log entries")
                print_info("Recent error logs:")
                print("-" * 40)
                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                    print(line)
                print("-" * 40)
                return False
            else:
                print_success("No auto-extract related errors found in recent logs")
                return True
        else:
            print_error("Could not read backend logs")
            return False
            
    except Exception as e:
        print_error(f"Backend log check error: {str(e)}")
        return False

def test_gemini_api_key():
    """Test if the Gemini API key is working by testing vocabulary extraction"""
    print_test_header("Step 6: Test Gemini API key functionality")
    
    try:
        # First get an article to test with
        articles_response = requests.get(
            f"{BASE_URL}/news-distributor/articles",
            headers=HEADERS,
            timeout=30
        )
        
        if articles_response.status_code == 200:
            articles_data = articles_response.json()
            articles = articles_data.get('articles', [])
            
            if len(articles) > 0:
                article_id = articles[0].get('id')
                article_title = articles[0].get('title', 'N/A')
                
                print_info(f"Testing Gemini API key with article: {article_title[:50]}...")
                
                # Test vocabulary extraction (this uses the Gemini API key)
                vocab_response = requests.post(
                    f"{BASE_URL}/news-distributor/extract-vocabulary/{article_id}",
                    headers=HEADERS,
                    timeout=120
                )
                
                if vocab_response.status_code == 200:
                    result = vocab_response.json()
                    new_vocab = result.get('new_vocab_count', 0)
                    print_success(f"Gemini API key is working (extracted {new_vocab} vocabulary)")
                    return True
                else:
                    print_error(f"Gemini API key may have issues: {vocab_response.status_code}")
                    print_error(f"Response: {vocab_response.text}")
                    
                    # Check if it's specifically an API key or rate limit issue
                    response_text = vocab_response.text.lower()
                    if "overloaded" in response_text or "503" in response_text:
                        print_info("This appears to be a rate limit/overload issue, not an API key problem")
                    elif "api key" in response_text or "unauthorized" in response_text:
                        print_error("This appears to be an API key issue")
                    
                    return False
            else:
                print_info("No articles available to test Gemini API key")
                return True
        else:
            print_error(f"Could not get articles to test API key: {articles_response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Gemini API key test error: {str(e)}")
        return False

def main():
    """Run focused News Distributor auto-extract tests"""
    print("🎯 NEWS DISTRIBUTOR AUTO-EXTRACT FEATURE TESTING")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nFOCUS: Finding why auto-extract is not working")
    
    # Test results tracking
    results = {}
    
    # Step 0: API Health Check
    results['api_health'] = test_api_health()
    if not results['api_health']:
        print_error("API is not accessible - stopping tests")
        return
    
    # Step 1: Check if RSS articles exist
    results['articles_exist'], articles = test_news_distributor_articles()
    
    # Step 2: Check available dates endpoint
    results['available_dates'], dates = test_available_dates()
    
    # Step 3: Test auto-extract without date filter
    results['auto_extract_no_date'], no_date_result = test_auto_extract_no_date()
    
    # Step 4: Test auto-extract with specific date
    if dates and len(dates) > 0:
        selected_date = dates[0]  # Use most recent date
        results['auto_extract_with_date'], date_result = test_auto_extract_with_date(selected_date)
    else:
        print_info("Skipping date-filtered test (no dates available)")
        results['auto_extract_with_date'] = None
    
    # Step 5: Check backend logs
    results['backend_logs_clean'] = check_backend_logs()
    
    # Step 6: Test Gemini API key
    results['gemini_api_working'] = test_gemini_api_key()
    
    # Summary
    print("\n" + "="*80)
    print("📋 NEWS DISTRIBUTOR AUTO-EXTRACT DIAGNOSTIC SUMMARY")
    print("="*80)
    
    print(f"✅ API Health: {'PASS' if results['api_health'] else 'FAIL'}")
    print(f"✅ RSS Articles Exist: {'PASS' if results['articles_exist'] else 'FAIL'}")
    print(f"✅ Available Dates Endpoint: {'PASS' if results['available_dates'] else 'FAIL'}")
    print(f"✅ Auto-Extract (No Date): {'PASS' if results['auto_extract_no_date'] else 'FAIL'}")
    
    if results['auto_extract_with_date'] is not None:
        print(f"✅ Auto-Extract (With Date): {'PASS' if results['auto_extract_with_date'] else 'FAIL'}")
    else:
        print(f"⏭️ Auto-Extract (With Date): SKIPPED")
    
    print(f"✅ Backend Logs Clean: {'PASS' if results['backend_logs_clean'] else 'FAIL'}")
    print(f"✅ Gemini API Key Working: {'PASS' if results['gemini_api_working'] else 'FAIL'}")
    
    # Diagnosis
    print("\n🔍 DIAGNOSIS:")
    
    if not results['articles_exist']:
        print("❌ ISSUE: No RSS articles in database - need to refresh RSS feed first")
    elif not results['available_dates']:
        print("❌ ISSUE: Available dates endpoint not working")
    elif not results['auto_extract_no_date']:
        print("❌ ISSUE: Auto-extract endpoint not working (without date filter)")
    elif not results['gemini_api_working']:
        print("❌ ISSUE: Gemini API key not working or rate limited")
    elif not results['backend_logs_clean']:
        print("⚠️ WARNING: Found errors in backend logs - check above for details")
    else:
        print("✅ All tests passed - auto-extract feature appears to be working")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()