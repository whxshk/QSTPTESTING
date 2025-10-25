import { ArrowRight, CheckCircle, FileText, BarChart3, Users } from 'lucide-react';

interface LandingPageProps {
  onStart: () => void;
}

const LandingPage = ({ onStart }: LandingPageProps) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Fintech Regulatory Readiness</h1>
                <p className="text-sm text-gray-500">QCB Compliance Platform</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Check Your Fintech<br />
            <span className="text-primary-600">Regulatory Readiness</span><br />
            in Minutes
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Upload your business documents and get an AI-powered compliance analysis
            against Qatar Central Bank (QCB) regulatory requirements. Identify gaps,
            get a readiness score, and receive tailored recommendations.
          </p>
          <button
            onClick={onStart}
            className="btn-primary text-lg px-8 py-4 inline-flex items-center space-x-2 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all"
          >
            <span>Upload Documents & Start Analysis</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">
            How It Works
          </h3>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-primary-600" />
              </div>
              <h4 className="text-lg font-semibold mb-2">1. Upload Documents</h4>
              <p className="text-gray-600 text-sm">
                Upload your business plan, compliance policy, legal structure, and
                regulatory documents (DOCX/PDF)
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-primary-600" />
              </div>
              <h4 className="text-lg font-semibold mb-2">2. AI Analysis</h4>
              <p className="text-gray-600 text-sm">
                Our AI extracts, analyzes, and compares your documentation against
                QCB regulatory requirements
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-primary-600" />
              </div>
              <h4 className="text-lg font-semibold mb-2">3. Get Your Score</h4>
              <p className="text-gray-600 text-sm">
                Receive a readiness score (0-100) with detailed breakdown of
                compliance gaps by severity
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-primary-600" />
              </div>
              <h4 className="text-lg font-semibold mb-2">4. Take Action</h4>
              <p className="text-gray-600 text-sm">
                Get matched with QDB programs and compliance experts to close
                your regulatory gaps
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why It Matters */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-primary-600 rounded-2xl p-12 text-white">
            <h3 className="text-3xl font-bold mb-6">Why Regulatory Readiness Matters</h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <h4 className="text-xl font-semibold mb-3">Faster Licensing</h4>
                <p className="text-primary-100">
                  Identify and fix compliance gaps early to accelerate your QCB
                  licensing application process
                </p>
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-3">Reduce Risk</h4>
                <p className="text-primary-100">
                  Avoid costly delays, rejections, and penalties by ensuring full
                  compliance before submission
                </p>
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-3">Expert Guidance</h4>
                <p className="text-primary-100">
                  Get connected to QDB programs and compliance experts who can help
                  you navigate complex regulations
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section className="bg-white py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Frequently Asked Questions
          </h3>
          <div className="space-y-6">
            <div className="card">
              <h4 className="text-lg font-semibold mb-2">What documents should I upload?</h4>
              <p className="text-gray-600">
                Upload your business plan, compliance policies (especially AML/CFT),
                legal structure documents, and any regulatory circular information.
                We accept DOCX and PDF formats.
              </p>
            </div>

            <div className="card">
              <h4 className="text-lg font-semibold mb-2">How is the score calculated?</h4>
              <p className="text-gray-600">
                We start with a base score of 100 and deduct points based on compliance
                gaps: -35 for high severity, -20 for medium, and -10 for low severity gaps.
              </p>
            </div>

            <div className="card">
              <h4 className="text-lg font-semibold mb-2">Is my data secure?</h4>
              <p className="text-gray-600">
                Yes. All documents are processed in-memory and are not permanently stored.
                The analysis is performed locally using AI, and we don't share your data
                with third parties.
              </p>
            </div>

            <div className="card">
              <h4 className="text-lg font-semibold mb-2">What if I score low?</h4>
              <p className="text-gray-600">
                A low score simply means there are compliance gaps to address. We provide
                specific recommendations for QDB programs and experts who can help you
                improve your compliance status.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            &copy; 2024 Fintech Regulatory Readiness Platform. Built for Qatar's
            fintech ecosystem.
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Powered by AI. For informational purposes only. Consult with legal and
            compliance professionals for official guidance.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
