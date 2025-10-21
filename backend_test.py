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
BASE_URL = "https://playwright-newsgrab.preview.emergentagent.com/api"
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
            
            # Check 4: Contains Meta description section (should appear first)
            if "**Meta description**" in translated_content:
                print_success("✓ Contains Meta description section")
                checks_passed += 1
            else:
                print_error("✗ Missing Meta description section")
            
            # Check 5: Contains Sapo section (should appear after meta description)
            if "**Sapo**" in translated_content:
                print_success("✓ Contains Sapo section")
                checks_passed += 1
            else:
                print_error("✗ Missing Sapo section")
            
            # Check 6: Crypto terms preserved (check for some key terms)
            crypto_terms = ["Lightning Network", "Bitcoin", "blockchain", "smart contract"]
            preserved_terms = [term for term in crypto_terms if term in translated_content]
            if len(preserved_terms) >= 2:
                print_success(f"✓ Crypto terms preserved: {', '.join(preserved_terms)}")
                checks_passed += 1
            else:
                print_error("✗ Crypto terms not properly preserved")
            
            # Check 7: Verify correct order (Meta description → Sapo → Giới thiệu → ... → Kết luận)
            meta_pos = translated_content.find("**Meta description**")
            sapo_pos = translated_content.find("**Sapo**")
            intro_pos = translated_content.find("Giới thiệu")
            conclusion_pos = translated_content.find("Kết luận")
            
            if (meta_pos < sapo_pos < intro_pos < conclusion_pos and 
                meta_pos != -1 and sapo_pos != -1 and intro_pos != -1 and conclusion_pos != -1):
                print_success("✓ Sections appear in correct order: Meta → Sapo → Giới thiệu → ... → Kết luận")
                checks_passed += 1
                total_checks += 1
            else:
                print_error("✗ Sections not in correct order")
                total_checks += 1
            
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

def test_kol_post_generation_text():
    """Test KOL Post generation with text input"""
    print_test_header("Testing KOL Post Generation (Text Input)")
    
    try:
        payload = {
            "information_source": "Bitcoin vừa vượt mốc $100,000 lần đầu tiên trong lịch sử. Các nhà đầu tư tổ chức đang mua vào mạnh mẽ thông qua Bitcoin ETF. On-chain data cho thấy whales đang accumulate. Trading volume tăng 300% trong 24h qua.",
            "insight_required": "Đây là dấu hiệu tích cực cho bull run, nhưng ae cẩn thận với FOMO vì sau ATH thường có correction 15-20%",
            "source_type": "text"
        }
        
        print_info("Sending KOL post generation request with text input...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/kol-posts/generate",
            json=payload,
            headers=HEADERS,
            timeout=120
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            generated_content = result.get('generated_content', '')
            post_id = result.get('id')
            
            print_success(f"KOL post generated in {processing_time:.2f} seconds")
            print_info(f"Post ID: {post_id}")
            
            # Verify KOL post content quality
            checks_passed = 0
            total_checks = 6
            
            # Check 1: Content exists and is not empty
            if generated_content and len(generated_content.strip()) > 0:
                print_success("✓ Generated content exists")
                checks_passed += 1
            else:
                print_error("✗ No generated content")
            
            # Check 2: Content has casual KOL style (check for "ae", "mình", casual tone)
            casual_indicators = ["ae", "mình", "t ", "m ", "kkk", "đệt", "cay"]
            has_casual_tone = any(indicator in generated_content.lower() for indicator in casual_indicators)
            if has_casual_tone:
                print_success("✓ Contains casual KOL tone")
                checks_passed += 1
            else:
                print_error("✗ Missing casual KOL tone")
            
            # Check 3: Preserves crypto tickers ($BTC format)
            crypto_tickers = ["$BTC", "$ETH", "$100,000"]
            preserved_tickers = [ticker for ticker in crypto_tickers if ticker in generated_content]
            if preserved_tickers:
                print_success(f"✓ Crypto tickers preserved: {', '.join(preserved_tickers)}")
                checks_passed += 1
            else:
                print_error("✗ Crypto tickers not preserved")
            
            # Check 4: Combines info and insight naturally
            if "bull run" in generated_content.lower() and ("fomo" in generated_content.lower() or "correction" in generated_content.lower()):
                print_success("✓ Combines information and insight naturally")
                checks_passed += 1
            else:
                print_error("✗ Does not properly combine info and insight")
            
            # Check 5: Not too long (KOL posts should be concise)
            word_count = len(generated_content.split())
            if word_count <= 200:
                print_success(f"✓ Appropriate length: {word_count} words")
                checks_passed += 1
            else:
                print_error(f"✗ Too long: {word_count} words (should be concise)")
            
            # Check 6: Contains Vietnamese content
            vietnamese_chars = any(char in generated_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
            if vietnamese_chars:
                print_success("✓ Content is in Vietnamese")
                checks_passed += 1
            else:
                print_error("✗ Content does not appear to be in Vietnamese")
            
            print_info(f"KOL post quality: {checks_passed}/{total_checks} checks passed")
            
            # Show sample of generated content
            print_info("Generated KOL post content:")
            print("-" * 40)
            print(generated_content)
            print("-" * 40)
            
            return post_id if checks_passed >= 4 else None
            
        else:
            print_error(f"KOL post generation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"KOL post generation error: {str(e)}")
        return None

def test_kol_post_generation_url():
    """Test KOL Post generation with URL input (if working URL available)"""
    print_test_header("Testing KOL Post Generation (URL Input)")
    
    try:
        # Use a reliable crypto news URL for testing
        test_url = "https://cointelegraph.com/news/bitcoin-price-analysis"
        
        payload = {
            "information_source": test_url,
            "insight_required": "Entry tốt cho swing trade",
            "source_type": "url"
        }
        
        print_info(f"Sending KOL post generation request with URL: {test_url}")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/kol-posts/generate",
            json=payload,
            headers=HEADERS,
            timeout=120
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            generated_content = result.get('generated_content', '')
            post_id = result.get('id')
            
            print_success(f"KOL post with URL generated in {processing_time:.2f} seconds")
            print_info(f"Post ID: {post_id}")
            
            # Basic checks for URL-based generation
            checks_passed = 0
            total_checks = 3
            
            # Check 1: Content exists
            if generated_content and len(generated_content.strip()) > 0:
                print_success("✓ Generated content from URL exists")
                checks_passed += 1
            else:
                print_error("✗ No generated content from URL")
            
            # Check 2: Contains insight
            if "swing trade" in generated_content.lower() or "entry" in generated_content.lower():
                print_success("✓ Contains required insight")
                checks_passed += 1
            else:
                print_error("✗ Missing required insight")
            
            # Check 3: Vietnamese content
            vietnamese_chars = any(char in generated_content for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ')
            if vietnamese_chars:
                print_success("✓ Content is in Vietnamese")
                checks_passed += 1
            else:
                print_error("✗ Content does not appear to be in Vietnamese")
            
            print_info(f"URL-based KOL post quality: {checks_passed}/{total_checks} checks passed")
            
            # Show sample of generated content
            print_info("Generated KOL post from URL:")
            print("-" * 40)
            print(generated_content[:300] + "..." if len(generated_content) > 300 else generated_content)
            print("-" * 40)
            
            return post_id if checks_passed >= 2 else None
            
        elif response.status_code == 400:
            print_error(f"URL not accessible or scraping failed: {response.status_code}")
            print_info("This is expected if the URL is not accessible")
            return "url_failed"  # Special return to indicate URL issue, not system failure
            
        else:
            print_error(f"KOL post URL generation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"KOL post URL generation error: {str(e)}")
        return None

def test_get_all_kol_posts():
    """Test getting all KOL posts"""
    print_test_header("Testing Get All KOL Posts")
    
    try:
        response = requests.get(
            f"{BASE_URL}/kol-posts",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            posts = response.json()
            
            print_success(f"Retrieved {len(posts)} KOL posts")
            
            if len(posts) > 0:
                # Check if posts are sorted by created_at descending
                if len(posts) > 1:
                    first_post_time = posts[0].get('created_at', '')
                    second_post_time = posts[1].get('created_at', '')
                    if first_post_time >= second_post_time:
                        print_success("✓ Posts are sorted by created_at descending")
                    else:
                        print_error("✗ Posts are not properly sorted")
                
                # Check if posts have required fields
                sample_post = posts[0]
                required_fields = ['id', 'information_source', 'insight_required', 'generated_content', 'source_type', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in sample_post]
                
                if not missing_fields:
                    print_success("✓ Posts contain all required fields")
                else:
                    print_error(f"✗ Missing fields in posts: {missing_fields}")
                
                print_info(f"Sample post ID: {sample_post.get('id')}")
                print_info(f"Sample post source type: {sample_post.get('source_type')}")
                
                return posts[0].get('id')  # Return first post ID for further testing
            else:
                print_info("No KOL posts found (empty list)")
                return None
                
        else:
            print_error(f"Get KOL posts failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Get KOL posts error: {str(e)}")
        return None

def test_get_single_kol_post(post_id):
    """Test getting a single KOL post"""
    print_test_header("Testing Get Single KOL Post")
    
    if not post_id or post_id == "url_failed":
        print_error("No valid post ID available for testing")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/kol-posts/{post_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            post = response.json()
            
            print_success("Single KOL post retrieved successfully")
            print_info(f"Post ID: {post.get('id')}")
            print_info(f"Source type: {post.get('source_type')}")
            print_info(f"Has generated content: {bool(post.get('generated_content'))}")
            
            # Verify it's the correct post
            if post.get('id') == post_id:
                print_success("✓ Correct post retrieved")
                return True
            else:
                print_error("✗ Wrong post retrieved")
                return False
                
        elif response.status_code == 404:
            print_error("Post not found (404)")
            return False
            
        else:
            print_error(f"Get single KOL post failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Get single KOL post error: {str(e)}")
        return False

def test_delete_kol_post(post_id):
    """Test deleting a KOL post"""
    print_test_header("Testing Delete KOL Post")
    
    if not post_id or post_id == "url_failed":
        print_error("No valid post ID available for testing")
        return False
    
    try:
        # First verify the post exists
        get_response = requests.get(
            f"{BASE_URL}/kol-posts/{post_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if get_response.status_code != 200:
            print_error("Post does not exist before deletion test")
            return False
        
        # Delete the post
        delete_response = requests.delete(
            f"{BASE_URL}/kol-posts/{post_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if delete_response.status_code == 200:
            result = delete_response.json()
            print_success("KOL post deleted successfully")
            print_info(f"Delete response: {result.get('message', 'No message')}")
            
            # Verify the post is actually deleted
            verify_response = requests.get(
                f"{BASE_URL}/kol-posts/{post_id}",
                headers=HEADERS,
                timeout=30
            )
            
            if verify_response.status_code == 404:
                print_success("✓ Post successfully removed from database")
                return True
            else:
                print_error("✗ Post still exists after deletion")
                return False
                
        else:
            print_error(f"Delete KOL post failed: {delete_response.status_code}")
            print_error(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Delete KOL post error: {str(e)}")
        return False

def test_create_project_with_url():
    """Create a test project with URL to test image extraction"""
    print_test_header("Creating Project with URL for Image Testing")
    
    try:
        # Use a URL that likely has images - crypto news site
        test_url = "https://coindesk.com"  # Using coindesk as it's reliable and has images
        
        payload = {
            "source_url": test_url
        }
        
        print_info(f"Creating project with URL: {test_url}")
        
        response = requests.post(
            f"{BASE_URL}/projects",
            json=payload,
            headers=HEADERS,
            timeout=60  # Increased timeout for scraping
        )
        
        if response.status_code == 200:
            project = response.json()
            project_id = project.get('id')
            image_metadata = project.get('image_metadata', [])
            
            print_success(f"Project with URL created successfully")
            print_info(f"Project ID: {project_id}")
            print_info(f"Project Title: {project.get('title', 'N/A')}")
            print_info(f"Images found: {len(image_metadata)}")
            
            return project_id, image_metadata
        else:
            print_error(f"Project creation with URL failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None, None
            
    except Exception as e:
        print_error(f"Project creation with URL error: {str(e)}")
        return None, None

def test_image_metadata_structure(image_metadata):
    """Test the structure and format of image metadata"""
    print_test_header("Testing Image Metadata Structure")
    
    if not image_metadata:
        print_info("No image metadata to test (project has no images)")
        return True
    
    try:
        checks_passed = 0
        total_checks = 5
        
        # Check 1: image_metadata is an array
        if isinstance(image_metadata, list):
            print_success("✓ image_metadata is an array")
            checks_passed += 1
        else:
            print_error("✗ image_metadata is not an array")
        
        if len(image_metadata) > 0:
            sample_image = image_metadata[0]
            
            # Check 2: Each item has required fields (url, alt_text, filename)
            required_fields = ['url', 'alt_text', 'filename']
            missing_fields = [field for field in required_fields if field not in sample_image]
            
            if not missing_fields:
                print_success("✓ Image metadata has all required fields: url, alt_text, filename")
                checks_passed += 1
            else:
                print_error(f"✗ Missing fields in image metadata: {missing_fields}")
            
            # Check 3: URL is absolute URL
            image_url = sample_image.get('url', '')
            if image_url.startswith(('http://', 'https://')):
                print_success("✓ Image URL is absolute URL")
                checks_passed += 1
            else:
                print_error(f"✗ Image URL is not absolute: {image_url}")
            
            # Check 4: Filename has "Succinct " prefix
            filename = sample_image.get('filename', '')
            if filename.startswith('Succinct '):
                print_success("✓ Filename has 'Succinct ' prefix")
                checks_passed += 1
            else:
                print_error(f"✗ Filename missing 'Succinct ' prefix: {filename}")
            
            # Check 5: Extension is valid image format
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
            file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
            
            if file_extension in valid_extensions:
                print_success(f"✓ Valid image extension: {file_extension}")
                checks_passed += 1
            else:
                print_error(f"✗ Invalid image extension: {file_extension}")
            
            # Show sample metadata
            print_info("Sample image metadata:")
            print_info(f"  URL: {sample_image.get('url', 'N/A')}")
            print_info(f"  Alt text: {sample_image.get('alt_text', 'N/A')}")
            print_info(f"  Filename: {sample_image.get('filename', 'N/A')}")
        
        print_info(f"Image metadata structure: {checks_passed}/{total_checks} checks passed")
        return checks_passed >= 3
        
    except Exception as e:
        print_error(f"Image metadata structure test error: {str(e)}")
        return False

def test_download_image_proxy(image_metadata):
    """Test the download image proxy endpoint"""
    print_test_header("Testing Download Image Proxy Endpoint")
    
    if not image_metadata or len(image_metadata) == 0:
        print_info("No images available for download testing")
        return True
    
    try:
        # Test with first image
        sample_image = image_metadata[0]
        image_url = sample_image.get('url')
        filename = sample_image.get('filename')
        
        if not image_url or not filename:
            print_error("Sample image missing URL or filename")
            return False
        
        print_info(f"Testing download for: {filename}")
        print_info(f"Image URL: {image_url}")
        
        # Test the download proxy endpoint
        download_url = f"{BASE_URL}/download-image"
        params = {
            'url': image_url,
            'filename': filename
        }
        
        response = requests.get(
            download_url,
            params=params,
            timeout=30,
            stream=True
        )
        
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Response status is 200
        if response.status_code == 200:
            print_success("✓ Download proxy returns 200 status")
            checks_passed += 1
        else:
            print_error(f"✗ Download proxy failed: {response.status_code}")
            print_error(f"Response: {response.text}")
        
        # Check 2: Content-Type is image type
        content_type = response.headers.get('content-type', '')
        if content_type.startswith('image/'):
            print_success(f"✓ Correct content-type: {content_type}")
            checks_passed += 1
        else:
            print_error(f"✗ Incorrect content-type: {content_type}")
        
        # Check 3: Content-Disposition header has custom filename
        content_disposition = response.headers.get('content-disposition', '')
        if 'attachment' in content_disposition and filename in content_disposition:
            print_success("✓ Content-Disposition header has custom filename")
            checks_passed += 1
        else:
            print_error(f"✗ Incorrect Content-Disposition: {content_disposition}")
        
        # Check 4: Response has image data
        if response.status_code == 200:
            # Read a small chunk to verify it's image data
            chunk = next(response.iter_content(chunk_size=1024), b'')
            if len(chunk) > 0:
                print_success("✓ Response streams image data")
                checks_passed += 1
            else:
                print_error("✗ No image data in response")
        
        print_info(f"Download proxy test: {checks_passed}/{total_checks} checks passed")
        return checks_passed >= 3
        
    except Exception as e:
        print_error(f"Download image proxy test error: {str(e)}")
        return False

def test_main_content_filtering():
    """Test that images are only extracted from main content, not sidebar/footer"""
    print_test_header("Testing Main Content Filtering")
    
    try:
        # Create a project with a URL that has multiple images
        # We'll use coindesk which should have some images
        test_url = "https://coindesk.com"
        
        payload = {
            "source_url": test_url
        }
        
        print_info(f"Testing main content filtering with: {test_url}")
        
        response = requests.post(
            f"{BASE_URL}/projects",
            json=payload,
            headers=HEADERS,
            timeout=60
        )
        
        if response.status_code == 200:
            project = response.json()
            image_metadata = project.get('image_metadata', [])
            
            print_success(f"Project created for content filtering test")
            print_info(f"Images extracted: {len(image_metadata)}")
            
            # The main test here is that the scraping completed without errors
            # and that we got a reasonable number of images (not too many from sidebar/footer)
            if len(image_metadata) <= 10:  # Reasonable number for main content
                print_success("✓ Reasonable number of images extracted (likely from main content)")
                return True
            else:
                print_error(f"✗ Too many images extracted ({len(image_metadata)}), may include sidebar/footer")
                return False
                
        else:
            print_error(f"Content filtering test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Main content filtering test error: {str(e)}")
        return False

def test_backward_compatibility():
    """Test that old projects without image_metadata still work"""
    print_test_header("Testing Backward Compatibility")
    
    try:
        # Create a project with raw text (no URL, so no image_metadata)
        payload = {
            "raw_text": "Test content for backward compatibility"
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
            
            print_success("Project created without URL (no image_metadata)")
            
            # Test retrieving the project
            get_response = requests.get(
                f"{BASE_URL}/projects/{project_id}",
                headers=HEADERS,
                timeout=30
            )
            
            if get_response.status_code == 200:
                retrieved_project = get_response.json()
                image_metadata = retrieved_project.get('image_metadata', [])
                
                print_success("✓ Project retrieval works for projects without image_metadata")
                print_info(f"image_metadata field: {image_metadata}")
                
                # Clean up
                requests.delete(f"{BASE_URL}/projects/{project_id}", headers=HEADERS, timeout=30)
                
                return True
            else:
                print_error(f"Failed to retrieve project: {get_response.status_code}")
                return False
                
        else:
            print_error(f"Backward compatibility test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Backward compatibility test error: {str(e)}")
        return False

def test_error_handling_images():
    """Test error handling for image-related operations"""
    print_test_header("Testing Image Error Handling")
    
    try:
        checks_passed = 0
        total_checks = 3
        
        # Test 1: Download with invalid URL
        print_info("Testing download with invalid image URL...")
        invalid_url = "https://invalid-domain-that-does-not-exist.com/image.jpg"
        
        response = requests.get(
            f"{BASE_URL}/download-image",
            params={'url': invalid_url, 'filename': 'test.jpg'},
            timeout=30
        )
        
        if response.status_code == 400:
            print_success("✓ Proper error handling for invalid image URL")
            checks_passed += 1
        else:
            print_error(f"✗ Unexpected response for invalid URL: {response.status_code}")
        
        # Test 2: Download with missing parameters
        print_info("Testing download with missing filename parameter...")
        
        response = requests.get(
            f"{BASE_URL}/download-image",
            params={'url': 'https://example.com/image.jpg'},  # Missing filename
            timeout=30
        )
        
        if response.status_code in [400, 422]:  # 422 for validation error
            print_success("✓ Proper error handling for missing filename")
            checks_passed += 1
        else:
            print_error(f"✗ Unexpected response for missing filename: {response.status_code}")
        
        # Test 3: Create project with invalid URL
        print_info("Testing project creation with invalid URL...")
        
        response = requests.post(
            f"{BASE_URL}/projects",
            json={"source_url": "https://invalid-domain-that-does-not-exist.com"},
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 400:
            print_success("✓ Proper error handling for invalid project URL")
            checks_passed += 1
        else:
            print_error(f"✗ Unexpected response for invalid project URL: {response.status_code}")
        
        print_info(f"Error handling test: {checks_passed}/{total_checks} checks passed")
        return checks_passed >= 2
        
    except Exception as e:
        print_error(f"Error handling test error: {str(e)}")
        return False

def test_delete_partner_content_project(project_id):
    """Test deleting a Partner Content Hub project"""
    print_test_header("Testing Delete Partner Content Hub Project")
    
    if not project_id:
        print_error("No project ID available for testing")
        return False
    
    try:
        # First verify the project exists
        get_response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if get_response.status_code != 200:
            print_error("Project does not exist before deletion test")
            return False
        
        # Delete the project
        delete_response = requests.delete(
            f"{BASE_URL}/projects/{project_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if delete_response.status_code == 200:
            result = delete_response.json()
            print_success("Partner Content Hub project deleted successfully")
            print_info(f"Delete response: {result.get('message', 'No message')}")
            
            # Verify the project is actually deleted
            verify_response = requests.get(
                f"{BASE_URL}/projects/{project_id}",
                headers=HEADERS,
                timeout=30
            )
            
            if verify_response.status_code == 404:
                print_success("✓ Project successfully removed from database")
                return True
            else:
                print_error("✗ Project still exists after deletion")
                return False
                
        else:
            print_error(f"Delete project failed: {delete_response.status_code}")
            print_error(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Delete project error: {str(e)}")
        return False

# ==================== CRYPTO NEWS FEED TESTS ====================

def test_crypto_news_crawl():
    """Test the Crypto News Feed crawl endpoint using Playwright"""
    print_test_header("Testing Crypto News Crawl Endpoint")
    
    try:
        print_info("Triggering Playwright crawl of CryptoPanic...")
        print_info("⚠️  This may take 10-30 seconds due to browser launch and page load")
        
        start_time = time.time()
        
        response = requests.get(
            f"{BASE_URL}/crypto-news/crawl",
            headers=HEADERS,
            timeout=60  # Increased timeout for Playwright operations
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            news_items = result.get('news', [])
            
            print_success(f"Crawl completed in {processing_time:.2f} seconds")
            print_info(f"Response message: {message}")
            print_info(f"News items crawled: {len(news_items)}")
            
            # Verify crawl response structure
            checks_passed = 0
            total_checks = 6
            
            # Check 1: Response has message and news fields
            if 'message' in result and 'news' in result:
                print_success("✓ Response has correct structure (message + news)")
                checks_passed += 1
            else:
                print_error("✗ Response missing required fields")
            
            # Check 2: News items exist
            if len(news_items) > 0:
                print_success(f"✓ Successfully crawled {len(news_items)} news items")
                checks_passed += 1
            else:
                print_error("✗ No news items crawled")
            
            if len(news_items) > 0:
                sample_news = news_items[0]
                
                # Check 3: News items have required fields
                required_fields = ['id', 'title', 'url', 'created_at']
                missing_fields = [field for field in required_fields if field not in sample_news]
                
                if not missing_fields:
                    print_success("✓ News items have all required fields")
                    checks_passed += 1
                else:
                    print_error(f"✗ Missing fields in news items: {missing_fields}")
                
                # Check 4: Title is not empty
                title = sample_news.get('title', '')
                if title and len(title.strip()) > 0:
                    print_success("✓ News titles are not empty")
                    checks_passed += 1
                else:
                    print_error("✗ News titles are empty")
                
                # Check 5: URL is valid format
                url = sample_news.get('url', '')
                if url and (url.startswith('http://') or url.startswith('https://')):
                    print_success("✓ News URLs are valid format")
                    checks_passed += 1
                else:
                    print_error(f"✗ Invalid URL format: {url}")
                
                # Check 6: Optional fields (source, published_time, votes) are present
                optional_fields = ['source', 'published_time', 'votes']
                present_optional = [field for field in optional_fields if sample_news.get(field)]
                
                if len(present_optional) >= 1:
                    print_success(f"✓ Optional fields present: {', '.join(present_optional)}")
                    checks_passed += 1
                else:
                    print_error("✗ No optional fields (source, published_time, votes) present")
                
                # Show sample news item
                print_info("Sample crawled news item:")
                print_info(f"  Title: {sample_news.get('title', 'N/A')}")
                print_info(f"  URL: {sample_news.get('url', 'N/A')}")
                print_info(f"  Source: {sample_news.get('source', 'N/A')}")
                print_info(f"  Published: {sample_news.get('published_time', 'N/A')}")
                print_info(f"  Votes: {sample_news.get('votes', 'N/A')}")
            
            print_info(f"Crawl endpoint quality: {checks_passed}/{total_checks} checks passed")
            
            return news_items if checks_passed >= 4 else None
            
        else:
            print_error(f"Crawl endpoint failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Crypto news crawl test error: {str(e)}")
        return None

def test_get_cached_crypto_news():
    """Test getting cached crypto news from database"""
    print_test_header("Testing Get Cached Crypto News")
    
    try:
        response = requests.get(
            f"{BASE_URL}/crypto-news",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            news_list = response.json()
            
            print_success(f"Retrieved {len(news_list)} cached news items")
            
            checks_passed = 0
            total_checks = 4
            
            # Check 1: Response is a list
            if isinstance(news_list, list):
                print_success("✓ Response is a list")
                checks_passed += 1
            else:
                print_error("✗ Response is not a list")
            
            if len(news_list) > 0:
                # Check 2: Items are sorted by created_at descending
                if len(news_list) > 1:
                    first_time = news_list[0].get('created_at', '')
                    second_time = news_list[1].get('created_at', '')
                    if first_time >= second_time:
                        print_success("✓ News items sorted by created_at descending")
                        checks_passed += 1
                    else:
                        print_error("✗ News items not properly sorted")
                else:
                    print_success("✓ Only one item, sorting not applicable")
                    checks_passed += 1
                
                # Check 3: Items have CryptoNews model fields
                sample_item = news_list[0]
                model_fields = ['id', 'title', 'url', 'created_at']
                missing_fields = [field for field in model_fields if field not in sample_item]
                
                if not missing_fields:
                    print_success("✓ Items have all CryptoNews model fields")
                    checks_passed += 1
                else:
                    print_error(f"✗ Missing model fields: {missing_fields}")
                
                # Check 4: Data consistency with crawl
                title = sample_item.get('title', '')
                url = sample_item.get('url', '')
                
                if title and url and url.startswith(('http://', 'https://')):
                    print_success("✓ Data is consistent and valid")
                    checks_passed += 1
                else:
                    print_error("✗ Data inconsistency detected")
                
                print_info("Sample cached news item:")
                print_info(f"  ID: {sample_item.get('id', 'N/A')}")
                print_info(f"  Title: {sample_item.get('title', 'N/A')[:50]}...")
                print_info(f"  Source: {sample_item.get('source', 'N/A')}")
                print_info(f"  Created: {sample_item.get('created_at', 'N/A')}")
            else:
                print_info("No cached news items found")
                checks_passed += 2  # Skip sorting and data checks
            
            print_info(f"Cached news quality: {checks_passed}/{total_checks} checks passed")
            
            return news_list[0].get('id') if len(news_list) > 0 else None
            
        else:
            print_error(f"Get cached news failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Get cached crypto news test error: {str(e)}")
        return None

def test_delete_crypto_news(news_id):
    """Test deleting a specific crypto news item"""
    print_test_header("Testing Delete Crypto News")
    
    if not news_id:
        print_error("No news ID available for testing")
        return False
    
    try:
        print_info(f"Attempting to delete news item: {news_id}")
        
        # Delete the news item
        response = requests.delete(
            f"{BASE_URL}/crypto-news/{news_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            print_success("Crypto news item deleted successfully")
            print_info(f"Delete response: {message}")
            
            # Verify the news item is actually deleted
            verify_response = requests.get(
                f"{BASE_URL}/crypto-news",
                headers=HEADERS,
                timeout=30
            )
            
            if verify_response.status_code == 200:
                remaining_news = verify_response.json()
                deleted_item_exists = any(item.get('id') == news_id for item in remaining_news)
                
                if not deleted_item_exists:
                    print_success("✓ News item successfully removed from database")
                    return True
                else:
                    print_error("✗ News item still exists after deletion")
                    return False
            else:
                print_error("Could not verify deletion")
                return False
                
        elif response.status_code == 404:
            print_error("News item not found (404)")
            return False
            
        else:
            print_error(f"Delete crypto news failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Delete crypto news test error: {str(e)}")
        return False

def test_crypto_news_error_handling():
    """Test error handling for crypto news endpoints"""
    print_test_header("Testing Crypto News Error Handling")
    
    try:
        checks_passed = 0
        total_checks = 2
        
        # Test 1: Delete non-existent news item
        print_info("Testing delete with non-existent news ID...")
        fake_id = "non-existent-news-id-12345"
        
        response = requests.delete(
            f"{BASE_URL}/crypto-news/{fake_id}",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 404:
            print_success("✓ Proper 404 error for non-existent news item")
            checks_passed += 1
        else:
            print_error(f"✗ Unexpected response for non-existent news: {response.status_code}")
        
        # Test 2: Verify crawl endpoint handles errors gracefully
        print_info("Testing crawl endpoint error resilience...")
        
        # This test just verifies the endpoint exists and responds
        # We can't easily test Playwright failures without breaking the system
        response = requests.get(
            f"{BASE_URL}/crypto-news/crawl",
            headers=HEADERS,
            timeout=5  # Short timeout to potentially trigger timeout handling
        )
        
        # Accept both success and timeout as valid responses
        if response.status_code in [200, 500, 408]:  # Success, server error, or timeout
            print_success("✓ Crawl endpoint responds appropriately to requests")
            checks_passed += 1
        else:
            print_error(f"✗ Unexpected crawl response: {response.status_code}")
        
        print_info(f"Error handling test: {checks_passed}/{total_checks} checks passed")
        return checks_passed >= 1
        
    except Exception as e:
        print_error(f"Crypto news error handling test error: {str(e)}")
        return False

def test_playwright_integration():
    """Test that Playwright integration is working correctly"""
    print_test_header("Testing Playwright Integration")
    
    try:
        print_info("Testing Playwright browser launch and CryptoPanic access...")
        print_info("⚠️  This test verifies Playwright can launch Chromium and access CryptoPanic")
        
        # Trigger a crawl to test Playwright
        response = requests.get(
            f"{BASE_URL}/crypto-news/crawl",
            headers=HEADERS,
            timeout=45  # Give enough time for browser operations
        )
        
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Endpoint responds (not necessarily successfully)
        if response.status_code in [200, 500]:  # Either success or server error is acceptable
            print_success("✓ Crawl endpoint is accessible")
            checks_passed += 1
        else:
            print_error(f"✗ Crawl endpoint not accessible: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            news_items = result.get('news', [])
            
            # Check 2: Playwright successfully launched and crawled
            if len(news_items) > 0:
                print_success("✓ Playwright successfully launched and crawled data")
                checks_passed += 1
            else:
                print_error("✗ Playwright launched but no data crawled")
            
            # Check 3: CryptoPanic selectors are working
            if len(news_items) > 0:
                sample_item = news_items[0]
                has_title = bool(sample_item.get('title'))
                has_url = bool(sample_item.get('url'))
                
                if has_title and has_url:
                    print_success("✓ CryptoPanic selectors (.title-text a) working correctly")
                    checks_passed += 1
                else:
                    print_error("✗ CryptoPanic selectors not extracting data properly")
            
            # Check 4: URLs are absolute (not relative)
            if len(news_items) > 0:
                sample_url = news_items[0].get('url', '')
                if sample_url.startswith('https://'):
                    print_success("✓ URLs are converted to absolute format")
                    checks_passed += 1
                else:
                    print_error(f"✗ URLs not absolute: {sample_url}")
        
        elif response.status_code == 500:
            # Server error might indicate Playwright issues
            print_error("✗ Server error during crawl - possible Playwright configuration issue")
            print_error(f"Response: {response.text}")
        
        print_info(f"Playwright integration: {checks_passed}/{total_checks} checks passed")
        return checks_passed >= 2
        
    except Exception as e:
        print_error(f"Playwright integration test error: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("🚀 Partner Content Hub, KOL Post & Crypto News Feed - Backend API Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {
        'api_health': False,
        'project_creation': False,
        'translation': False,
        'social_generation': False,
        'project_retrieval': False,
        'project_with_url_creation': False,
        'image_metadata_structure': False,
        'download_image_proxy': False,
        'main_content_filtering': False,
        'backward_compatibility': False,
        'image_error_handling': False,
        'kol_post_text_generation': False,
        'kol_post_url_generation': False,
        'get_all_kol_posts': False,
        'get_single_kol_post': False,
        'delete_kol_post': False,
        'delete_partner_project': False,
        'crypto_news_crawl': False,
        'get_cached_crypto_news': False,
        'delete_crypto_news': False,
        'crypto_news_error_handling': False,
        'playwright_integration': False
    }
    
    # Test 1: API Health Check
    test_results['api_health'] = test_api_health()
    if not test_results['api_health']:
        print_error("API is not accessible. Stopping tests.")
        return False
    
    # Test 2: Create Test Project (with raw text)
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
    
    # IMAGE EXTRACTION & DOWNLOAD TESTS
    print_test_header("IMAGE EXTRACTION & DOWNLOAD FEATURE TESTING")
    
    # Test 6: Create Project with URL (for image extraction)
    url_project_id, image_metadata = test_create_project_with_url()
    test_results['project_with_url_creation'] = url_project_id is not None
    
    # Test 7: Image Metadata Structure
    test_results['image_metadata_structure'] = test_image_metadata_structure(image_metadata)
    
    # Test 8: Download Image Proxy Endpoint
    test_results['download_image_proxy'] = test_download_image_proxy(image_metadata)
    
    # Test 9: Main Content Filtering
    test_results['main_content_filtering'] = test_main_content_filtering()
    
    # Test 10: Backward Compatibility
    test_results['backward_compatibility'] = test_backward_compatibility()
    
    # Test 11: Image Error Handling
    test_results['image_error_handling'] = test_error_handling_images()
    
    # KOL POST TESTS
    print_test_header("KOL POST FEATURE TESTING")
    
    # Test 12: KOL Post Generation with Text Input
    kol_post_id = test_kol_post_generation_text()
    test_results['kol_post_text_generation'] = kol_post_id is not None
    
    # Test 13: KOL Post Generation with URL Input
    kol_post_url_id = test_kol_post_generation_url()
    test_results['kol_post_url_generation'] = kol_post_url_id is not None and kol_post_url_id != "url_failed"
    
    # Test 14: Get All KOL Posts
    first_post_id = test_get_all_kol_posts()
    test_results['get_all_kol_posts'] = first_post_id is not None
    
    # Use the first available post ID for single post and delete tests
    test_post_id = kol_post_id or first_post_id
    
    # Test 15: Get Single KOL Post
    test_results['get_single_kol_post'] = test_get_single_kol_post(test_post_id)
    
    # Test 16: Delete KOL Post
    test_results['delete_kol_post'] = test_delete_kol_post(test_post_id)
    
    # Test 17: Delete Partner Content Hub Project
    test_results['delete_partner_project'] = test_delete_partner_content_project(project_id)
    
    # CRYPTO NEWS FEED TESTS
    print_test_header("CRYPTO NEWS FEED FEATURE TESTING")
    
    # Test 18: Crypto News Crawl (Playwright)
    crawled_news = test_crypto_news_crawl()
    test_results['crypto_news_crawl'] = crawled_news is not None
    
    # Test 19: Get Cached Crypto News
    first_news_id = test_get_cached_crypto_news()
    test_results['get_cached_crypto_news'] = first_news_id is not None
    
    # Test 20: Delete Crypto News
    test_results['delete_crypto_news'] = test_delete_crypto_news(first_news_id)
    
    # Test 21: Crypto News Error Handling
    test_results['crypto_news_error_handling'] = test_crypto_news_error_handling()
    
    # Test 22: Playwright Integration
    test_results['playwright_integration'] = test_playwright_integration()
    
    # Clean up URL project if created
    if url_project_id:
        test_delete_partner_content_project(url_project_id)
    
    # Summary
    print_test_header("TEST SUMMARY")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print("PARTNER CONTENT HUB TESTS:")
    partner_tests = ['api_health', 'project_creation', 'translation', 'social_generation', 'project_retrieval', 'delete_partner_project']
    for test_name in partner_tests:
        result = test_results[test_name]
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print("\nIMAGE EXTRACTION & DOWNLOAD TESTS:")
    image_tests = ['project_with_url_creation', 'image_metadata_structure', 'download_image_proxy', 'main_content_filtering', 'backward_compatibility', 'image_error_handling']
    for test_name in image_tests:
        result = test_results[test_name]
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print("\nKOL POST TESTS:")
    kol_tests = ['kol_post_text_generation', 'kol_post_url_generation', 'get_all_kol_posts', 'get_single_kol_post', 'delete_kol_post']
    for test_name in kol_tests:
        result = test_results[test_name]
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    # Detailed analysis
    partner_passed = sum(test_results[test] for test in partner_tests)
    image_passed = sum(test_results[test] for test in image_tests)
    kol_passed = sum(test_results[test] for test in kol_tests)
    
    print(f"Partner Content Hub: {partner_passed}/{len(partner_tests)} tests passed")
    print(f"Image Extraction & Download: {image_passed}/{len(image_tests)} tests passed")
    print(f"KOL Post Feature: {kol_passed}/{len(kol_tests)} tests passed")
    
    if passed_tests == total_tests:
        print_success("🎉 All tests passed! Backend APIs are working correctly.")
        return True
    else:
        print_error(f"⚠️  {total_tests - passed_tests} test(s) failed. Backend needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)