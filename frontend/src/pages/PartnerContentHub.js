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
import { Loader2, FileText, Link as LinkIcon, Sparkles, Share2, Copy, ArrowLeft, Home as HomeIcon } from "lucide-react";

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-12 max-w-7xl">
        <div className="flex justify-between items-center mb-12">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Button
                variant="ghost"
                onClick={() => navigate('/')}
                className="hover:bg-slate-200 rounded-full"
              >
                <HomeIcon className="h-5 w-5" />
              </Button>
              <h1 className="text-5xl font-bold text-slate-900" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                Partner Content Hub
              </h1>
            </div>
            <p className="text-lg text-slate-600 ml-14">Manage and automate your content workflow</p>
          </div>
          <Button
            data-testid="create-project-btn"
            onClick={() => navigate('/partner-content-hub/create')}
            size="lg"
            className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-8 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            <Sparkles className="mr-2 h-5 w-5" />
            Create New Project
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
          </div>
        ) : projects.length === 0 ? (
          <Card className="text-center py-16 bg-white/60 backdrop-blur-sm border-slate-200 shadow-xl">
            <CardContent>
              <FileText className="h-24 w-24 mx-auto mb-6 text-slate-300" />
              <h3 className="text-2xl font-semibold text-slate-700 mb-3">No projects yet</h3>
              <p className="text-slate-500 mb-6">Create your first project to get started</p>
              <Button
                onClick={() => navigate('/partner-content-hub/create')}
                className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-6"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Create Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card
                key={project.id}
                data-testid={`project-card-${project.id}`}
                className="cursor-pointer hover:shadow-2xl transition-all duration-300 bg-white/80 backdrop-blur-sm border-slate-200 hover:scale-105 transform"
                onClick={() => navigate(`/partner-content-hub/workshop/${project.id}`)}
              >
                <CardHeader>
                  <CardTitle className="text-xl font-bold text-slate-900 line-clamp-2">
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
                  <div className="space-y-2">
                    {project.translated_content && (
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

// Rest of the file content continues with CreateProject and Workshop components...
// I'll need to copy the rest from the original App.js

export default function PartnerContentHub() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/create" element={<CreateProject />} />
      <Route path="/workshop/:id" element={<Workshop />} />
    </Routes>
  );
}

// CreateProject Component
function CreateProject() {
  // Will continue with rest of components in next file
}

function Workshop() {
  // Will continue with rest of components in next file
}
