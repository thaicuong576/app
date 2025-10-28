import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Home, RefreshCw, BookOpen, Trash2, Copy, Loader2, Rss, Calendar, Play, X, Eye } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const NewsDistributor = () => {
  const { toast } = useToast();
  
  // State management
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [vocabularyOutput, setVocabularyOutput] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [totalArticles, setTotalArticles] = useState(0);
  const [totalVocabulary, setTotalVocabulary] = useState(0);
  const [allVocabulary, setAllVocabulary] = useState([]);
  const [showVocabModal, setShowVocabModal] = useState(false);
  const [vocabSearchTerm, setVocabSearchTerm] = useState('');

  // Load initial data
  useEffect(() => {
    fetchVocabularyCount();
    fetchAvailableDates();
  }, []);

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

  const fetchAvailableDates = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/available-dates`);
      if (!response.ok) throw new Error('Failed to fetch available dates');
      
      const data = await response.json();
      setAvailableDates(data.dates || []);
    } catch (error) {
      console.error('Error fetching available dates:', error);
    }
  };

  const fetchAllVocabulary = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news-distributor/vocabulary`);
      if (!response.ok) throw new Error('Failed to fetch vocabulary');
      
      const data = await response.json();
      setAllVocabulary(data.vocabulary || []);
    } catch (error) {
      console.error('Error fetching vocabulary:', error);
      toast({
        title: "Lỗi",
        description: "Không thể tải danh sách từ vựng: " + error.message,
        variant: "destructive",
      });
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
      
      setTotalArticles(data.total_articles);
      
      // Refresh available dates
      await fetchAvailableDates();
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

  const handleExtractByDate = async () => {
    if (!selectedDate) {
      toast({
        title: "Chưa chọn ngày",
        description: "Vui lòng chọn ngày để trích xuất từ vựng.",
        variant: "destructive",
      });
      return;
    }

    setIsExtracting(true);
    setVocabularyOutput('');
    
    try {
      toast({
        title: "Bắt đầu xử lý...",
        description: "Đang trích xuất từ vựng từ tất cả bài viết trong ngày đã chọn.",
      });

      const response = await fetch(`${BACKEND_URL}/api/news-distributor/auto-extract?selected_date=${selectedDate}`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to extract vocabulary');
      
      const data = await response.json();
      
      toast({
        title: "Hoàn thành!",
        description: `Đã xử lý ${data.total_articles} bài viết. Thu thập ${data.total_vocab_extracted} từ vựng (${data.new_vocab_count} mới).`,
      });
      
      // Update vocabulary count
      setTotalVocabulary(data.total_vocab_count);
      
      // Show the content template output
      setVocabularyOutput(data.output_content || "Không có từ vựng nào được thu thập.");
      
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

  const handleViewAllVocabulary = async () => {
    await fetchAllVocabulary();
    setShowVocabModal(true);
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

  // Filter vocabulary for modal search
  const filteredVocabulary = allVocabulary.filter(item => {
    const searchLower = vocabSearchTerm.toLowerCase();
    return (
      item.original_word?.toLowerCase().includes(searchLower) ||
      item.vietnamese_definition?.toLowerCase().includes(searchLower)
    );
  });

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
        <div className="max-w-4xl mx-auto space-y-6">
          
          {/* RSS Control Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Rss className="h-5 w-5 text-red-500" />
                RSS Feed từ CoinTelegraph
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
            <p className="text-gray-600 text-sm">
              Fetch tin tức mới nhất từ CoinTelegraph RSS. Chỉ lấy Title, Overview và Ngày đăng (không scrape URL).
            </p>
            {totalArticles > 0 && (
              <p className="text-gray-600 mt-2">
                Đã lưu <span className="font-bold text-red-600">{totalArticles}</span> bài viết
              </p>
            )}
          </div>

          {/* Date Selection & Extract Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-red-500" />
              Trích xuất từ vựng theo ngày
            </h2>
            
            <p className="text-sm text-gray-600 mb-4">
              Chọn ngày để trích xuất từ vựng từ TẤT CẢ bài viết trong ngày đó (gom title + overview thành 1 nhóm)
            </p>

            {/* Date Selector */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chọn ngày phát hành:
              </label>
              <select
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="">-- Chọn ngày --</option>
                {availableDates.map((date) => (
                  <option key={date} value={date}>
                    {new Date(date).toLocaleDateString('vi-VN', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </option>
                ))}
              </select>
            </div>

            {/* Extract Button */}
            <button
              onClick={handleExtractByDate}
              disabled={!selectedDate || isExtracting}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Đang trích xuất từ vựng...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5" />
                  Trích xuất từ vựng nhóm ngày này
                </>
              )}
            </button>

            <p className="text-sm text-gray-500 mt-2 text-center">
              Hệ thống sẽ gom tất cả title + overview trong ngày → Gửi 1 lần cho Gemini AI
            </p>
          </div>

          {/* Vocabulary Output Section */}
          {vocabularyOutput && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">📝 Kết quả từ vựng</h2>
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
            <h2 className="text-xl font-bold text-gray-900 mb-4">🗂️ Quản lý kho từ vựng</h2>
            <div className="flex items-center justify-between mb-4">
              <div className="text-gray-600">
                Tổng số từ vựng đã lưu: <span className="font-bold text-red-600">{totalVocabulary}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleViewAllVocabulary}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Eye className="h-4 w-4" />
                  Xem tất cả
                </button>
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
                  {isResetting ? 'Đang reset...' : 'Reset'}
                </button>
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Kho từ vựng được lưu trữ đơn giản như file txt. Không có duplicate (case-insensitive).
            </p>
          </div>

        </div>
      </div>

      {/* View All Vocabulary Modal */}
      {showVocabModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-2xl font-bold text-gray-900">
                📚 Kho từ vựng Web3 ({allVocabulary.length} từ)
              </h2>
              <button
                onClick={() => setShowVocabModal(false)}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="p-4 border-b">
              <input
                type="text"
                placeholder="Tìm kiếm từ vựng hoặc định nghĩa..."
                value={vocabSearchTerm}
                onChange={(e) => setVocabSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Vocabulary List */}
            <div className="flex-1 overflow-y-auto p-6">
              {filteredVocabulary.length === 0 ? (
                <p className="text-center text-gray-500 py-8">Không tìm thấy từ vựng nào</p>
              ) : (
                <div className="space-y-3">
                  {filteredVocabulary.map((item, index) => (
                    <div
                      key={index}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-lg font-bold text-gray-900">
                            {item.original_word}
                          </p>
                          <p className="text-gray-700 mt-1">
                            {item.vietnamese_definition}
                          </p>
                          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                            <span>📰 {item.source_article_title}</span>
                            <span>•</span>
                            <span>{new Date(item.created_at).toLocaleDateString('vi-VN')}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t flex justify-end">
              <button
                onClick={() => setShowVocabModal(false)}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsDistributor;
