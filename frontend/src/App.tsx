import { useState } from 'react';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import SummaryPage from './pages/SummaryPage';
import ResultsPage from './pages/ResultsPage';
import { AnalysisResult } from './api';

type Page = 'landing' | 'upload' | 'summary' | 'results';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [uploadComplete, setUploadComplete] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const handleStartAnalysis = () => {
    setCurrentPage('upload');
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
        return <LandingPage onStart={handleStartAnalysis} />;
      case 'upload':
        return <UploadPage onUploadComplete={handleUploadComplete} onBack={() => setCurrentPage('landing')} />;
      case 'summary':
        return <SummaryPage onAnalysisComplete={handleAnalysisComplete} onBack={() => setCurrentPage('upload')} />;
      case 'results':
        return <ResultsPage result={analysisResult} onReset={handleReset} />;
      default:
        return <LandingPage onStart={handleStartAnalysis} />;
    }
  };

  return (
    <div className="min-h-screen">
      {renderPage()}
    </div>
  );
}

export default App;
