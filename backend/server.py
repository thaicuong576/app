from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import aiofiles
from PIL import Image
import io
import asyncio
from urllib.parse import urljoin, urlparse
from emergentintegrations.llm.chat import LlmChat, UserMessage
import unicodedata
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Multiple Google API Keys for failover
GOOGLE_API_KEYS = [
    "AIzaSyDZaFsKqNMXs-Ni2Cr-w9hHhUqPqB8gKjs",
    "AIzaSyD4Nz1llcsVKkiWv2txzpAJnf_i6QqQl3I",
    "AIzaSyDhMC5X_es42QaUnDQi9YwwtaVLYcSpiE4"
]

# API Key Manager for automatic failover
class APIKeyManager:
    """Manages multiple API keys with automatic failover on rate limits"""
    
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.current_index = 0
    
    def get_current_key(self) -> str:
        """Get the current API key"""
        return self.keys[self.current_index]
    
    def get_next_key(self) -> str:
        """Rotate to the next API key"""
        self.current_index = (self.current_index + 1) % len(self.keys)
        return self.keys[self.current_index]
    
    def reset(self):
        """Reset to the first key"""
        self.current_index = 0
    
    async def try_with_all_keys(self, func, *args, **kwargs):
        """
        Try executing a function with all available API keys.
        Automatically switches to next key on rate limit or quota errors.
        """
        last_error = None
        attempted_keys = []
        
        for attempt in range(len(self.keys)):
            current_key = self.get_current_key()
            attempted_keys.append(current_key[-4:])  # Log last 4 chars for debugging
            
            try:
                logging.info(f"Attempting API call with key ending in ...{current_key[-4:]} (attempt {attempt + 1}/{len(self.keys)})")
                result = await func(current_key, *args, **kwargs)
                logging.info(f"✅ Success with key ending in ...{current_key[-4:]}")
                # Success! Rotate to next key for next call (round-robin)
                self.get_next_key()
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                last_error = e
                
                # Check if it's a rate limit or quota error
                if any(keyword in error_msg for keyword in ['rate limit', 'quota', 'overload', '429', 'resource exhausted', 'too many requests']):
                    logging.warning(f"⚠️ Rate limit/quota error with key ...{current_key[-4:]}: {str(e)[:100]}")
                    # Try next key
                    self.get_next_key()
                    continue
                else:
                    # For other errors, don't try other keys (likely a code/input issue)
                    logging.error(f"❌ Non-recoverable error with key ...{current_key[-4:]}: {str(e)[:100]}")
                    raise e
        
        # All keys failed
        logging.error(f"❌ All {len(self.keys)} API keys failed. Attempted keys ending in: {attempted_keys}")
        raise HTTPException(
            status_code=503,
            detail=f"All API keys are currently overloaded or have reached quota limits. Please try again later. (Tried {len(attempted_keys)} keys)"
        )

# Initialize the key manager
api_key_manager = APIKeyManager(GOOGLE_API_KEYS)

# Create images directory
IMAGES_DIR = ROOT_DIR / 'static' / 'images'
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")

# Create API router
api_router = APIRouter(prefix="/api")

# Models
class SocialContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    hashtags: Optional[str] = None

class ImageMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str
    alt_text: str
    filename: str

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source_url: Optional[str] = None
    original_content: str
    translated_content: Optional[str] = None
    social_content: Optional[SocialContent] = None
    images: List[str] = Field(default_factory=list)  # Keep for backward compatibility
    image_metadata: List[ImageMetadata] = Field(default_factory=list)  # New field for image details
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    source_url: Optional[str] = None
    raw_text: Optional[str] = None

class ProjectUpdate(BaseModel):
    translated_content: str

class TranslateRequest(BaseModel):
    content: str
    custom_preset: str = ""

class SocialGenerateRequest(BaseModel):
    content: str
    custom_preset: str = ""

class KOLPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    information_source: str  # Can be text or URL
    insight_required: str
    generated_content: Optional[str] = None
    source_type: str = "text"  # "text" or "url"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KOLPostCreate(BaseModel):
    information_source: str
    insight_required: str
    source_type: str = "text"

class KOLPostGenerate(BaseModel):
    information_source: str
    insight_required: str
    source_type: str = "text"

class NewsArticle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_content: str  # English content - text or URL
    opinion: Optional[str] = None  # Optional user opinion/comment
    style_choice: str = "auto"  # "auto", "style1", "style2"
    generated_content: Optional[str] = None
    source_type: str = "text"  # "text" or "url"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NewsArticleGenerate(BaseModel):
    source_content: str
    opinion: Optional[str] = None
    style_choice: str = "auto"
    source_type: str = "text"

class NewsArticleUpdate(BaseModel):
    generated_content: str

class SocialPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    website_link: Optional[str] = None  # URL to GFI Research article (optional now)
    website_content: Optional[str] = None  # Text content (optional)
    source_type: str = "url"  # "url" or "text"
    title: Optional[str] = None  # Optional - AI will generate if empty
    introduction: Optional[str] = None  # Optional - AI will generate if empty
    highlight: Optional[str] = None  # Optional - AI will generate if empty
    generated_content: Optional[str] = None  # Final generated social post
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SocialPostGenerate(BaseModel):
    website_link: Optional[str] = None
    website_content: Optional[str] = None
    source_type: str = "url"
    title: Optional[str] = None
    introduction: Optional[str] = None
    highlight: Optional[str] = None

class SocialPostUpdate(BaseModel):
    generated_content: str

# Helper functions
async def download_image(image_url: str, project_id: str) -> Optional[str]:
    """Download image and return local path"""
    try:
        response = requests.get(image_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Create project directory
        project_dir = IMAGES_DIR / project_id
        project_dir.mkdir(exist_ok=True)
        
        # Generate filename
        parsed_url = urlparse(image_url)
        filename = Path(parsed_url.path).name or f"image_{uuid.uuid4().hex[:8]}.jpg"
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            filename += '.jpg'
        
        filepath = project_dir / filename
        
        # Save image
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(response.content)
        
        # Return relative path for URL
        return f"/static/images/{project_id}/{filename}"
    except Exception as e:
        logging.error(f"Error downloading image {image_url}: {e}")
        return None

def remove_vietnamese_accents(text: str) -> str:
    """Remove Vietnamese accents from text"""
    # Normalize unicode characters
    text = unicodedata.normalize('NFD', text)
    # Remove combining characters (accents)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text

async def batch_translate_to_vietnamese_slugs(texts: List[str]) -> List[str]:
    """Batch translate multiple English texts to Vietnamese slug format in one API call"""
    if not texts:
        return []
    
    # Define the translation function that will be tried with multiple keys
    async def _translate_with_key(api_key: str):
        llm = LlmChat(
            api_key=api_key,
            session_id=f"batch_translate_{uuid.uuid4().hex[:8]}",
            system_message="You are a translator. Translate English to simple, natural Vietnamese."
        ).with_model("gemini", "gemini-2.0-flash-exp")
        
        # Create numbered list for batch translation
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        prompt = f"""Translate these {len(texts)} English texts to Vietnamese (simple, natural translation).
Return ONLY the Vietnamese translations, one per line, numbered 1-{len(texts)}.
Do NOT add explanations or extra text.

{numbered_texts}"""
        
        user_message = UserMessage(text=prompt)
        response_obj = await llm.send_message(user_message)
        return response_obj.strip()
    
    try:
        # Try with all available API keys
        response_text = await api_key_manager.try_with_all_keys(_translate_with_key)
        
        # Parse response - extract translations
        translations = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove numbering (e.g., "1. ", "2. ", etc.)
            translation = re.sub(r'^\d+\.\s*', '', line)
            if translation:
                translations.append(translation)
        
        # If we didn't get enough translations, pad with originals
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])
        
        # Convert each translation to slug
        slugs = []
        for vietnamese_text in translations[:len(texts)]:
            # Remove accents
            no_accent = remove_vietnamese_accents(vietnamese_text)
            
            # Convert to lowercase
            no_accent = no_accent.lower()
            
            # Replace spaces and special characters with hyphens
            slug = re.sub(r'[^a-z0-9]+', '-', no_accent)
            
            # Remove leading/trailing hyphens
            slug = slug.strip('-')
            
            # Remove consecutive hyphens
            slug = re.sub(r'-+', '-', slug)
            
            slugs.append(slug)
        
        return slugs
    except Exception as e:
        logging.error(f"Error batch translating texts: {e}")
        # Fallback: convert English to slugs
        slugs = []
        for text in texts:
            no_accent = text.lower()
            slug = re.sub(r'[^a-z0-9]+', '-', no_accent)
            slug = slug.strip('-')
            slug = re.sub(r'-+', '-', slug)
            slugs.append(slug)
        return slugs

async def scrape_content(url: str, project_id: str) -> Dict:
    """Scrape content from URL and download images"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Untitled"
        
        # FIRST: Extract images BEFORE removing elements
        image_data_list = []  # Store temp image data
        images_downloaded = []
        
        # Find all images in the page
        all_imgs = soup.find_all('img')
        
        for idx, img in enumerate(all_imgs):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            # Filter out unwanted images by checking parent containers and classes
            skip = False
            
            # Skip if in navigation, menu, footer, sidebar
            for parent in img.parents:
                parent_class = ' '.join(parent.get('class', [])).lower() if parent.get('class') else ''
                parent_tag = parent.name if parent.name else ''
                parent_id = (parent.get('id') or '').lower()
                
                # Skip these containers
                if any(term in parent_class for term in ['navigation', 'menu', 'footer', 'sidebar', 'widget', 'related']):
                    skip = True
                    break
                if any(term in parent_id for term in ['nav', 'menu', 'footer', 'sidebar', 'widget']):
                    skip = True
                    break
                if parent_tag == 'footer':
                    skip = True
                    break
                # Keep header images if they're featured/article images
                if parent_tag in ['nav']:
                    skip = True
                    break
            
            # Skip author/profile/avatar images (usually small)
            img_class = ' '.join(img.get('class', [])).lower() if img.get('class') else ''
            if any(term in img_class for term in ['avatar', 'profile', 'author-image', 'author-profile']):
                skip = True
            
            # Skip logo images
            alt_text_check = (img.get('alt') or '').lower()
            if 'logo' in alt_text_check and len(alt_text_check) < 20:  # Short alt text with "logo" is usually a logo
                skip = True
            
            if skip:
                continue
                
            # Make absolute URL
            absolute_url = urljoin(url, src)
            
            # Get alt text
            alt_text = img.get('alt', '').strip()
            if not alt_text:
                alt_text = img.get('title', '').strip()
            if not alt_text:
                alt_text = f"image-{len(image_data_list)+1}"
            
            # Store temp data
            image_data_list.append({
                'url': absolute_url,
                'alt_text': alt_text
            })
        
        # BATCH TRANSLATE all alt texts at once (much faster!)
        alt_texts = [img['alt_text'] for img in image_data_list]
        vietnamese_slugs = await batch_translate_to_vietnamese_slugs(alt_texts)
        
        # Now create final metadata with translated filenames
        image_metadata = []
        for i, img_data in enumerate(image_data_list):
            vietnamese_slug = vietnamese_slugs[i] if i < len(vietnamese_slugs) else img_data['alt_text'].lower()
            filename = f"{vietnamese_slug}.jpg"
            
            image_metadata.append({
                'url': img_data['url'],
                'alt_text': img_data['alt_text'],
                'filename': filename
            })
            
            # Download image for preview
            local_path = await download_image(img_data['url'], project_id)
            if local_path:
                images_downloaded.append(local_path)
        
        # NOW: Remove script and style elements from soup copy for content extraction
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        for script in soup_copy(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Find main content (try common content containers)
        content = None
        for selector in ['article', 'main', '.content', '#content', '.post-content', '.entry-content']:
            content = soup_copy.select_one(selector)
            if content:
                break
        
        if not content:
            content = soup_copy.find('body')
        
        # Get HTML content
        html_content = str(content) if content else ""
        
        return {
            'title': title_text,
            'content': html_content,
            'images': images_downloaded,
            'image_metadata': image_metadata
        }
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Partner Content Hub API"}

@api_router.post("/projects", response_model=Project)
async def create_project(input: ProjectCreate):
    """Create a new project from URL or raw text"""
    project_id = str(uuid.uuid4())
    
    if input.source_url:
        # Scrape content from URL
        scraped_data = await scrape_content(input.source_url, project_id)
        project_data = {
            'id': project_id,
            'title': scraped_data['title'],
            'source_url': input.source_url,
            'original_content': scraped_data['content'],
            'images': scraped_data['images'],
            'image_metadata': scraped_data.get('image_metadata', []),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    elif input.raw_text:
        # Use raw text
        project_data = {
            'id': project_id,
            'title': 'Untitled Project',
            'original_content': input.raw_text,
            'images': [],
            'image_metadata': [],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    else:
        raise HTTPException(status_code=400, detail="Either source_url or raw_text must be provided")
    
    # Save to database
    doc = project_data.copy()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.projects.insert_one(doc)
    
    return Project(**project_data)

@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    """Get all projects"""
    projects = await db.projects.find({}, {"_id": 0}).sort('created_at', -1).to_list(1000)
    
    # Convert ISO strings to datetime
    for project in projects:
        if isinstance(project.get('created_at'), str):
            project['created_at'] = datetime.fromisoformat(project['created_at'])
        if isinstance(project.get('updated_at'), str):
            project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert ISO strings to datetime
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return Project(**project)

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update: ProjectUpdate):
    """Update project's translated content"""
    result = await db.projects.update_one(
        {"id": project_id},
        {
            "$set": {
                "translated_content": update.translated_content,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return await get_project(project_id)

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully", "id": project_id}

@api_router.get("/download-image")
async def download_image_proxy(url: str, filename: str):
    """Proxy endpoint to download images from external URLs with custom filename"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('content-type', 'image/jpeg')
        
        # Return streaming response with custom filename
        from fastapi.responses import StreamingResponse
        
        def iterfile():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logging.error(f"Error downloading image from {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")


@api_router.post("/projects/{project_id}/translate")
async def translate_content(project_id: str, request: TranslateRequest):
    """Translate and restructure content using Gemini with user's preset prompt"""
    
    # Define the translation function that will be tried with multiple keys
    async def _translate_with_key(api_key: str):
        chat = LlmChat(
            api_key=api_key,
            session_id=f"translate_{project_id}",
            system_message="Bạn là một chuyên gia viết báo về crypto."
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Build custom preset addition if provided
        custom_instructions = ""
        if request.custom_preset:
            custom_instructions = f"\n\nYÊU CẦU BỔ SUNG TỪ NGƯỜI DÙNG:\n{request.custom_preset}\n"
        
        # Use exact user preset prompt with HTML format requirement
        prompt = f"""Tôi yêu cầu bạn, nhiệm vụ chính là: 
-Với mỗi nội dung tôi gửi bạn, đó là bài article, bạn hãy dịch sang tiếng việt và đổi phong cách viết thành cách viết của các bên báo VN, không quá shill dự án, giữ các thuật ngữ crypto nhé, và vẫn giữ format heading.
- Các heading và title chỉ viết hoa chữ cái đầu tiên trong câu hoặc từ khoá quan trọng.
- Để thêm các bản dịch tiếng Việt trong dấu ngoặc đơn cho tất cả các thuật ngữ crypto khó hiểu nhé
- Các heading, đổi cách viết cho chuyên nghiệp, đỡ cringe hơn
- Đoạn đầu tiên luôn là "Giới thiệu" đoạn cuối cùng luôn là đoạn có heading là "Kết luận"
- Thay "công ty" thành "dự án" (nếu có)
- Thay "chúng tôi" hoặc các ngôi thứ nhất thành "dự án"/"đội ngũ"
- Đừng thêm từ "các bạn", hãy dùng "người dùng",...
- Trừ các từ ngữ tiếng anh này thì giữ nguyên từ gốc, còn lại dịch sang tiếng việt cho người dùng crypto hiểu, nhấn mạnh là người dùng crypto (nghĩa là họ đủ hiểu cơ bản về crypto, đừng dịch quá trừu tượng): Blockchain
Private Key / Public Key
Seed Phrase
Staking
Yield Farming
Token vs Coin
Stablecoin
Market Cap
Gas Fee
Smart Contract
NFT (Non-Fungible Token)
DAO (Decentralized Autonomous Organization)
Airdrop
IDO / ICO / IEO
DeFi (Decentralized Finance)
CeFi (Centralized Finance)
TVL (Total Value Locked)
DEX Aggregator
Slippage
Arbitrage
Bridge
Layer 1 / Layer 2
Cross-chain
Validator / Node
Consensus (PoW, PoS, Delegated PoS, …)
Halving
Liquidity Mining
Impermanent Loss
Rug Pull
Whitelist
Mainnet / Testnet
Protocol
Governance Token
- Bạn bây giờ là một chuyên gia viết báo, toàn quyền quyết định lượt bỏ những đoạn promotion không cần thiết khi viết báo về một dự án
{custom_instructions}
QUAN TRỌNG - FORMAT OUTPUT:
- Trả về HTML format với cấu trúc CHỈ 3 PHẦN:

1. TITLE (Tiêu đề bài viết):
<h1>Tiêu đề bài viết tiếng Việt</h1>

2. META DESCRIPTION (Tối đa 2-3 lần độ dài của title):
<div class="meta-description">
<p>Meta description ngắn gọn, chỉ 2-3 câu, tối đa 2-3 lần độ dài của tiêu đề</p>
</div>

3. MAIN CONTENT (Bao gồm Sapo và toàn bộ nội dung còn lại):
<div class="main-content">
<p><strong>Sapo:</strong> Đoạn sapo khoảng 100 từ</p>
<h2>Giới thiệu</h2>
<p>Nội dung giới thiệu...</p>
... (các section khác)
<h2>Kết luận</h2>
<p>Nội dung kết luận...</p>
</div>

- Heading cao nhất trong main content là <h2> (KHÔNG dùng h1, đã dùng cho title)
- Sub-heading dùng <h3>
- Đoạn văn dùng <p>
- Không thêm lời giải thích như "Chắc chắn rồi..." - chỉ trả về HTML thuần túy
- Meta description phải NGẮN GỌN, chỉ 2-3 lần độ dài của title

Nội dung:
{request.content}"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Clean up markdown code blocks if present
        cleaned_response = response.strip()
        if cleaned_response.startswith('```html'):
            cleaned_response = cleaned_response[7:]  # Remove ```html
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]  # Remove ```
        
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # Remove trailing ```
        
        return cleaned_response.strip()
    
    try:
        # Try with all available API keys
        cleaned_response = await api_key_manager.try_with_all_keys(_translate_with_key)
        
        # Update database
        await db.projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "translated_content": cleaned_response,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {"translated_content": cleaned_response}
    
    except Exception as e:
        logging.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@api_router.post("/projects/{project_id}/social")
async def generate_social_content(project_id: str, request: SocialGenerateRequest):
    """Generate social media content using Gemini with user's preset prompt"""
    
    # Define the generation function that will be tried with multiple keys
    async def _generate_with_key(api_key: str):
        chat = LlmChat(
            api_key=api_key,
            session_id=f"social_{project_id}",
            system_message="Bạn là một người quản lý cộng đồng (Community Manager) cho một kênh tin tức về crypto."
        ).with_model("gemini", "gemini-2.0-flash-exp")
        
        # Build custom preset addition if provided
        custom_instructions = ""
        if request.custom_preset:
            custom_instructions = f"\n\nYÊU CẦU BỔ SUNG TỪ NGƯỜI DÙNG:\n{request.custom_preset}\n"
        
        # Combined preset with examples from Partner (mới).pdf
        prompt = f"""ok giờ đọc bài đó và hãy viết bài post telegram ngắn cho tôi nhé, khoảng 100 từ thôi, theo outline sau: title dẫn dắt các vấn đề hiện tại của thị trường sau đó giới thiệu 1 phần nội dung có insight (ngắn, sao cho đừng quá shill dự án) kết luận và CTA về bài GFI Research gốc
{custom_instructions}
YÊU CẦU FORMAT OUTPUT:
- Viết thành 1 bài post liền mạch, KHÔNG CÓ labels như "Tiêu đề:", "Nội dung:", "CTA:"
- Dòng đầu tiên: Tiêu đề của bài (không cần label) - SỬ DỤNG EMOJI 🔥 hoặc 🤔 ở đầu tiêu đề
- Sau đó xuống dòng và viết nội dung chính
- Nội dung chính chia thành 2 đoạn văn (mỗi đoạn cân đối độ dài), ngăn cách bởi 1 dòng trống
- Sử dụng emojis phù hợp trong nội dung: 🙂 ➡️ 🎯 🤔 (2-3 emojis trong bài)
- Đoạn cuối: CTA về GFI Research với emoji ➡️ và link đầy đủ
- Tổng cộng: Tiêu đề + 2 đoạn nội dung + 1 đoạn CTA

OUTLINE CỦA BÀI POST:
- Tiêu đề (dòng đầu) - có emoji 🔥 hoặc 🤔
- Nội dung chính đoạn 1 (context và vấn đề)
- Nội dung chính đoạn 2 (insight và detail kỹ thuật) - có emoji như 🙂 ➡️ 🎯
- CTA về bài viết gốc GFI Research - có emoji ➡️ và link

Lưu ý: 
- Viết với góc nhìn thứ ba, không shill dự án
- Sử dụng emojis tự nhiên, không lạm dụng (2-3 emojis tổng cộng)
- Luôn có link đầy đủ trong CTA

VÍ DỤ THAM KHẢO (3 examples với format mới):

Example 1 - Bài về SP1 Hypercube (format đúng với emojis):
🔥 Tạo bằng chứng khối Ethereum chỉ trong 12 giây: Bài toán tốc độ cho ZK rollups

Một trong những rào cản lớn cho ZK rollups trên Ethereum là thời gian tạo bằng chứng. Mục tiêu là proving dưới 12 giây, thời gian slot của Ethereum, để đạt được finality thực sự thời gian thực.

🙂 SP1 Hypercube đang thử nghiệm cách tiếp cận mới với đa thức đa tuyến thay vì đa thức đơn biến truyền thống. AE nghĩ đây có phải là đột phá thực sự cho ZK Ethereum, hay vẫn còn xa mới đến sự công nhận rộng rãi do yêu cầu phần cứng?

Cùng GFI khám phá chi tiết tại ➡️ SP1 Hypercube: zkVM cho phép tạo bằng chứng Ethereum trong thời gian thực (https://gfiresearch.net/sp1-hypercube-zkvm-cho-phep-tao-bang-chung-ethereum-trong-thoi-gian-thuc)

Example 2 - Bài về Succinct (format đúng với emojis):
🤔 Bài toán về chi phí và khả năng tiếp cận của ZK Proof

Việc tạo Zero-Knowledge Proof hiện vẫn đòi hỏi cơ sở hạ tầng phức tạp và chi phí cao, hạn chế khả năng áp dụng rộng rãi. Các dự án thường phải tự vận hành prover hoặc phụ thuộc vào nhà cung cấp tập trung.

➡️ Vì vậy, Succinct đang thử nghiệm mô hình marketplace hai chiều, kết nối người cần ZK proof với prover thông qua đấu giá. Điểm đáng chú ý là kiến trúc tách biệt: auctioneer off-chain cho tốc độ cao, settlement on-chain Ethereum cho bảo mật. Token $PROVE vừa là phương tiện thanh toán, vừa làm cơ chế staking để ràng buộc trách nhiệm prover.

🤔 Liệu mô hình marketplace này có tạo ra thị trường ZK proof hiệu quả hơn, hay vẫn chỉ phù hợp cho một số use case nhất định?

Đọc phân tích chi tiết về kiến trúc của Succinct tại ➡️ Kiến trúc Mạng lưới Succinct và token $PROVE (https://gfiresearch.net/kien-truc-mang-luoi-succinct-va-token-prove)

Example 3 - Bài về BitVM (format đúng với emojis):
🔥 Bitcoin Script và bài toán ứng dụng phức tạp: Liệu ZK Proof có là lời giải?

Bitcoin Script (Ngôn ngữ lập trình của Bitcoin) được thiết kế không hoàn chỉnh về tính toán để tối ưu bảo mật, nhưng điều này cũng hạn chế khả năng xây dựng các ứng dụng phức tạp như rollup hay bridge phi tín nhiệm trên Bitcoin.

🎯 BitVM đang thử nghiệm cách tiếp cận mới bằng việc xác minh tính toán thay vì thực thi trực tiếp. Điểm kỹ thuật đáng chú ý là BLAKE3 chỉ cần 7 vòng nén so với 64 vòng của SHA256, giúp giảm đáng kể chi phí xác minh ZK Proof trên Bitcoin Script. Một số dự án như Alpen Labs (ZK rollup), Babylon (bridge phi tín nhiệm) đang thử nghiệm mô hình này. Tuy nhiên, liệu cách tiếp cận này có đủ hiệu quả và bảo mật cho ứng dụng thực tế?

Cùng GFI tìm hiểu chi tiết về hướng tiếp cận kĩ thuật của Succinct tại ➡️ Succinct mở ra khả năng xác minh ZK Proof trên Bitcoin thông qua BitVM (https://gfiresearch.net/succinct-mo-ra-kha-nang-xac-minh-zk-proof-tren-bitcoin-thong-qua-bitvm)

---

BÀI VIẾT CẦN TẠO SOCIAL POST:
{request.content}"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Store the Vietnamese social post as a single content piece
        # The response is a ~100 word social media post following the structure:
        # Title → Problem/Context → Insight → CTA
        social_content = {
            'facebook': response.strip(),
            'twitter': '',  # Not used in Vietnamese format
            'hashtags': ''  # Not used in Vietnamese format
        }
        
        # Update database
        await db.projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "social_content": social_content,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return social_content
    
    except Exception as e:
        logging.error(f"Social content generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Social content generation failed: {str(e)}")

# KOL Post endpoints
@api_router.post("/kol-posts", response_model=KOLPost)
async def create_kol_post(post_data: KOLPostCreate):
    """Create a new KOL post without generating content"""
    post = KOLPost(**post_data.dict())
    await db.kol_posts.insert_one(post.dict())
    return post

@api_router.get("/kol-posts", response_model=List[KOLPost])
async def get_kol_posts():
    """Get all KOL posts"""
    posts = await db.kol_posts.find().sort("created_at", -1).to_list(100)
    return posts

@api_router.get("/kol-posts/{post_id}", response_model=KOLPost)
async def get_kol_post(post_id: str):
    """Get a specific KOL post"""
    post = await db.kol_posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="KOL post not found")
    return post

@api_router.delete("/kol-posts/{post_id}")
async def delete_kol_post(post_id: str):
    """Delete a KOL post"""
    result = await db.kol_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="KOL post not found")
    return {"message": "KOL post deleted successfully"}

@api_router.post("/kol-posts/generate")
async def generate_kol_post(request: KOLPostGenerate):
    """Generate KOL post content using AI"""
    try:
        # Get information content
        information_content = request.information_source
        
        # If source is URL, scrape the content
        if request.source_type == "url":
            try:
                response = requests.get(request.information_source, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                # Get title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                # Get main content
                main_content = ""
                # Try to find main content areas
                content_areas = soup.find_all(['article', 'main', 'div'], class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'article', 'post', 'entry']))
                if content_areas:
                    main_content = ' '.join([area.get_text(separator=' ', strip=True) for area in content_areas])
                else:
                    # Fallback to all paragraph text
                    paragraphs = soup.find_all('p')
                    main_content = ' '.join([p.get_text(separator=' ', strip=True) for p in paragraphs])
                
                information_content = f"Tiêu đề: {title_text}\n\nNội dung:\n{main_content}"
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Không thể cào nội dung từ URL: {str(e)}")
        
        # DQ Writing Style from PDF - Complete examples
        writing_style_examples = """
Bài 1:
Upbit trước delist hết mấy coin privacy như $XMR, $ZEC vì lý do tuân thủ.
Nhưng giờ lại list $PROVE, cũng là token liên quan đến privacy, nhưng không bị xem là dạng private currency
Có thể do nó thuộc dạng hạ tầng ZK, dùng cho xác minh và mở rộng mạng lưới chứ không phục vụ ẩn danh giao dịch.
Không biết trong tương lai có open ra để list lại mấy thằng privacy không, vì lquan đến rửa tiền thì cũng căng.
Không ai muốn liên đới cả

Bài 2:
Đệt trước có tia được em này mà chờ lâu nóng đít nên thu hồi về dca coin top
Nào ngờ nó chờ mình bán xong là nó x8
Cay dé vậy ta kkk $ZKWASM
Thôi tìm gem khác vậy, alpha tụi nó hay đẩy láo lắm ae

Bài 3:
Bài viết này dành cho ae hay sợ ma voi quỷ mập trên Hyperliquid
Dạo này thấy các bác follow ví "insider nhà Trump" nhiều và hễ cứ thấy nó sọc $BTC thì sợ toán loạn lên, vì đa phần ae hold hàng nhưng toàn mang tâm lí trade, âm 5 - 10% là đã thấy chột dạ.
Thằng này nó short $BTC volume lớn, lại còn lù lù trên Hyper, ae track ra được nó, đăng social tùm lum cả trong và ngoài nước, không lẽ nó không biết
Yên vị giùm t cái, cuối mùa rồi đừng có tối ưu nữa, cú sập này kill hết bẩy rồi, mục đích là để ae rén tay không dám bẩy nữa, từ đó đẩy là chốt lời quy mô lớn hơn vì thanh khoản đó từ ae mới là thanh khoản thật.
That's it, $ETH szn incoming

Bài 5:
Quả $SNX x2 sau 2 tuần, x4 từ đáy. Múc theo Dương Quá thì Quá gì ạ, Quá đã
GM đầu tuần cả nhà, đúng plan thì mình làm thôi, kệ mẹ cú sập luôn
Sau đợt liquidate full market thì $SNX vẫn là 1 trong những còn hàng chịu ảnh hưởng ít nhất, sập xong thực tế chỉ lõm 10% so với entry của Dương.
Và cũng may mắn nhờ cú sập nên kịp thó 1 lệnh DCA vào, đúng vùng 0.9 luôn vì 4h sáng hôm đó thì Dương chưa dậy =))
Thành quả cho những chuỗi ngày sideway, x2 chốt gốc là đẹp. AE vào con hàng này cùng Dương thì có thể chốt gốc nhé, còn lại để market tự xử lí, #Ethereum Eco bắt đầu chạy, uptrend tới rồi ae ơi

Bài 7:
KINH KHỦNG: Sống đủ lâu để thấy con số 20 tỷ dô bị thanh lý
Trừ $BTC, $ETH còn đỡ tí, tất cả altcoin nát gáo, chia buồn với ae long đòn bẩy, chỉ cần 2x là cháy hết, không còn giọt máu nào luôn.
Điều cần làm hiện tại là bình tĩnh, chờ tạo đáy đã, Trung Quốc chưa đáp trả, còn hành tiếp đó ae ạ

Bài 9:
GM AE, con hàng $SNX vẫn cứng phết
Chart vẫn còn sideway và vẫn không lủng được entry của Dương, nay được mùa coin cũ nó đẩy lên +20% ngon lành luôn ae ạ
Ae nào trade lướt thì chốt vừa mồm đợi entry mới cũng được vì $BTC đang khá dập dìu.
Còn Dương thì hold chặt, sẽ vào thêm và target cao hơn, vẫn bet vào perp dex hệ Ethereum này

Bài 11:
Thấy chưa ae, nổ súng rồi đó. Giá này còn rẻ chán
Cứ chill chill ôm mấy em chất lượng thôi không cần làm gì nhiều ae ạ
$PLUME on the top, up only (ko đùa)
P/s: Sẽ nói rõ về tin này sau, nhưng bùng lổ vl đó ae

Bài 14:
Uptrend tới, các dự án bắt đầu ngáo giá
Anh em cẩn thận, mới hôm qua có $FF làm mẫu rồi đó, chia gần 10 từ đỉnh dù mới TGE...1 ngày.
Đánh giá kỹ dự án, đừng để bị slow rug như năm ngoái nha ae
Nói chung tốt nhất mới list thì đừng đụng tay vào

Bài 16:
Nếu ae miss cả $ASTER, $AVNT, $APEX thì có thể múc $SNX, entry now. Lý do:
@synthetix_io là dự án mùa cũ, mùa này sẽ có động lực đẩy để chốt sổ, còn làm dự án khác mùa sau
Chuyển sang bú Ethereum theo trend perp dex, với trading prize pool $1M
Chart đã confirm breakout với volume mạnh + vượt đỉnh, mốc cản gần nhất thì chỉ là trendline giảm quanh 1.8, nhưng các đỉnh trước đó là mấy năm về trước rồi.
Kỳ vọng $ETH pump mạnh vào Q4 năm nay
Một trong những cái thiếu là một người dẫn sóng, tuy nhiên nếu rõ ràng rồi thì không còn entry đẹp nữa.
Target gần nhất 1.8, về tầm 0.9 dca thêm đoạn nữa, stop loss là khi $ETH bắt đầu có dấu hiệu rụng trong Q4 này.

Bài 17:
Volume thanh lý $ETH những tháng qua bao giờ cũng cao nhất thị trường.
MM hay thật, nào ra phố wall, nào lên ETF gom, dụ cho bullish, max long, xong quét là ấm cả làng
Nói vậy thôi chứ quét xong xuôi -> chuẩn bị đà tăng mới
Hold spot vẫn tín nha các bác, dưới 4k, tầm 3k6 -> 3k8 là vùng giá đẹp để quăng thêm 1 2 chiếc dép lên thuyền chờ Up to bờ đến.
"""
        
        # System message for KOL writing style
        system_message = f"""Bạn là một KOL crypto có phong cách viết đặc trưng. Học phong cách viết này:

{writing_style_examples}

PHONG CÁCH VIẾT CỦA BẠN:
- Tone casual, thân mật với độc giả (dùng "ae", "mình", "t", "m")
- Nhận xét ngắn gọn, không giải thích dài dòng
- Dùng tiếng lóng crypto và tiếng Việt tự nhiên
- Đi thẳng vào vấn đề, không lan man
- Dùng cảm thán vừa phải, không lạm dụng
- Giữ ticker crypto với $ (ví dụ: $BTC, $ETH)
- Có thể dùng emoji nhẹ nhàng
- Viết theo kiểu tâm sự, chia sẻ quan điểm cá nhân

QUAN TRỌNG:
- Nhận định phải NGẮN GỌN, đúng trọng tâm
- KHÔNG giải thích tá lả
- KHÔNG lạm dụng cảm thán
- Giữ phong cách tự nhiên như đang chat với bạn bè"""

        # Initialize Gemini chat
        chat = LlmChat(
            api_key=GOOGLE_API_KEY,
            session_id=f"kol_post_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Create user message
        user_message = UserMessage(f"""Đây là thông tin cần học:

{information_content}

Đây là nhận định cần có (viết ngắn gọn theo nhận định này):
{request.insight_required}

Hãy viết 1 bài post theo phong cách của bạn, kết hợp thông tin trên và nhận định đã cho. Nhớ: nhận định ngắn gọn, không giải thích dài dòng.""")
        
        # Generate content
        response = await chat.send_message(user_message)
        
        # Create and save KOL post
        kol_post = KOLPost(
            information_source=request.information_source,
            insight_required=request.insight_required,
            generated_content=response.strip(),
            source_type=request.source_type
        )
        
        await db.kol_posts.insert_one(kol_post.dict())
        
        return kol_post
    
    except Exception as e:
        logging.error(f"KOL post generation error: {e}")
        raise HTTPException(status_code=500, detail=f"KOL post generation failed: {str(e)}")

# News Generator endpoints
@api_router.post("/news", response_model=NewsArticle)
async def create_news_article(news_data: NewsArticleGenerate):
    """Create a new news article without generating content"""
    news = NewsArticle(**news_data.dict())
    await db.news_articles.insert_one(news.dict())
    return news

@api_router.get("/news", response_model=List[NewsArticle])
async def get_news_articles():
    """Get all news articles"""
    articles = await db.news_articles.find().sort("created_at", -1).to_list(100)
    return articles

@api_router.get("/news/{news_id}", response_model=NewsArticle)
async def get_news_article(news_id: str):
    """Get a specific news article"""
    article = await db.news_articles.find_one({"id": news_id})
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    return article

@api_router.put("/news/{news_id}", response_model=NewsArticle)
async def update_news_article(news_id: str, update: NewsArticleUpdate):
    """Update news article content"""
    result = await db.news_articles.update_one(
        {"id": news_id},
        {
            "$set": {
                "generated_content": update.generated_content,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="News article not found")
    
    article = await db.news_articles.find_one({"id": news_id})
    return article

@api_router.delete("/news/{news_id}")
async def delete_news_article(news_id: str):
    """Delete a news article"""
    result = await db.news_articles.delete_one({"id": news_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News article not found")
    return {"message": "News article deleted successfully"}

@api_router.post("/news/generate")
async def generate_news_article(request: NewsArticleGenerate):
    """Generate crypto news summary using AI"""
    try:
        # Get source content
        source_content = request.source_content
        
        # If source is URL, scrape the content
        if request.source_type == "url":
            try:
                response = requests.get(request.source_content, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                # Get title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                # Get main content
                main_content = ""
                content_areas = soup.find_all(['article', 'main', 'div'], class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'article', 'post', 'entry']))
                if content_areas:
                    main_content = ' '.join([area.get_text(separator=' ', strip=True) for area in content_areas])
                else:
                    paragraphs = soup.find_all('p')
                    main_content = ' '.join([p.get_text(separator=' ', strip=True) for p in paragraphs])
                
                source_content = f"Title: {title_text}\n\nContent:\n{main_content}"
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Không thể cào nội dung từ URL: {str(e)}")
        
        # Determine style based on choice
        style_instruction = ""
        if request.style_choice == "style1":
            style_instruction = """
🔹 PHONG CÁCH 1: Văn xuôi + có liệt kê
> Dành cho tin có số liệu, dữ kiện, cập nhật thị trường.

**CẤU TRÚC CHI TIẾT:**
1. **Mở đầu:** 🔥 Tiêu đề giật tít, nhấn mạnh con số hoặc sự kiện chính
2. **Tóm tắt:** Một đoạn ngắn tóm bối cảnh hoặc nguồn tin  
3. **Trọng tâm:** 2–3 dòng liệt kê, dùng icon 👉
4. **Phân tích:** Giải thích ý nghĩa, xu hướng hoặc tác động
5. **Hàm ý/Dự báo:** ➡️ Nêu hướng đi tiếp theo hoặc khả năng xảy ra
6. **Kết bài:** Câu hỏi mở thân mật, có emoji
   > Ví dụ: "AE nghĩ sao? 😅" hoặc "Liệu đây là tín hiệu gom hàng không AE? 😅"

**TONE:** Nhanh, súc tích, gần gũi, rõ ý.
"""
        elif request.style_choice == "style2":
            style_instruction = """
🔹 PHONG CÁCH 2: Văn xuôi, không liệt kê
> Dành cho tin nhận định, xu hướng, chính sách, phát biểu, hợp tác.

**CẤU TRÚC CHI TIẾT:**
1. **Mở đầu:** 🔥 + tiêu đề định hướng (xu hướng, nhân vật, hành động)
2. **Dẫn dắt:** Giới thiệu nhân vật/chủ thể + hành động cụ thể
3. **Bối cảnh:** 🤔 Giải thích ngắn gọn vì sao đây là sự kiện đáng chú ý
4. **Phát biểu/Củng cố:** Có thể trích dẫn 1 câu nói hoặc quan điểm
5. **Kết bài:** Hai câu cuối tách riêng, cùng nhịp, kích thích tương tác
   > Ví dụ:
   > Cuộc chiến này không chỉ xoay quanh một cá nhân.
   > Liệu Nhà Trắng có đang cố gia tăng ảnh hưởng lên Fed? AE nghĩ sao? 😅

**TONE:** Mạch lạc, tự nhiên, có chất bình luận nhẹ.
"""
        else:  # auto
            style_instruction = """
🔹 TỰ ĐỘNG CHỌN STYLE dựa vào nội dung:
- Nếu tin có nhiều **số liệu/dữ kiện/metrics/cập nhật thị trường** → chọn Phong cách 1 (có liệt kê)
- Nếu tin về **chính sách/xu hướng/nhận định/phát biểu/hợp tác** → chọn Phong cách 2 (không liệt kê)

**PHONG CÁCH 1 (Văn xuôi + liệt kê):**
Cấu trúc: 🔥 Mở đầu → Tóm tắt → 👉 Trọng tâm (list) → Phân tích → ➡️ Hàm ý/Dự báo → Kết bài (? 😅)
Tone: Nhanh, súc tích, gần gũi, rõ ý

**PHONG CÁCH 2 (Văn xuôi, không liệt kê):**  
Cấu trúc: 🔥 Mở đầu + định hướng → Dẫn dắt → 🤔 Bối cảnh → Phát biểu/Củng cố → 2 câu cuối tách riêng (? 😅)
Tone: Mạch lạc, tự nhiên, có chất bình luận nhẹ
"""
        
        # System message for News Generator with enhanced context engineering
        system_message = f"""Bạn là một Crypto News Generator AI chuyên nghiệp, tạo bản tin crypto tự động bằng tiếng Việt.

🎯 MỤC TIÊU:
Tạo bản tin crypto ngắn gọn (~150 từ), đúng tone mạng xã hội (Twitter/Telegram/LinkedIn), dựa trên nội dung gốc tiếng Anh.
Output: Bản tin tiếng Việt súc tích, có cảm xúc, logic, dễ đọc và dễ viral.

🎭 BRAND VOICE:
**Thông minh – Thân thiện – Tự tin – Không dư thừa**
- Bạn là một "chiến hữu" cùng bàn luận tin tức crypto với người đọc
- Giọng văn như một người bạn am hiểu, không học thuật, gần gũi
- Tạo cảm xúc, nhấn mạnh sự kiện chính
- Khuyến khích tương tác qua câu hỏi mở

📰 PHONG CÁCH VIẾT:
{style_instruction}

⚙️ QUY TẮC & CHI TIẾT KỸ THUẬT:
- **Giữ nguyên tên báo:** ví dụ *Financial Times (Anh)*
- **Emoji:** chỉ dùng 2–3 cái chính (🔥 🤔 👉 ➡️ 😅)
- **KHÔNG thêm thông tin ngoài bài gốc** - chỉ tóm tắt và diễn đạt lại
- **KHÔNG dùng meme hoặc emoji lố** - giữ tinh tế
- **Quote:** có thể để nguyên tiếng Anh hoặc dịch tự nhiên
- **Độ dài:** 120–160 từ (chặt chẽ)
- **Kết bài:** Luôn có câu hỏi mở khơi gợi tương tác + emoji 😅

📤 OUTPUT FORMATTING RULES:
- **KHÔNG** bắt đầu bằng: "Chắc chắn rồi", "Dưới đây là", "Tất nhiên rồi", "Sure", "Here's your text"
- Bắt đầu **NGAY LẬP TỨC** với nội dung (tiêu đề hoặc câu mở đầu)
- **KHÔNG** bao gồm bất kỳ bình luận ngoài lề, giải thích, hoặc câu chuyển tiếp
- Output phải trông như được viết trực tiếp để xuất bản, không cần chỉnh sửa

💡 VÍ DỤ MẪU KẾT BÀI:
- "AE nghĩ sao? 😅"
- "Liệu đây là tín hiệu gom hàng không AE? 😅"  
- "Khấn các anh đẩy vội cho AE toai về bờ rồi vỡ sau cũng được 😅"
- "AE nghĩ sao, cú sập này là dấu hiệu cảnh báo kết mùa hay reset game cho nhẹ thuyền nào? 😅"
- "Anh em đang nhắm tới dự án nào bên hệ Base và phân khúc AI đó, share với cộng đồng nào 😅"

Hãy tạo bản tin theo đúng phong cách đã chỉ định, giữ độ dài 120-160 từ, và đảm bảo tone thân thiện như đang trò chuyện với chiến hữu."""

        # Build user message
        user_message_text = f"""Nội dung nguồn (tiếng Anh):

{source_content}"""
        
        if request.opinion:
            user_message_text += f"""

Nhận xét/Opinion từ người dùng:
{request.opinion}"""
        
        user_message_text += "\n\nHãy tạo bản tin crypto summary theo style đã chỉ định. Nhớ: BẮT ĐẦU NGAY với nội dung bản tin, KHÔNG thêm lời mở đầu hay giải thích."
        
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=GOOGLE_API_KEY,
            session_id=f"news_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Generate content
        user_message = UserMessage(user_message_text)
        response = await chat.send_message(user_message)
        
        # Create and save news article
        news_article = NewsArticle(
            source_content=request.source_content,
            opinion=request.opinion,
            style_choice=request.style_choice,
            generated_content=response.strip(),
            source_type=request.source_type
        )
        
        await db.news_articles.insert_one(news_article.dict())
        
        return news_article
    
    except Exception as e:
        logging.error(f"News generation error: {e}")
        raise HTTPException(status_code=500, detail=f"News generation failed: {str(e)}")

# Social-to-Website Post endpoints
@api_router.post("/social-posts", response_model=SocialPost)
async def create_social_post(post_data: SocialPostGenerate):
    """Create a new social post without generating content"""
    post = SocialPost(**post_data.dict())
    await db.social_posts.insert_one(post.dict())
    return post

@api_router.get("/social-posts", response_model=List[SocialPost])
async def get_social_posts():
    """Get all social posts"""
    posts = await db.social_posts.find().sort("created_at", -1).to_list(length=100)
    return posts

@api_router.get("/social-posts/{post_id}", response_model=SocialPost)
async def get_social_post(post_id: str):
    """Get a specific social post"""
    post = await db.social_posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Social post not found")
    return post

@api_router.put("/social-posts/{post_id}", response_model=SocialPost)
async def update_social_post(post_id: str, update: SocialPostUpdate):
    """Update social post content"""
    result = await db.social_posts.update_one(
        {"id": post_id},
        {
            "$set": {
                "generated_content": update.generated_content,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Social post not found")
    
    post = await db.social_posts.find_one({"id": post_id})
    return post

@api_router.delete("/social-posts/{post_id}")
async def delete_social_post(post_id: str):
    """Delete a social post"""
    result = await db.social_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Social post not found")
    return {"message": "Social post deleted successfully"}

@api_router.post("/social-posts/generate")
async def generate_social_post(request: SocialPostGenerate):
    """Generate social-to-website post using AI"""
    try:
        # Get website content based on source type
        website_content = ""
        
        if request.source_type == "url" and request.website_link:
            # Scrape website content from URL
            try:
                response = requests.get(request.website_link, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                website_content = soup.get_text(separator=' ', strip=True)
                # Limit content length
                website_content = website_content[:5000]
                
            except Exception as e:
                logging.error(f"Error scraping website: {e}")
                raise HTTPException(status_code=400, detail=f"Không thể cào nội dung từ URL: {str(e)}")
        
        elif request.source_type == "text" and request.website_content:
            # Use provided text content
            website_content = request.website_content[:5000]
        
        if not website_content:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp URL hoặc nội dung website")
        
        # Build system message based on context engineering
        system_message = """Bạn là một AI chuyên tạo bài đăng social media để dẫn traffic về website (GFI Research).

🎯 MỤC TIÊU:
Tạo bài viết đăng trên các nền tảng social (X, Facebook, LinkedIn) để dẫn người đọc về website, nơi có bài phân tích chi tiết.
- Độ dài: 150–180 từ
- Cấu trúc: 3–4 đoạn ngắn
- Tone: Chuyên nghiệp – dễ đọc – giàu thông tin (giống KOL crypto)

📝 CẤU TRÚC BÀI VIẾT (4 PHẦN):

1️⃣ **TITLE (Hook nhà đầu tư)**
   - Thu hút đầu tiên, chứa yếu tố "giật nhẹ"
   - Có số liệu hoặc câu hỏi gợi tò mò
   - Có thể dùng chữ in hoa, icon, số liệu lớn
   - Ví dụ: "🔥 Gọi vốn 130 TRIỆU ĐÔ với định giá 1 TỶ ĐÔ – Dự án này có gì mà 'nổ' cả X?"

2️⃣ **GIỚI THIỆU DỰ ÁN**
   - Cung cấp bối cảnh và tóm tắt trong 1–2 câu
   - Trả lời: "Dự án này là gì, giải quyết vấn đề nào, và vì sao được chú ý?"

3️⃣ **ĐIỂM NỔI BẬT/RÒ RỈ**
   - Tiết lộ chi tiết gây tò mò: gọi vốn, tranh luận, công nghệ, nhân vật, insight
   - Dạng câu tự nhiên, có thể dùng icon (⚡, 🤔, 💸...)
   - Ví dụ: "😳 Nhưng nhìn on-chain lại thấy một câu chuyện khác..."

4️⃣ **CTA (Call to Action)**
   - Đưa người đọc về website
   - Kết thúc bằng câu hỏi hoặc gợi mở
   - Ví dụ: "Cùng GFI tìm hiểu tại bài viết này 👇"

🎨 TONE & BRAND VOICE:
- **Phong cách:** Chuyên nghiệp, dễ đọc, giàu thông tin
- **Đối tượng:** Nhà đầu tư, người quan tâm crypto
- **Giống:** Các KOL crypto hàng đầu
- **Độ dài chặt chẽ:** 150–180 từ

⚙️ QUY TẮC KỸ THUẬT:
- Số đoạn: 3–4 đoạn ngắn
- Yếu tố thu hút: Số liệu, câu hỏi, chữ in hoa, icon
- Mục đích: Dẫn traffic về website
- CTA: Luôn có và rõ ràng, kèm link về website

💡 LOGIC FILL SYSTEM:
1. Nếu user điền title → giữ nguyên. Nếu trống → AI sinh hook giật nhẹ với số liệu/câu hỏi
2. Nếu user điền giới thiệu → dùng nguyên văn. Nếu trống → AI tóm tắt từ web content
3. Nếu user điền điểm nổi bật → giữ nguyên. Nếu trống → AI chọn insight hấp dẫn nhất từ bài web
4. Thêm CTA rõ ràng hướng về website, kèm link

📤 OUTPUT FORMATTING RULES:
- **KHÔNG** bắt đầu bằng: "Chắc chắn rồi", "Dưới đây là", "Sure", "Here's your text"
- Bắt đầu **NGAY LẬP TỨC** với nội dung (title/câu mở đầu)
- **KHÔNG** bao gồm bình luận ngoài lề, giải thích
- Output phải sẵn sàng để đăng lên social media ngay

Hãy tạo bài viết social post theo đúng cấu trúc và tone đã chỉ định."""

        # Build user message
        user_message_parts = []
        
        # Add website content
        if website_content:
            user_message_parts.append(f"NỘI DUNG TỪ WEBSITE:\n{website_content[:3000]}")
        
        # Add link if provided
        if request.website_link:
            user_message_parts.append(f"\nLINK WEBSITE: {request.website_link}")
        
        # Add user inputs if provided
        if request.title:
            user_message_parts.append(f"\nTITLE (do user cung cấp):\n{request.title}")
        else:
            user_message_parts.append("\nTITLE: (để trống - AI tự sinh hook giật tít)")
        
        if request.introduction:
            user_message_parts.append(f"\nGIỚI THIỆU (do user cung cấp):\n{request.introduction}")
        else:
            user_message_parts.append("\nGIỚI THIỆU: (để trống - AI tự tóm tắt dự án)")
        
        if request.highlight:
            user_message_parts.append(f"\nĐIỂM NỔI BẬT (do user cung cấp):\n{request.highlight}")
        else:
            user_message_parts.append("\nĐIỂM NỔI BẬT: (để trống - AI tự chọn insight hấp dẫn)")
        
        user_message_parts.append("\n\nHãy tạo bài social post hoàn chỉnh với CTA dẫn về website. Nhớ: BẮT ĐẦU NGAY với nội dung, KHÔNG thêm lời mở đầu.")
        
        user_message_text = "\n".join(user_message_parts)
        
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=GOOGLE_API_KEY,
            session_id=f"social_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Generate content
        user_message = UserMessage(user_message_text)
        response = await chat.send_message(user_message)
        
        # Create and save social post
        social_post = SocialPost(
            website_link=request.website_link,
            website_content=request.website_content,
            source_type=request.source_type,
            title=request.title,
            introduction=request.introduction,
            highlight=request.highlight,
            generated_content=response.strip()
        )
        
        await db.social_posts.insert_one(social_post.dict())
        
        return social_post
    
    except Exception as e:
        logging.error(f"Social post generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Social post generation failed: {str(e)}")

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()