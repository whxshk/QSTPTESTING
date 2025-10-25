import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';
import { uploadDocuments } from '../api';

interface UploadPageProps {
  onUploadComplete: () => void;
  onBack: () => void;
}

const UploadPage = ({ onUploadComplete, onBack }: UploadPageProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadResult, setUploadResult] = useState<any>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
    setUploadStatus('idle');
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setErrorMessage('Please select at least one file');
      setUploadStatus('error');
      return;
    }

    setUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');

    try {
      const result = await uploadDocuments(files);
      setUploadResult(result);
      setUploadStatus('success');
    } catch (error: any) {
      console.error('Upload error:', error);
      setErrorMessage(
        error.response?.data?.error || error.message || 'Upload failed. Please try again.'
      );
      setUploadStatus('error');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Upload Documents</h1>
              <p className="text-sm text-gray-500">Step 1 of 2</p>
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
          <span>Back to Home</span>
        </button>

        {/* Instructions */}
        <div className="card mb-8">
          <h2 className="text-2xl font-bold mb-4">Upload Your Documents</h2>
          <p className="text-gray-600 mb-4">
            Upload your <strong>Business Plan, Legal Structure, Compliance Policies, and Regulatory References</strong> in DOCX or PDF format:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600">
            <li><strong>Business Plan</strong> - Your company overview, business model, and operations</li>
            <li><strong>Legal Structure Document</strong> - Corporate registration, shareholder agreements, governance</li>
            <li><strong>Compliance Policies</strong> - AML/CFT policy, data protection, customer verification procedures</li>
            <li><strong>Regulatory References</strong> - Any QCB circulars, licensing requirements, or regulatory documentation</li>
          </ul>
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Privacy Note:</strong> All documents are processed in-memory and not stored permanently.
              Your data remains confidential and secure. We support any fintech startup or financial services company.
            </p>
          </div>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 bg-white hover:border-primary-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          {isDragActive ? (
            <p className="text-lg text-primary-600 font-semibold">Drop files here...</p>
          ) : (
            <>
              <p className="text-lg text-gray-700 mb-2">
                Drag & drop files here, or click to select
              </p>
              <p className="text-sm text-gray-500">
                Accepts DOCX and PDF files (max 50MB per file)
              </p>
            </>
          )}
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-8 card">
            <h3 className="text-lg font-semibold mb-4">
              Selected Files ({files.length})
            </h3>
            <div className="space-y-3">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <FileText className="w-5 h-5 text-primary-600" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="ml-4 text-gray-400 hover:text-red-600 transition-colors"
                    disabled={uploading}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Status Messages */}
        {uploadStatus === 'success' && uploadResult && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-green-900">Upload Successful!</p>
              <p className="text-sm text-green-700 mt-1">
                Processed {uploadResult.files_processed} files with{' '}
                {uploadResult.chunks_indexed} text chunks indexed.
              </p>
            </div>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Upload Failed</p>
              <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex justify-between">
          <button onClick={onBack} className="btn-secondary">
            Cancel
          </button>

          {uploadStatus === 'success' ? (
            <button
              onClick={onUploadComplete}
              className="btn-primary inline-flex items-center space-x-2"
            >
              <span>Continue to Summary</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleUpload}
              disabled={files.length === 0 || uploading}
              className="btn-primary inline-flex items-center space-x-2"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Process</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
