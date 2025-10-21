import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Home, RefreshCw, ExternalLink, Trash2, Newspaper, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const CryptoNewsFeed = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);

  const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

  // Load cached news on mount
  useEffect(() => {
    loadCachedNews();
  }, []);

  const loadCachedNews = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/crypto-news`);
      if (response.ok) {
        const data = await response.json();
        setNews(data);
      }
    } catch (error) {
      console.error('Error loading cached news:', error);
    } finally {
      setLoading(false);
    }
  };

  const crawlFreshNews = async () => {
    setCrawling(true);
    toast.info('🔍 Đang crawl tin tức mới từ CryptoPanic...');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/crypto-news/crawl`);
      if (response.ok) {
        const data = await response.json();
        setNews(data.news || []);
        toast.success(`🎉 Đã crawl thành công ${data.news?.length || 0} tin tức!`);
      } else {
        toast.error('Không thể crawl tin tức. Vui lòng thử lại.');
      }
    } catch (error) {
      console.error('Error crawling news:', error);
      toast.error('Lỗi khi crawl tin tức');
    } finally {
      setCrawling(false);
    }
  };

  const deleteNews = async (newsId) => {
    if (!window.confirm('Bạn có chắc muốn xóa tin tức này?')) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/crypto-news/${newsId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setNews(news.filter(item => item.id !== newsId));
        toast.success('Đã xóa tin tức');
      } else {
        toast.error('Không thể xóa tin tức');
      }
    } catch (error) {
      console.error('Error deleting news:', error);
      toast.error('Lỗi khi xóa tin tức');
    }
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    return timeStr;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-sm border-b border-white/20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors duration-200"
              >
                <Home className="h-5 w-5" />
                <span className="font-medium">Home</span>
              </Link>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-rose-600">
                  <Newspaper className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-white">Crypto News Feed</h1>
              </div>
            </div>
            <button
              onClick={crawlFreshNews}
              disabled={crawling}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-5 w-5 ${crawling ? 'animate-spin' : ''}`} />
              <span className="font-medium">{crawling ? 'Đang Crawl...' : 'Crawl Fresh News'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-white text-lg">Đang tải tin tức...</div>
          </div>
        ) : news.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <TrendingUp className="h-16 w-16 text-white/40 mb-4" />
            <p className="text-white/60 text-lg mb-6">Chưa có tin tức. Nhấn "Crawl Fresh News" để lấy tin mới nhất!</p>
          </div>
        ) : (
          <div className="grid gap-4 max-w-6xl mx-auto">
            {news.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-200 border-l-4 border-red-500"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Title */}
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xl font-bold text-gray-900 hover:text-red-600 transition-colors duration-200 flex items-start gap-2 group mb-2"
                    >
                      <span className="flex-1">{item.title}</span>
                      <ExternalLink className="h-5 w-5 text-gray-400 group-hover:text-red-600 flex-shrink-0 mt-1" />
                    </a>

                    {/* Meta Info */}
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                      {item.source && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium text-red-600">📰</span>
                          <span className="font-medium">{item.source}</span>
                        </div>
                      )}
                      {item.published_time && (
                        <div className="flex items-center gap-1">
                          <span>🕐</span>
                          <span>{formatTime(item.published_time)}</span>
                        </div>
                      )}
                      {item.votes && (
                        <div className="flex items-center gap-1">
                          <span>👍</span>
                          <span className="font-medium text-green-600">{item.votes}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={() => deleteNews(item.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200"
                    title="Xóa tin tức"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Box */}
        {news.length > 0 && (
          <div className="max-w-6xl mx-auto mt-8 p-4 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
            <p className="text-white/80 text-sm text-center">
              📊 Hiển thị {news.length} tin tức từ CryptoPanic • Nhấn "Crawl Fresh News" để cập nhật
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CryptoNewsFeed;
