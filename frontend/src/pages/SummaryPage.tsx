import { useState } from 'react';
import { ArrowLeft, ArrowRight, AlertCircle, Loader } from 'lucide-react';
import { analyzeCompliance, AnalysisResult } from '../api';

interface SummaryPageProps {
  onAnalysisComplete: (result: AnalysisResult) => void;
  onBack: () => void;
}

const SummaryPage = ({ onAnalysisComplete, onBack }: SummaryPageProps) => {
  const [summary, setSummary] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const exampleSummary = `P2P lending platform connecting borrowers with investors. Business model charges 2% origination fee and 1% servicing fee. Paid-up capital: QAR 5,000,000. Data hosted on AWS infrastructure in Ireland and Singapore. Transaction volumes up to QAR 45,000 per transaction. Currently no dedicated Compliance Officer. AML policy drafted but not yet board-approved. Customer verification performed manually. Targeting retail customers in Qatar.`;

  const handleAnalyze = async () => {
    if (!summary.trim()) {
      setError('Please provide a startup summary');
      return;
    }

    if (summary.trim().length < 50) {
      setError('Please provide a more detailed summary (at least 50 characters)');
      return;
    }

    setAnalyzing(true);
    setError('');

    try {
      const result = await analyzeCompliance(summary);
      onAnalysisComplete(result);
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(
        err.response?.data?.error ||
        err.message ||
        'Analysis failed. Please ensure documents are uploaded and try again.'
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const useExample = () => {
    setSummary(exampleSummary);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <Loader className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Describe Your Startup</h1>
              <p className="text-sm text-gray-500">Step 2 of 2</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <button
          onClick={onBack}
          className="mb-6 flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload</span>
        </button>

        {/* Instructions */}
        <div className="card mb-8">
          <h2 className="text-2xl font-bold mb-4">Tell Us About Your Startup</h2>
          <p className="text-gray-600 mb-4">
            Provide a brief summary of your fintech startup, including:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600 mb-4">
            <li>Business model and revenue streams</li>
            <li>Paid-up capital amount</li>
            <li>Data hosting location (servers, cloud providers)</li>
            <li>Transaction volumes and limits</li>
            <li>Compliance officer status</li>
            <li>AML/CFT policy status</li>
            <li>Customer verification processes</li>
            <li>Target market and customer segments</li>
          </ul>
          <p className="text-sm text-gray-500">
            Be specific and honest - this information will be analyzed against QCB
            requirements to identify compliance gaps.
          </p>
        </div>

        {/* Summary Input */}
        <div className="card mb-6">
          <div className="flex justify-between items-center mb-4">
            <label htmlFor="summary" className="block text-lg font-semibold text-gray-900">
              Startup Summary
            </label>
            <button
              onClick={useExample}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Use Example
            </button>
          </div>
          <textarea
            id="summary"
            value={summary}
            onChange={(e) => {
              setSummary(e.target.value);
              setError('');
            }}
            rows={12}
            className="textarea"
            placeholder="e.g., P2P lending platform connecting borrowers with investors. Business model charges 2% origination fee and 1% servicing fee. Paid-up capital: QAR 5,000,000. Data hosted on AWS infrastructure in Ireland and Singapore..."
          />
          <div className="mt-2 flex justify-between items-center">
            <p className="text-sm text-gray-500">
              {summary.length} characters
            </p>
            <p className="text-sm text-gray-500">
              Minimum 50 characters recommended
            </p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="card bg-blue-50 border border-blue-200 mb-8">
          <h3 className="font-semibold text-blue-900 mb-2">What Happens Next?</h3>
          <p className="text-sm text-blue-800">
            Our AI will analyze your uploaded documents and this summary against QCB
            regulatory requirements. This typically takes 10-30 seconds. You'll receive:
          </p>
          <ul className="mt-2 space-y-1 text-sm text-blue-800 list-disc list-inside">
            <li>Regulatory readiness score (0-100)</li>
            <li>Detailed list of compliance gaps</li>
            <li>Severity assessment for each gap</li>
            <li>Recommended QDB programs and experts</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between">
          <button onClick={onBack} className="btn-secondary" disabled={analyzing}>
            Back
          </button>

          <button
            onClick={handleAnalyze}
            disabled={analyzing || !summary.trim()}
            className="btn-primary inline-flex items-center space-x-2"
          >
            {analyzing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Analyzing Compliance...</span>
              </>
            ) : (
              <>
                <span>Analyze Compliance</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Loading State Info */}
        {analyzing && (
          <div className="mt-6 card bg-yellow-50 border border-yellow-200">
            <div className="flex items-start space-x-3">
              <Loader className="w-5 h-5 text-yellow-600 animate-spin flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-yellow-900">
                  AI Analysis in Progress
                </p>
                <p className="text-sm text-yellow-800 mt-1">
                  Please wait while we retrieve relevant document excerpts, compare them
                  against QCB regulations, and generate your compliance report. This may
                  take up to 30 seconds.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryPage;
