import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Globe, Sparkles, Copy, Trash2, Edit2, Home as HomeIcon, FileText, Link as LinkIcon } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SocialToWebsite = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [sourceType, setSourceType] = useState('url'); // 'url' or 'text'
  const [websiteLink, setWebsiteLink] = useState('');
  const [websiteContent, setWebsiteContent] = useState(''); // For text input
  const [title, setTitle] = useState('');
  const [introduction, setIntroduction] = useState('');
  const [highlight, setHighlight] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentPost, setCurrentPost] = useState(null);
  const [editContent, setEditContent] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/social-posts`);
      setPosts(response.data);
    } catch (error) {
      console.error("Error loading posts:", error);
      toast.error("Không thể tải danh sách bài viết");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    // Check based on source type
    if (sourceType === 'url' && !websiteLink.trim()) {
      toast.error('Vui lòng nhập link website');
      return;
    }
    if (sourceType === 'text' && !websiteContent.trim()) {
      toast.error('Vui lòng nhập nội dung website');
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post(`${API}/social-posts/generate`, {
        website_link: sourceType === 'url' ? websiteLink : null,
        website_content: sourceType === 'text' ? websiteContent : null,
        source_type: sourceType,
        title: title || null,
        introduction: introduction || null,
        highlight: highlight || null
      });
      
      setGeneratedContent(response.data.generated_content);
      setCurrentPost(response.data);
      setShowPreview(true);
      toast.success('🎉 Bài viết social đã được tạo thành công!');
      
      // Reload posts list
      loadPosts();
      
      // Clear inputs
      setWebsiteLink('');
      setWebsiteContent('');
      setTitle('');
      setIntroduction('');
      setHighlight('');
    } catch (error) {
      console.error("Error generating post:", error);
      toast.error(error.response?.data?.detail || "Không thể tạo bài viết");
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (postId) => {
    if (!window.confirm('Bạn có chắc muốn xóa bài viết này?')) {
      return;
    }

    try {
      await axios.delete(`${API}/social-posts/${postId}`);
      toast.success('Đã xóa bài viết');
      loadPosts();
      if (currentPost?.id === postId) {
        setShowPreview(false);
        setShowEditModal(false);
      }
    } catch (error) {
      console.error("Error deleting post:", error);
      toast.error("Không thể xóa bài viết");
    }
  };

  const handleEdit = (post) => {
    setCurrentPost(post);
    setEditContent(post.generated_content);
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    try {
      await axios.put(`${API}/social-posts/${currentPost.id}`, {
        generated_content: editContent
      });
      toast.success('Đã cập nhật bài viết');
      setShowEditModal(false);
      loadPosts();
      
      // Update preview if it's open
      if (showPreview && currentPost) {
        setGeneratedContent(editContent);
      }
    } catch (error) {
      console.error("Error updating post:", error);
      toast.error("Không thể cập nhật bài viết");
    }
  };

  const handleCopy = (content) => {
    navigator.clipboard.writeText(content);
    toast.success('✅ Đã copy nội dung');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
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
                Social-to-Website Post
              </h1>
            </div>
            <p className="text-lg text-white/80 ml-14">Tạo bài post social dẫn traffic về website GFI Research</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <Sparkles className="h-6 w-6 mr-2 text-green-600" />
                🔥 Tạo bài viết mới
              </CardTitle>
              <CardDescription>
                Nhập link website và tùy chọn các phần - AI sẽ tự động điền các phần trống
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Website Link */}
              <div>
                <Label>Link Website GFI Research <span className="text-red-500">*</span></Label>
                <Input
                  placeholder="https://gfiresearch.net/..."
                  value={websiteLink}
                  onChange={(e) => setWebsiteLink(e.target.value)}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  🌐 Link bài phân tích chi tiết trên website
                </p>
              </div>

              {/* Title Field */}
              <div>
                <Label>Title / Hook (Tùy chọn)</Label>
                <Textarea
                  placeholder="VD: 🔥 Gọi vốn 130 TRIỆU ĐÔ với định giá 1 TỶ ĐÔ..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  rows={3}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  💡 Để trống nếu muốn AI tự sinh hook giật tít với số liệu
                </p>
              </div>

              {/* Introduction Field */}
              <div>
                <Label>Giới thiệu dự án (Tùy chọn)</Label>
                <Textarea
                  placeholder="VD: ZAMA là công ty chuyên về Fully Homomorphic Encryption..."
                  value={introduction}
                  onChange={(e) => setIntroduction(e.target.value)}
                  rows={3}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  📝 Để trống nếu muốn AI tự tóm tắt từ bài web
                </p>
              </div>

              {/* Highlight Field */}
              <div>
                <Label>Điểm nổi bật / Leak (Tùy chọn)</Label>
                <Textarea
                  placeholder="VD: Gọi vốn thành công với sự tham gia của Multicoin, Pantera..."
                  value={highlight}
                  onChange={(e) => setHighlight(e.target.value)}
                  rows={3}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  ⚡ Để trống nếu muốn AI tự chọn insight hấp dẫn nhất
                </p>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-6 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Đang tạo bài viết...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-5 w-5" />
                    ✨ Tạo bài viết social
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Posts List */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <Globe className="h-6 w-6 mr-2 text-green-600" />
                Bài viết đã tạo
              </CardTitle>
              <CardDescription>
                Danh sách các bài social post của bạn
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-12 w-12 animate-spin text-green-600" />
                </div>
              ) : posts.length === 0 ? (
                <div className="text-center py-16">
                  <Globe className="h-24 w-24 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">Chưa có bài viết</h3>
                  <p className="text-gray-500">Tạo bài social post đầu tiên của bạn!</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {posts.map((post) => (
                    <Card
                      key={post.id}
                      className="hover:shadow-lg transition-all cursor-pointer border-l-4 border-l-green-600"
                      onClick={() => {
                        setCurrentPost(post);
                        setGeneratedContent(post.generated_content);
                        setShowPreview(true);
                      }}
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-2">
                              {post.generated_content?.slice(0, 100)}...
                            </p>
                            <p className="text-xs text-gray-400 truncate mb-1">
                              🌐 {post.website_link}
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(post.created_at).toLocaleString('vi-VN')}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(post);
                              }}
                              className="hover:bg-blue-50"
                            >
                              <Edit2 className="h-4 w-4 text-blue-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopy(post.generated_content);
                              }}
                              className="hover:bg-green-50"
                            >
                              <Copy className="h-4 w-4 text-green-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(post.id);
                              }}
                              className="hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Preview Dialog */}
        <Dialog open={showPreview} onOpenChange={setShowPreview}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <FileText className="h-6 w-6 mr-2 text-green-600" />
                Preview Bài Viết
              </DialogTitle>
              <DialogDescription>
                Bài social post đã được tạo thành công
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-6 rounded-lg">
                <pre className="whitespace-pre-wrap font-sans text-gray-800 leading-relaxed">
                  {generatedContent}
                </pre>
              </div>
              
              {currentPost?.website_link && (
                <div className="text-sm text-gray-500 border-t pt-4">
                  <p className="font-medium mb-1">Link website:</p>
                  <a 
                    href={currentPost.website_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:underline break-all"
                  >
                    {currentPost.website_link}
                  </a>
                </div>
              )}
              
              <div className="flex gap-2 pt-4">
                <Button
                  onClick={() => handleCopy(generatedContent)}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Copy className="mr-2 h-4 w-4" />
                  Copy nội dung
                </Button>
                <Button
                  onClick={() => handleEdit(currentPost)}
                  variant="outline"
                  className="flex-1"
                >
                  <Edit2 className="mr-2 h-4 w-4" />
                  Chỉnh sửa
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit Dialog */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold text-gray-900">
                Chỉnh sửa nội dung
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={15}
                className="font-sans"
              />
              
              <div className="flex gap-2">
                <Button
                  onClick={handleSaveEdit}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  💾 Lưu thay đổi
                </Button>
                <Button
                  onClick={() => setShowEditModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Hủy
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default SocialToWebsite;
