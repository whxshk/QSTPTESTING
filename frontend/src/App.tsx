import { useState } from 'react';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import SummaryPage from './pages/SummaryPage';
import ResultsPage from './pages/ResultsPage';
import { AnalysisResult, getDemoAnalysis } from './api';

type Page = 'landing' | 'upload' | 'summary' | 'results';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [uploadComplete, setUploadComplete] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const handleStartAnalysis = () => {
    setCurrentPage('upload');
  };

  const handleViewDemo = async () => {
    try {
      const demoResult = await getDemoAnalysis();
      setAnalysisResult(demoResult);
      setCurrentPage('results');
    } catch (error) {
      console.error('Failed to load demo:', error);
      alert('Failed to load demo. Please try again.');
    }
  };

  const handleUploadComplete = () => {
    setUploadComplete(true);
    setCurrentPage('summary');
  };

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setCurrentPage('results');
  };

  const handleReset = () => {
    setCurrentPage('landing');
    setUploadComplete(false);
    setAnalysisResult(null);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onStart={handleStartAnalysis} onViewDemo={handleViewDemo} />;
      case 'upload':
        return <UploadPage onUploadComplete={handleUploadComplete} onBack={() => setCurrentPage('landing')} />;
      case 'summary':
        return <SummaryPage onAnalysisComplete={handleAnalysisComplete} onBack={() => setCurrentPage('upload')} />;
      case 'results':
        return <ResultsPage result={analysisResult} onReset={handleReset} />;
      default:
        return <LandingPage onStart={handleStartAnalysis} onViewDemo={handleViewDemo} />;
    }
  };

  return (
    <div className="min-h-screen">
      {renderPage()}
    </div>
  );
}

export default App;
