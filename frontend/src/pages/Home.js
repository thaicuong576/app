import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Newspaper, Users, Globe, Rss, ArrowRight } from 'lucide-react';

const Home = () => {

  const features = [
    {
      id: 'partner-content-hub',
      title: 'Partner Content Hub',
      description: 'Dịch và tái cấu trúc nội dung crypto chuyên nghiệp',
      icon: FileText,
      path: '/partner-content-hub',
      gradient: 'from-orange-500 to-amber-600'
    },
    {
      id: 'news-generator',
      title: 'News Generator',
      description: 'Tạo tin tức tự động từ nhiều nguồn',
      icon: Newspaper,
      path: '/news-generator',
      gradient: 'from-blue-500 to-cyan-600'
    },
    {
      id: 'kol-post',
      title: 'KOL Post',
      description: 'Quản lý và tạo bài đăng cho KOL',
      icon: Users,
      path: '/kol-post',
      gradient: 'from-purple-500 to-pink-600'
    },
    {
      id: 'social-to-website',
      title: 'Social-to-Website Post',
      description: 'Chuyển đổi nội dung social thành bài viết website',
      icon: Globe,
      path: '/social-to-website',
      gradient: 'from-green-500 to-emerald-600'
    },
    {
      id: 'news-distributor',
      title: 'News Distributor',
      description: 'Thu thập từ vựng Web3 từ tin tức CoinDesk',
      icon: Rss,
      path: '/news-distributor',
      gradient: 'from-red-500 to-orange-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      {/* Header */}
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-16 pt-12">
          <h1 className="text-6xl font-bold text-white mb-4" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            GFI Studio - Eddie
          </h1>
          <p className="text-xl text-white/80">Content Creation & Management Platform</p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link
                key={feature.id}
                to={feature.path}
                className="group cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl border-0 overflow-hidden bg-white rounded-lg relative block no-underline"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300 pointer-events-none`} />
                <div className="p-8 relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-4 rounded-2xl bg-gradient-to-br ${feature.gradient} shadow-lg`}>
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    <ArrowRight className="h-6 w-6 text-gray-400 group-hover:text-[#E38400] group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-[#E38400] transition-colors duration-300">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Footer */}
        <div className="text-center mt-16 pb-8">
          <p className="text-white/60 text-sm">Powered by AI • Built for Content Creators</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
