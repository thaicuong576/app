import { useState, useEffect } from "react";
import { Routes, Route, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, FileText, Link as LinkIcon, Sparkles, Share2, Copy, ArrowLeft, Home as HomeIcon, Trash2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Component
const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error("Error loading projects:", error);
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <div className="mb-4">
            <div className="flex items-center gap-3 mb-2">
              <Button
                variant="ghost"
                onClick={() => navigate('/')}
                className="hover:bg-white/10 text-white rounded-full"
              >
                <HomeIcon className="h-5 w-5" />
              </Button>
              <h1 className="text-5xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                Partner Content Hub
              </h1>
            </div>
            <p className="text-lg text-white/80 ml-14">Dịch và tạo content tự động cho crypto/blockchain</p>
          </div>
          <div className="ml-14">
            <Button
              data-testid="create-project-btn"
              onClick={() => navigate('/partner-content-hub/create')}
              size="lg"
              className="bg-[#E38400] hover:bg-[#C67300] text-white rounded-xl px-8 shadow-lg hover:shadow-xl transition-all"
            >
              <Sparkles className="mr-2 h-5 w-5" />
              Tạo Project Mới
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-12 w-12 animate-spin text-[#E38400]" />
          </div>
        ) : projects.length === 0 ? (
          <Card className="text-center py-16 bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardContent>
              <FileText className="h-24 w-24 mx-auto mb-6 text-gray-300" />
              <h3 className="text-2xl font-semibold text-gray-700 mb-3">Chưa có project</h3>
              <p className="text-gray-500 mb-6">Tạo project đầu tiên của bạn!</p>
              <Button
                onClick={() => navigate('/partner-content-hub/create')}
                className="bg-[#E38400] hover:bg-[#C67300] text-white rounded-xl px-6"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Tạo Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card
                key={project.id}
                data-testid={`project-card-${project.id}`}
                className="cursor-pointer hover:shadow-2xl transition-all bg-white/95 backdrop-blur-sm border-0 hover:scale-105 transform"
                onClick={() => navigate(`/partner-content-hub/workshop/${project.id}`)}
              >
                <CardHeader>
                  <CardTitle className="text-xl font-bold text-gray-900 line-clamp-2">
                    {project.title}
                  </CardTitle>
                  <CardDescription className="flex items-center text-sm">
                    {project.source_url && (
                      <LinkIcon className="h-3 w-3 mr-1" />
                    )}
                    {project.source_url || 'Manual Entry'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">{project.translated_content && (
                      <div className="flex items-center text-xs text-green-600 bg-green-50 px-3 py-1 rounded-full w-fit">
                        <Sparkles className="h-3 w-3 mr-1" />
                        Translated
                      </div>
                    )}
                    {project.social_content?.facebook && (
                      <div className="flex items-center text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full w-fit">
                        <Share2 className="h-3 w-3 mr-1" />
                        Social Ready
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Create Project Component
const CreateProject = () => {
  const [inputType, setInputType] = useState('url');
  const [url, setUrl] = useState('');
  const [rawText, setRawText] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    if (!url && !rawText) {
      toast.error('Please provide a URL or text');
      return;
    }

    setLoading(true);
    try {
      const payload = inputType === 'url' ? { source_url: url } : { raw_text: rawText };
      const response = await axios.post(`${API}/projects`, payload);
      toast.success('Project created successfully!');
      navigate(`/partner-content-hub/workshop/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error(error.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844] py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <Button
          variant="ghost"
          onClick={() => navigate('/partner-content-hub')}
          className="mb-6 hover:bg-white/10 text-white"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Quay lại Dashboard
        </Button>

        <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
              Tạo Project Mới
            </CardTitle>
            <CardDescription>Bắt đầu bằng cách cung cấp URL hoặc paste nội dung</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={inputType} onValueChange={setInputType} className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="url" data-testid="tab-url">
                  <LinkIcon className="mr-2 h-4 w-4" />
                  From URL
                </TabsTrigger>
                <TabsTrigger value="text" data-testid="tab-text">
                  <FileText className="mr-2 h-4 w-4" />
                  Paste Text
                </TabsTrigger>
              </TabsList>

              <TabsContent value="url" className="space-y-4">
                <div>
                  <Label htmlFor="url" className="text-base font-semibold text-slate-700">Article URL</Label>
                  <Input
                    id="url"
                    data-testid="input-url"
                    placeholder="https://example.com/article"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="mt-2 h-12 text-base"
                  />
                  <p className="text-sm text-slate-500 mt-2">
                    The system will automatically scrape content and download images
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="text" className="space-y-4">
                <div>
                  <Label htmlFor="rawText" className="text-base font-semibold text-slate-700">Content</Label>
                  <Textarea
                    id="rawText"
                    data-testid="input-text"
                    placeholder="Paste your article content here..."
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    className="mt-2 min-h-[300px] text-base"
                  />
                </div>
              </TabsContent>
            </Tabs>

            <Button
              data-testid="submit-create-btn"
              onClick={handleSubmit}
              disabled={loading}
              className="w-full mt-6 h-12 text-base bg-[#E38400] hover:bg-[#C67300] text-white rounded-xl shadow-lg hover:shadow-xl transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Đang tạo project...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-5 w-5" />
                  Tạo Project
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Workshop Component
const Workshop = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [translating, setTranslating] = useState(false);
  const [generatingSocial, setGeneratingSocial] = useState(false);
  const [showSocialModal, setShowSocialModal] = useState(false);
  const [socialContent, setSocialContent] = useState(null);
  const [customPreset, setCustomPreset] = useState('');
  const [customPresetSocial, setCustomPresetSocial] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}`);
      setProject(response.data);
      setContent(response.data.translated_content || response.data.original_content);
      setSocialContent(response.data.social_content);
    } catch (error) {
      console.error('Error loading project:', error);
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const handleTranslate = async () => {
    setTranslating(true);
    try {
      const response = await axios.post(`${API}/projects/${projectId}/translate`, {
        content: project.original_content,
        custom_preset: customPreset
      });
      setContent(response.data.translated_content);
      toast.success('Translation completed!');
    } catch (error) {
      console.error('Translation error:', error);
      toast.error('Translation failed');
    } finally {
      setTranslating(false);
    }
  };

  const handleGenerateSocial = async () => {
    setGeneratingSocial(true);
    try {
      const response = await axios.post(`${API}/projects/${projectId}/social`, {
        content: content,
        custom_preset: customPresetSocial
      });
      setSocialContent(response.data);
      setShowSocialModal(true);
      toast.success('Social content generated!');
    } catch (error) {
      console.error('Social generation error:', error);
      toast.error('Failed to generate social content');
    } finally {
      setGeneratingSocial(false);
    }
  };

  const handleCopyContent = async () => {
    try {
      // Create a ClipboardItem with both HTML and plain text formats
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = content;
      
      // Get plain text as fallback
      const plainText = tempDiv.innerText || tempDiv.textContent;
      
      // Create blob for HTML content
      const htmlBlob = new Blob([content], { type: 'text/html' });
      const textBlob = new Blob([plainText], { type: 'text/plain' });
      
      // Use ClipboardItem to copy with formatting
      const clipboardItem = new ClipboardItem({
        'text/html': htmlBlob,
        'text/plain': textBlob
      });
      
      await navigator.clipboard.write([clipboardItem]);
      toast.success('Content copied with formatting!');
    } catch (error) {
      // Fallback to plain text if rich text copy fails
      console.error('Rich copy failed, using plain text:', error);
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = content;
      const plainText = tempDiv.innerText || tempDiv.textContent;
      navigator.clipboard.writeText(plainText);
      toast.success('Content copied to clipboard!');
    }
  };

  const handleCopyText = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied!`);
  };

  const handleDeleteProject = async () => {
    if (!window.confirm('Bạn có chắc muốn xóa project này không?')) {
      return;
    }

    try {
      await axios.delete(`${API}/projects/${projectId}`);
      toast.success('Project đã được xóa');
      navigate('/partner-content-hub');
    } catch (error) {
      console.error('Delete project error:', error);
      toast.error('Không thể xóa project');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      <div className="container mx-auto px-4 py-8 max-w-[1600px]">
        <div className="flex justify-between items-center mb-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/partner-content-hub')}
            className="hover:bg-white/10 text-white"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Quay lại Dashboard
          </Button>
          
          <Button
            variant="outline"
            onClick={handleDeleteProject}
            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Xóa Project
          </Button>
        </div>

        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            {project.title}
          </h1>
          {project.source_url && (
            <a href={project.source_url} target="_blank" rel="noopener noreferrer" className="text-[#E38400] hover:underline flex items-center">
              <LinkIcon className="h-4 w-4 mr-1" />
              {project.source_url}
            </a>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          {/* Editor Section */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Content Editor</span>
                <Button
                  data-testid="copy-content-btn"
                  onClick={handleCopyContent}
                  variant="outline"
                  size="sm"
                  className="rounded-full"
                >
                  <Copy className="h-4 w-4 mr-1" />
                  Copy Content
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                data-testid="content-editor"
                className="prose max-w-none min-h-[600px] p-6 bg-white rounded-lg border border-slate-200 overflow-auto"
                dangerouslySetInnerHTML={{ __html: content }}
              />
            </CardContent>
          </Card>

          {/* AI Control Panel */}
          <div className="space-y-4">
            <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl sticky top-8">
              <CardHeader>
                <CardTitle className="text-xl">AI Control Panel</CardTitle>
                <CardDescription>Transform your content with AI</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Custom Preset Input */}
                <div className="space-y-2">
                  <Label htmlFor="customPreset" className="text-sm font-semibold text-gray-700">
                    Custom Preset (Tùy chọn)
                  </Label>
                  <Textarea
                    id="customPreset"
                    placeholder="Thêm hướng dẫn tùy chỉnh kết hợp với preset mặc định..."
                    value={customPreset}
                    onChange={(e) => setCustomPreset(e.target.value)}
                    className="min-h-[100px] text-sm"
                  />
                  <p className="text-xs text-gray-500">
                    Hướng dẫn này sẽ được kết hợp với preset dịch thuật mặc định
                  </p>
                </div>

                <Button
                  data-testid="translate-btn"
                  onClick={handleTranslate}
                  disabled={translating}
                  className="w-full h-12 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white rounded-xl shadow-md"
                >
                  {translating ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Đang dịch...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      🚀 Dịch và Tái cấu trúc
                    </>
                  )}
                </Button>

                {/* Custom Preset for Social Content */}
                <div className="space-y-2 pt-4 border-t border-gray-200">
                  <Label htmlFor="customPresetSocial" className="text-sm font-semibold text-gray-700">
                    Custom Preset Social (Tùy chọn)
                  </Label>
                  <Textarea
                    id="customPresetSocial"
                    placeholder="Thêm hướng dẫn tùy chỉnh cho social content..."
                    value={customPresetSocial}
                    onChange={(e) => setCustomPresetSocial(e.target.value)}
                    className="min-h-[100px] text-sm"
                  />
                  <p className="text-xs text-gray-500">
                    Hướng dẫn này sẽ được kết hợp với preset tạo social content mặc định
                  </p>
                </div>

                <Button
                  data-testid="generate-social-btn"
                  onClick={handleGenerateSocial}
                  disabled={generatingSocial}
                  className="w-full h-12 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl shadow-md"
                >
                  {generatingSocial ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Đang tạo...
                    </>
                  ) : (
                    <>
                      <Share2 className="mr-2 h-5 w-5" />
                      ✍️ Tạo Content Social
                    </>
                  )}
                </Button>

                {socialContent && (
                  <Button
                    data-testid="view-social-btn"
                    onClick={() => setShowSocialModal(true)}
                    variant="outline"
                    className="w-full h-10 rounded-lg"
                  >
                    Xem Nội dung Social
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Social Content Modal */}
      <Dialog open={showSocialModal} onOpenChange={setShowSocialModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto" data-testid="social-modal">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold">Nội dung Social Media</DialogTitle>
            <DialogDescription>Nội dung sẵn sàng để đăng lên các kênh mạng xã hội</DialogDescription>
          </DialogHeader>
          <div className="space-y-6 mt-4">
            {socialContent?.facebook && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-lg text-slate-900">Bài đăng Social Media</h3>
                  <Button
                    data-testid="copy-facebook-btn"
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopyText(socialContent.facebook, 'Nội dung social')}
                    className="rounded-full"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Sao chép
                  </Button>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <p className="text-slate-700 whitespace-pre-wrap">{socialContent.facebook}</p>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default function PartnerContentHub() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/create" element={<CreateProject />} />
      <Route path="/workshop/:projectId" element={<Workshop />} />
    </Routes>
  );
}
