import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Home as HomeIcon, Newspaper, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const NewsGenerator = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#004154] via-[#005568] to-[#003844]">
      <div className="container mx-auto px-4 py-12 max-w-7xl">
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
            <p className="text-lg text-white/80 ml-14">Tạo tin tức tự động từ nhiều nguồn</p>
          </div>
        </div>

        <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-2xl">
          <CardHeader className="text-center pb-8">
            <div className="mx-auto mb-6 p-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 w-24 h-24 flex items-center justify-center">
              <Newspaper className="h-12 w-12 text-white" />
            </div>
            <CardTitle className="text-3xl font-bold text-gray-900 mb-3">
              Tính năng đang được phát triển
            </CardTitle>
            <CardDescription className="text-lg text-gray-600">
              News Generator sẽ sớm có mặt với các tính năng mạnh mẽ
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-6 rounded-xl">
              <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Sparkles className="h-5 w-5 mr-2 text-[#E38400]" />
                Các tính năng sắp có:
              </h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-[#E38400] mr-2 mt-1">•</span>
                  <span>Tự động thu thập tin tức từ nhiều nguồn khác nhau</span>
                </li>
                <li className="flex items-start">
                  <span className="text-[#E38400] mr-2 mt-1">•</span>
                  <span>AI tổng hợp và viết lại nội dung độc đáo</span>
                </li>
                <li className="flex items-start">
                  <span className="text-[#E38400] mr-2 mt-1">•</span>
                  <span>Tùy chỉnh phong cách viết và tone giọng</span>
                </li>
                <li className="flex items-start">
                  <span className="text-[#E38400] mr-2 mt-1">•</span>
                  <span>Xuất bản tự động lên website</span>
                </li>
              </ul>
            </div>

            <div className="text-center pt-4">
              <Button
                onClick={() => navigate('/')}
                className="bg-[#E38400] hover:bg-[#c77200] text-white px-8 py-6 text-lg rounded-full shadow-lg hover:shadow-xl transition-all"
              >
                <ArrowLeft className="mr-2 h-5 w-5" />
                Quay về Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NewsGenerator;
