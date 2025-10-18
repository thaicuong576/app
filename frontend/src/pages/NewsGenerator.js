import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, FileText, Link as LinkIcon, Sparkles, Copy, Trash2, Edit2, Home as HomeIcon, Newspaper } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NewsGenerator = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [sourceType, setSourceType] = useState('text');
  const [sourceContent, setSourceContent] = useState('');
  const [opinion, setOpinion] = useState('');
  const [styleChoice, setStyleChoice] = useState('auto');
  const [generatedContent, setGeneratedContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentArticle, setCurrentArticle] = useState(null);
  const [editContent, setEditContent] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/news`);
      setArticles(response.data);
    } catch (error) {
      console.error("Error loading articles:", error);
      toast.error("Không thể tải danh sách bài viết");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!sourceContent.trim()) {
      toast.error('Vui lòng nhập nội dung nguồn');
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post(`${API}/news/generate`, {
        source_content: sourceContent,
        opinion: opinion || null,
        style_choice: styleChoice,
        source_type: sourceType
      });
      
      setGeneratedContent(response.data.generated_content);
      setCurrentArticle(response.data);
      setShowPreview(true);
      toast.success('🎉 Tin tức đã được tạo thành công!');
      
      // Reload articles list
      loadArticles();
      
      // Clear inputs
      setSourceContent('');
      setOpinion('');
      setStyleChoice('auto');
    } catch (error) {
      console.error("Error generating article:", error);
      toast.error(error.response?.data?.detail || "Không thể tạo tin tức");
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (articleId) => {
    if (!window.confirm('Bạn có chắc muốn xóa bài viết này?')) {
      return;
    }

    try {
      await axios.delete(`${API}/news/${articleId}`);
      toast.success('Đã xóa bài viết');
      loadArticles();
      if (currentArticle?.id === articleId) {
        setShowPreview(false);
        setShowEditModal(false);
      }
    } catch (error) {
      console.error("Error deleting article:", error);
      toast.error("Không thể xóa bài viết");
    }
  };

  const handleEditClick = (article) => {
    setCurrentArticle(article);
    setEditContent(article.generated_content);
    setShowEditModal(true);
    setShowPreview(false);
  };

  const handleSaveEdit = async () => {
    if (!editContent.trim()) {
      toast.error('Nội dung không được để trống');
      return;
    }

    try {
      await axios.put(`${API}/news/${currentArticle.id}`, {
        generated_content: editContent
      });
      toast.success('Đã cập nhật bài viết');
      loadArticles();
      setShowEditModal(false);
      
      // Update current article
      const updatedArticle = { ...currentArticle, generated_content: editContent };
      setCurrentArticle(updatedArticle);
      setGeneratedContent(editContent);
    } catch (error) {
      console.error("Error updating article:", error);
      toast.error("Không thể cập nhật bài viết");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Đã copy vào clipboard!');
  };

  const getStyleLabel = (style) => {
    switch(style) {
      case 'style1': return 'Style 1 (List)';
      case 'style2': return 'Style 2 (Prose)';
      default: return 'Auto';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      <div className="container mx-auto px-4 py-12 max-w-7xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Button
                variant="ghost"
                onClick={() => navigate('/')}
                className="hover:bg-white/10 text-white rounded-full"
              >
                <HomeIcon className="h-5 w-5" />
              </Button>
              <h1 className="text-5xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                News Generator
              </h1>
            </div>
            <p className="text-lg text-white/80 ml-14">Tạo tin tức crypto tự động với AI</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <Sparkles className="h-6 w-6 mr-2 text-blue-600" />
                🔥 Tạo tin tức mới
              </CardTitle>
              <CardDescription>
                Nhập nội dung nguồn và để AI tạo bản tóm tắt crypto
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Source Type Tabs */}
              <Tabs value={sourceType} onValueChange={setSourceType}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="text">
                    <FileText className="h-4 w-4 mr-2" />
                    Text
                  </TabsTrigger>
                  <TabsTrigger value="url">
                    <LinkIcon className="h-4 w-4 mr-2" />
                    URL
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="text" className="space-y-4 mt-4">
                  <div>
                    <Label>Nội dung nguồn (tiếng Anh)</Label>
                    <Textarea
                      placeholder="Paste nội dung bài viết tiếng Anh vào đây..."
                      value={sourceContent}
                      onChange={(e) => setSourceContent(e.target.value)}
                      rows={8}
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      ✨ Paste bài viết crypto tiếng Anh - AI sẽ tóm tắt thành tin tức tiếng Việt súc tích
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="url" className="space-y-4 mt-4">
                  <div>
                    <Label>URL bài viết</Label>
                    <Textarea
                      placeholder="https://cointelegraph.com/news/..."
                      value={sourceContent}
                      onChange={(e) => setSourceContent(e.target.value)}
                      rows={3}
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      🌐 AI sẽ tự động cào title và content từ URL
                    </p>
                  </div>
                </TabsContent>
              </Tabs>

              {/* Opinion Field */}
              <div>
                <Label>Nhận xét/Opinion (Tùy chọn)</Label>
                <Textarea
                  placeholder="Thêm nhận xét hoặc góc nhìn của bạn về tin này..."
                  value={opinion}
                  onChange={(e) => setOpinion(e.target.value)}
                  rows={3}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  💡 Giúp AI hiểu tone và góc độ bạn muốn
                </p>
              </div>

              {/* Style Selection */}
              <div>
                <Label>Chọn Style</Label>
                <Select value={styleChoice} onValueChange={setStyleChoice}>
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Chọn style viết" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">
                      <span className="flex items-center">
                        <Sparkles className="h-4 w-4 mr-2" />
                        Auto (AI tự chọn)
                      </span>
                    </SelectItem>
                    <SelectItem value="style1">Style 1 (List) - Metrics/Data</SelectItem>
                    <SelectItem value="style2">Style 2 (Prose) - Opinion/Trend</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  🎨 Style 1 dùng list (👉) cho tin có số liệu. Style 2 là văn xuôi cho tin nhận định
                </p>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Đang tạo tin tức...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-5 w-5" />
                    ✨ Tạo tin tức
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Articles List */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <Newspaper className="h-6 w-6 mr-2 text-blue-600" />
                Tin tức đã tạo
              </CardTitle>
              <CardDescription>
                Danh sách các bài tin tức crypto của bạn
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
                </div>
              ) : articles.length === 0 ? (
                <div className="text-center py-16">
                  <Newspaper className="h-24 w-24 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">Chưa có tin tức</h3>
                  <p className="text-gray-500">Tạo tin tức crypto đầu tiên của bạn!</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {articles.map((article) => (
                    <Card
                      key={article.id}
                      className="hover:shadow-lg transition-all cursor-pointer border-l-4 border-l-blue-600"
                      onClick={() => {
                        setCurrentArticle(article);
                        setGeneratedContent(article.generated_content);
                        setShowPreview(true);
                      }}
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                {getStyleLabel(article.style_choice)}
                              </span>
                              <span className="text-xs text-gray-500">
                                {article.source_type === 'url' ? (
                                  <span className="flex items-center">
                                    <LinkIcon className="h-3 w-3 mr-1" />
                                    URL
                                  </span>
                                ) : (
                                  <span className="flex items-center">
                                    <FileText className="h-3 w-3 mr-1" />
                                    Text
                                  </span>
                                )}
                              </span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-2">
                              {article.generated_content?.slice(0, 100)}...
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(article.created_at).toLocaleString('vi-VN')}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditClick(article);
                              }}
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(article.id);
                              }}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
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
              <DialogTitle className="text-2xl font-bold flex items-center">
                <Newspaper className="h-6 w-6 mr-2 text-blue-600" />
                Tin tức Crypto
              </DialogTitle>
              <DialogDescription>
                Bản tóm tắt tin tức được tạo bởi AI
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              {currentArticle && (
                <>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Style:</p>
                      <p className="text-sm text-gray-700">{getStyleLabel(currentArticle.style_choice)}</p>
                    </div>
                    {currentArticle.opinion && (
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase">Opinion:</p>
                        <p className="text-sm text-gray-700">{currentArticle.opinion}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Nguồn:</p>
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {currentArticle.source_type === 'url' ? (
                          <a href={currentArticle.source_content} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {currentArticle.source_content}
                          </a>
                        ) : (
                          currentArticle.source_content.slice(0, 150) + '...'
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="bg-white border-2 border-blue-600 rounded-lg p-6">
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {generatedContent}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => copyToClipboard(generatedContent)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Copy tin tức
                    </Button>
                    <Button
                      onClick={() => {
                        setShowPreview(false);
                        handleEditClick(currentArticle);
                      }}
                      variant="outline"
                      className="border-blue-600 text-blue-600 hover:bg-blue-50"
                    >
                      <Edit2 className="mr-2 h-4 w-4" />
                      Chỉnh sửa
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowPreview(false)}
                    >
                      Đóng
                    </Button>
                  </div>
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit Dialog */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold flex items-center">
                <Edit2 className="h-6 w-6 mr-2 text-blue-600" />
                Chỉnh sửa tin tức
              </DialogTitle>
              <DialogDescription>
                Tùy chỉnh nội dung tin tức theo ý bạn
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <div>
                <Label>Nội dung tin tức</Label>
                <Textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={15}
                  className="mt-2 font-mono text-sm"
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleSaveEdit}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Lưu thay đổi
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowEditModal(false)}
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

export default NewsGenerator;
