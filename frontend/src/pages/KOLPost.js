import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, FileText, Link as LinkIcon, Sparkles, Copy, Trash2, Home as HomeIcon, Users } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const KOLPost = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [sourceType, setSourceType] = useState('text');
  const [informationSource, setInformationSource] = useState('');
  const [insightRequired, setInsightRequired] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [currentPost, setCurrentPost] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/kol-posts`);
      setPosts(response.data);
    } catch (error) {
      console.error("Error loading posts:", error);
      toast.error("Không thể tải danh sách bài viết");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!informationSource.trim()) {
      toast.error('Vui lòng nhập thông tin nguồn');
      return;
    }
    if (!insightRequired.trim()) {
      toast.error('Vui lòng nhập nhận định cần có');
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post(`${API}/kol-posts/generate`, {
        information_source: informationSource,
        insight_required: insightRequired,
        source_type: sourceType
      });
      
      setGeneratedContent(response.data.generated_content);
      setCurrentPost(response.data);
      setShowPreview(true);
      toast.success('Đã tạo bài viết thành công!');
      
      // Reload posts list
      loadPosts();
      
      // Clear inputs
      setInformationSource('');
      setInsightRequired('');
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
      await axios.delete(`${API}/kol-posts/${postId}`);
      toast.success('Đã xóa bài viết');
      loadPosts();
    } catch (error) {
      console.error("Error deleting post:", error);
      toast.error("Không thể xóa bài viết");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Đã copy vào clipboard!');
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
                KOL Post
              </h1>
            </div>
            <p className="text-lg text-white/80 ml-14">Tạo bài viết theo phong cách KOL crypto</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <Sparkles className="h-6 w-6 mr-2 text-[#E38400]" />
                Tạo bài viết mới
              </CardTitle>
              <CardDescription>
                Nhập thông tin và nhận định để AI tạo bài viết
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
                    <Label>Thông tin cần học</Label>
                    <Textarea
                      placeholder="Paste nội dung thông tin cần học vào đây..."
                      value={informationSource}
                      onChange={(e) => setInformationSource(e.target.value)}
                      rows={8}
                      className="mt-2"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="url" className="space-y-4 mt-4">
                  <div>
                    <Label>URL thông tin</Label>
                    <Textarea
                      placeholder="https://example.com/article"
                      value={informationSource}
                      onChange={(e) => setInformationSource(e.target.value)}
                      rows={3}
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      AI sẽ tự động cào title và content chính từ URL
                    </p>
                  </div>
                </TabsContent>
              </Tabs>

              {/* Insight Input */}
              <div>
                <Label>Nhận định cần có</Label>
                <Textarea
                  placeholder="Nhập nhận định ngắn gọn của bạn... (Lưu ý: viết ngắn gọn, không giải thích dài dòng)"
                  value={insightRequired}
                  onChange={(e) => setInsightRequired(e.target.value)}
                  rows={4}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  💡 Nhận định nên ngắn gọn, đi thẳng vào vấn đề
                </p>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full bg-[#E38400] hover:bg-[#c77200] text-white py-6 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Đang tạo bài viết...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-5 w-5" />
                    Tạo bài viết
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Posts List */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-gray-900 flex items-center">
                <FileText className="h-6 w-6 mr-2 text-[#E38400]" />
                Bài viết đã tạo
              </CardTitle>
              <CardDescription>
                Danh sách các bài viết KOL của bạn
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-12 w-12 animate-spin text-[#E38400]" />
                </div>
              ) : posts.length === 0 ? (
                <div className="text-center py-16">
                  <Users className="h-24 w-24 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">Chưa có bài viết</h3>
                  <p className="text-gray-500">Tạo bài viết đầu tiên của bạn</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {posts.map((post) => (
                    <Card
                      key={post.id}
                      className="hover:shadow-lg transition-all cursor-pointer border-l-4 border-l-[#E38400]"
                      onClick={() => {
                        setCurrentPost(post);
                        setGeneratedContent(post.generated_content);
                        setShowPreview(true);
                      }}
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <p className="text-sm text-gray-500 mb-1">
                              {post.source_type === 'url' ? (
                                <span className="flex items-center">
                                  <LinkIcon className="h-3 w-3 mr-1" />
                                  URL Source
                                </span>
                              ) : (
                                <span className="flex items-center">
                                  <FileText className="h-3 w-3 mr-1" />
                                  Text Source
                                </span>
                              )}
                            </p>
                            <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-2">
                              {post.generated_content?.slice(0, 100)}...
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(post.created_at).toLocaleString('vi-VN')}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(post.id);
                            }}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
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
                <Sparkles className="h-6 w-6 mr-2 text-[#E38400]" />
                Bài viết KOL
              </DialogTitle>
              <DialogDescription>
                Bài viết được tạo theo phong cách KOL crypto
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              {currentPost && (
                <>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Nhận định:</p>
                      <p className="text-sm text-gray-700">{currentPost.insight_required}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Nguồn:</p>
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {currentPost.source_type === 'url' ? (
                          <a href={currentPost.information_source} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {currentPost.information_source}
                          </a>
                        ) : (
                          currentPost.information_source.slice(0, 150) + '...'
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="bg-white border-2 border-[#E38400] rounded-lg p-6">
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {generatedContent}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => copyToClipboard(generatedContent)}
                      className="flex-1 bg-[#E38400] hover:bg-[#c77200] text-white"
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Copy bài viết
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
      </div>
    </div>
  );
};

export default KOLPost;
