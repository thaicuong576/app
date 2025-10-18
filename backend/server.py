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
    custom_preset: str = ""

class SocialGenerateRequest(BaseModel):
    content: str

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

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully", "id": project_id}

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