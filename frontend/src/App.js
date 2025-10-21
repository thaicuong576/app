import React from 'react';
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Home from '@/pages/Home';
import PartnerContentHub from '@/pages/PartnerContentHub';
import NewsGenerator from '@/pages/NewsGenerator';
import KOLPost from '@/pages/KOLPost';
import SocialToWebsite from '@/pages/SocialToWebsite';
import CryptoNewsFeed from '@/pages/CryptoNewsFeed';

function App() {
  return (
    <>
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/partner-content-hub/*" element={<PartnerContentHub />} />
          <Route path="/news-generator" element={<NewsGenerator />} />
          <Route path="/kol-post" element={<KOLPost />} />
          <Route path="/social-to-website" element={<SocialToWebsite />} />
          <Route path="/crypto-news-feed" element={<CryptoNewsFeed />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
