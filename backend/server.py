from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM API Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source_url: Optional[str] = None
    original_content: str
    translated_content: Optional[str] = None
    social_content: Optional[SocialContent] = None
    images: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    source_url: Optional[str] = None
    raw_text: Optional[str] = None

class ProjectUpdate(BaseModel):
    translated_content: str

class TranslateRequest(BaseModel):
    content: str

class SocialGenerateRequest(BaseModel):
    content: str

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
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Find main content (try common content containers)
        content = None
        for selector in ['article', 'main', '.content', '#content', '.post-content', '.entry-content']:
            content = soup.select_one(selector)
            if content:
                break
        
        if not content:
            content = soup.find('body')
        
        # Download images and replace URLs
        images_downloaded = []
        if content:
            img_tags = content.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Make absolute URL
                    absolute_url = urljoin(url, src)
                    # Download image
                    local_path = await download_image(absolute_url, project_id)
                    if local_path:
                        img['src'] = local_path
                        images_downloaded.append(local_path)
        
        # Get HTML content
        html_content = str(content) if content else ""
        
        return {
            'title': title_text,
            'content': html_content,
            'images': images_downloaded
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

@api_router.post("/projects/{project_id}/translate")
async def translate_content(project_id: str, request: TranslateRequest):
    """Translate and restructure content using Gemini with specialized crypto/blockchain prompt"""
    try:
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate_{project_id}",
            system_message="Bạn là một Biên tập viên và Chuyên gia viết báo về lĩnh vực crypto tại Việt Nam. Nhiệm vụ của bạn là biến một bài viết gốc (tiếng Anh) thành một bài báo chuyên nghiệp, chuẩn văn phong Việt Nam và sẵn sàng để đăng tải."
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Create the specialized prompt for crypto content
        prompt = f"""**BỐI CẢNH (CONTEXT):**
Bạn là một Biên tập viên và Chuyên gia viết báo về lĩnh vực crypto tại Việt Nam. Nhiệm vụ của bạn là biến một bài viết gốc (tiếng Anh) thành một bài báo chuyên nghiệp, chuẩn văn phong Việt Nam và sẵn sàng để đăng tải.

**NHIỆM VỤ CHÍNH (MISSION):**
Với nội dung tôi cung cấp, hãy thực hiện một chuỗi các nhiệm vụ sau một cách tuần tự và trả về một KẾT QUẢ DUY NHẤT.

**CÁC QUY TẮC BẮT BUỘC (MANDATORY RULES):**

1.  **DỊCH THUẬT & VĂN PHONG:**
    *   Dịch toàn bộ nội dung sang Tiếng Việt.
    *   Sử dụng văn phong báo chí chuyên nghiệp, khách quan, không quá quảng cáo (shill) cho dự án.
    *   Toàn quyền lược bỏ những đoạn quảng cáo hoặc thông tin không cần thiết.

2.  **ĐỊNH DẠNG & CẤU TRÚC:**
    *   Giữ nguyên cấu trúc các heading (tiêu đề phụ).
    *   Đoạn đầu tiên LUÔN LUÔN có heading là "Giới thiệu".
    *   Đoạn cuối cùng LUÔN LUÔN có heading là "Kết luận".
    *   Tất cả Tiêu đề chính (Title) và tiêu đề phụ (Heading) chỉ được viết hoa chữ cái đầu tiên của câu (hoặc các từ khóa, tên riêng quan trọng). Tinh chỉnh câu chữ của heading cho chuyên nghiệp và tự nhiên hơn.

3.  **QUY TẮC NGÔN TỪ:**
    *   Thay thế "công ty" bằng "dự án".
    *   Thay thế các đại từ nhân xưng ngôi thứ nhất ("chúng tôi", "tôi", "we", "our") thành các danh từ ngôi thứ ba như "dự án", "đội ngũ".
    *   Tránh dùng từ "các bạn", hãy sử dụng các từ thay thế trang trọng hơn như "người dùng", "cộng đồng", "nhà phát triển".

4.  **XỬ LÝ THUẬT NGỮ CRYPTO:**
    *   **Giữ nguyên gốc** các thuật ngữ sau: Blockchain, Private Key, Public Key, Seed Phrase, Staking, Yield Farming, Token, Coin, Stablecoin, Market Cap, Gas Fee, Smart Contract, NFT, DAO, Airdrop, IDO, ICO, IEO, DeFi, CeFi, TVL, DEX Aggregator, Slippage, Arbitrage, Bridge, Layer 1, Layer 2, Cross-chain, Validator, Node, Consensus, PoW, PoS, Halving, Liquidity Mining, Impermanent Loss, Rug Pull, Whitelist, Mainnet, Testnet, Protocol, Governance Token.
    *   Đối với các thuật ngữ crypto phức tạp khác không có trong danh sách trên, hãy **thêm bản dịch hoặc giải thích ngắn Tiếng Việt trong dấu ngoặc đơn**. Ví dụ: "zero-knowledge proofs (bằng chứng không kiến thức)".

5.  **YÊU CẦU ĐẦU RA (OUTPUT REQUIREMENT):**
    *   **Phần 1 - Bài viết chính:** Toàn bộ nội dung bài viết phải được định dạng bằng **Markdown**.
    *   **Phần 2 - Nội dung phụ:** Sau khi hoàn thành bài viết, hãy tạo thêm 2 đoạn sau và phân tách rõ ràng:
        *   `[SAPO]`
        *   Viết một đoạn sapo (mở bài) khoảng 100 chữ.
        *   `[META]`
        *   Viết một đoạn meta description (mô tả SEO) khoảng 100 chữ.

**NỘI DUNG GỐC CẦN XỬ LÝ:**
{request.content}"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Update database
        await db.projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "translated_content": response,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {"translated_content": response}
    
    except Exception as e:
        logging.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@api_router.post("/projects/{project_id}/social")
async def generate_social_content(project_id: str, request: SocialGenerateRequest):
    """Generate social media content using Claude with Vietnamese Community Manager prompt"""
    try:
        # Initialize Claude chat with Vietnamese persona
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"social_{project_id}",
            system_message="Bạn là một người quản lý cộng đồng (Community Manager) cho một kênh tin tức về crypto. Nhiệm vụ của bạn là đọc một bài nghiên cứu chuyên sâu và viết một bài đăng ngắn gọn để thu hút cộng đồng đọc bài viết đầy đủ."
        ).with_model("anthropic", "claude-4-sonnet-20250514")
        
        # Create specialized Vietnamese social content prompt
        prompt = f"""**BỐI CẢNH (CONTEXT):**
Bạn là một người quản lý cộng đồng (Community Manager) cho một kênh tin tức về crypto. Nhiệm vụ của bạn là đọc một bài nghiên cứu chuyên sâu và viết một bài đăng ngắn gọn để thu hút cộng đồng đọc bài viết đầy đủ.

**NHIỆM VỤ (MISSION):**
Dựa vào bài viết được cung cấp, hãy tạo một bài đăng cho các nền tảng mạng xã hội (như Telegram, Facebook) với độ dài khoảng 100 từ, tuân thủ nghiêm ngặt cấu trúc sau:

1.  **Tiêu đề:** Đặt một tiêu đề ngắn gọn, hấp dẫn.
2.  **Dẫn dắt:** Mở đầu bằng cách nêu lên một vấn đề hoặc một bối cảnh chung của thị trường crypto hiện tại.
3.  **Giới thiệu Insight:** Kết nối vấn đề đó với một insight (điểm sáng giá) cốt lõi có trong bài viết. Giới thiệu một cách khéo léo, không mang tính quảng cáo trực tiếp cho dự án được đề cập.
4.  **Kết luận và CTA:** Kết thúc bằng một câu kêu gọi hành động (Call To Action), mời cộng đồng đọc bài viết đầy đủ trên trang GFI Research.

**Lưu ý quan trọng:** Luôn viết với góc nhìn thứ ba, giữ thái độ khách quan và không shill dự án.

**BÀI VIẾT ĐỂ PHÂN TÍCH:**
{request.content}"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the response
        social_content = {
            'facebook': '',
            'twitter': '',
            'hashtags': ''
        }
        
        # Simple parsing
        parts = response.split('FACEBOOK:')
        if len(parts) > 1:
            remaining = parts[1]
            twitter_parts = remaining.split('TWITTER:')
            if len(twitter_parts) > 1:
                social_content['facebook'] = twitter_parts[0].strip()
                hashtag_parts = twitter_parts[1].split('HASHTAGS:')
                if len(hashtag_parts) > 1:
                    social_content['twitter'] = hashtag_parts[0].strip()
                    social_content['hashtags'] = hashtag_parts[1].strip()
                else:
                    social_content['twitter'] = twitter_parts[1].strip()
        
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