import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Home, RefreshCw, BookOpen, Trash2, Copy, Loader2, Rss, Search } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const NewsDistributor = () => {
  const { toast } = useToast();
  
  // State management
  const [articles, setArticles] = useState([]);
  const [selectedArticleId, setSelectedArticleId] = useState('');
  const [vocabularyOutput, setVocabularyOutput] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [totalArticles, setTotalArticles] = useState(0);
  const [totalVocabulary, setTotalVocabulary] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  // Load initial data
  useEffect(() => {
    fetchArticles();
    fetchVocabularyCount();
  }, []);

  const fetchArticles = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/articles`);
      if (!response.ok) throw new Error('Failed to fetch articles');
      
      const data = await response.json();
      setArticles(data.articles || []);
      setTotalArticles(data.total || 0);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };

  const fetchVocabularyCount = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/vocabulary-count`);
      if (!response.ok) throw new Error('Failed to fetch vocabulary count');
      
      const data = await response.json();
      setTotalVocabulary(data.total_vocabulary || 0);
    } catch (error) {
      console.error('Error fetching vocabulary count:', error);
    }
  };

  const handleRefreshRSS = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/refresh-rss`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to refresh RSS feed');
      
      const data = await response.json();
      
      toast({
        title: "RSS Feed đã cập nhật!",
        description: `${data.articles_saved} bài mới, ${data.articles_updated} bài cập nhật. Tổng: ${data.total_articles} bài.`,
      });
      
      // Refresh articles list
      await fetchArticles();
    } catch (error) {
      toast({
        title: "Lỗi",
        description: "Không thể làm mới RSS feed: " + error.message,
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExtractVocabulary = async () => {
    if (!selectedArticleId) {
      toast({
        title: "Chưa chọn bài viết",
        description: "Vui lòng chọn một bài viết để trích xuất từ vựng.",
        variant: "destructive",
      });
      return;
    }

    setIsExtracting(true);
    setVocabularyOutput('');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/extract-vocabulary/${selectedArticleId}`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to extract vocabulary');
      
      const data = await response.json();
      
      setVocabularyOutput(data.output_content);
      
      toast({
        title: "Trích xuất thành công!",
        description: `Đã thu thập ${data.new_vocab_count} từ vựng mới. Tổng: ${data.total_vocab_count} từ.`,
      });
      
      // Update vocabulary count
      setTotalVocabulary(data.total_vocab_count);
    } catch (error) {
      toast({
        title: "Lỗi",
        description: "Không thể trích xuất từ vựng: " + error.message,
        variant: "destructive",
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const handleResetVocabulary = async () => {
    if (!window.confirm('Bạn có chắc muốn xóa toàn bộ kho từ vựng? Hành động này không thể hoàn tác.')) {
      return;
    }

    setIsResetting(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/reset-vocabulary`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to reset vocabulary');
      
      const data = await response.json();
      
      toast({
        title: "Đã reset thành công!",
        description: `Đã xóa ${data.deleted_count} từ vựng.`,
      });
      
      setTotalVocabulary(0);
      setVocabularyOutput('');
    } catch (error) {
      toast({
        title: "Lỗi",
        description: "Không thể reset kho từ vựng: " + error.message,
        variant: "destructive",
      });
    } finally {
      setIsResetting(false);
    }
  };

  const handleCopyOutput = () => {
    if (!vocabularyOutput) {
      toast({
        title: "Không có nội dung",
        description: "Chưa có từ vựng để copy.",
        variant: "destructive",
      });
      return;
    }

    navigator.clipboard.writeText(vocabularyOutput);
    toast({
      title: "Đã copy!",
      description: "Nội dung từ vựng đã được copy vào clipboard.",
    });
  };

  // Filter articles based on search term
  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedArticle = articles.find(a => a.id === selectedArticleId);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      {/* Header */}
      <div className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="text-gray-600 hover:text-[#ef4444] transition-colors">
                <Home className="h-6 w-6" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-orange-600">
                  <Rss className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900">News Distributor</h1>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <BookOpen className="h-4 w-4" />
              <span>{totalVocabulary} từ vựng</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto space-y-6">
          
          {/* RSS Control Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Rss className="h-5 w-5 text-red-500" />
                RSS Feed từ CoinDesk
              </h2>
              <button
                onClick={handleRefreshRSS}
                disabled={isRefreshing}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-500 to-orange-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
              >
                {isRefreshing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {isRefreshing ? 'Đang làm mới...' : 'Làm mới RSS Feed'}
              </button>
            </div>
            <p className="text-gray-600">
              Đã lưu <span className="font-bold text-red-600">{totalArticles}</span> bài viết từ CoinDesk
            </p>
          </div>

          {/* Article Selection Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Chọn bài viết để phân tích</h2>
            
            {/* Search Bar */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm kiếm bài viết..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Article Dropdown */}
            <select
              value={selectedArticleId}
              onChange={(e) => setSelectedArticleId(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent mb-4"
            >
              <option value="">-- Chọn bài viết --</option>
              {filteredArticles.map((article) => (
                <option key={article.id} value={article.id}>
                  {article.title} ({article.published_date ? new Date(article.published_date).toLocaleDateString('vi-VN') : 'N/A'})
                </option>
              ))}
            </select>

            {/* Selected Article Preview */}
            {selectedArticle && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">{selectedArticle.title}</h3>
                <p className="text-sm text-gray-600 line-clamp-3">{selectedArticle.description}</p>
                <a 
                  href={selectedArticle.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-red-600 hover:text-red-700 mt-2 inline-block"
                >
                  Xem bài gốc →
                </a>
              </div>
            )}

            {/* Extract Button */}
            <button
              onClick={handleExtractVocabulary}
              disabled={!selectedArticleId || isExtracting}
              className="w-full mt-4 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-red-500 to-orange-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Đang trích xuất từ vựng...
                </>
              ) : (
                <>
                  <BookOpen className="h-5 w-5" />
                  Trích xuất từ vựng
                </>
              )}
            </button>
          </div>

          {/* Vocabulary Output Section */}
          {vocabularyOutput && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Kết quả</h2>
                <button
                  onClick={handleCopyOutput}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </button>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border-2 border-red-200">
                <pre className="whitespace-pre-wrap text-gray-800 font-mono text-sm">
                  {vocabularyOutput}
                </pre>
              </div>
            </div>
          )}

          {/* Vocabulary Management Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Quản lý kho từ vựng</h2>
            <div className="flex items-center justify-between">
              <div className="text-gray-600">
                Tổng số từ vựng đã thu thập: <span className="font-bold text-red-600">{totalVocabulary}</span>
              </div>
              <button
                onClick={handleResetVocabulary}
                disabled={isResetting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isResetting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                {isResetting ? 'Đang reset...' : 'Reset kho từ vựng'}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default NewsDistributor;
