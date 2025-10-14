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

# LLM API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

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
    """Translate and restructure content using Gemini with user's preset prompt"""
    try:
        # Initialize Gemini chat with Google API key
        chat = LlmChat(
            api_key=GOOGLE_API_KEY,
            session_id=f"translate_{project_id}",
            system_message="Bạn là một chuyên gia viết báo về crypto."
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Use exact user preset prompt
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

Sau khi viết xong, hãy viết giúp tôi 2 đoạn khác, gồm đoạn sapo và đoạn meta description, mỗi đoạn 100 chữ. Đặt meta description ở đầu tiên, sau đó là sapo, rồi mới đến phần "Giới thiệu".

Nội dung:
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
    """Generate social media content using Gemini with user's preset prompt"""
    try:
        # Initialize Gemini chat with Google API key
        chat = LlmChat(
            api_key=GOOGLE_API_KEY,
            session_id=f"social_{project_id}",
            system_message="Bạn là một người quản lý cộng đồng (Community Manager) cho một kênh tin tức về crypto."
        ).with_model("gemini", "gemini-2.0-flash-exp")
        
        # Use exact user preset prompt
        prompt = f"""ok giờ đọc bài đó và hãy viết bài post telegram ngắn cho tôi nhé, khoảng 100 từ thôi, theo outline sau: title dẫn dắt các vấn đề hiện tại của thị trường sau đó giới thiệu 1 phần nội dung có insight (ngắn, sao cho đừng quá shill Succinct) kết luận và CTA về bài GFI Research gốc
Lưu ý: Viết với góc nhìn thứ ba, không shill dự án

Bài viết:
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