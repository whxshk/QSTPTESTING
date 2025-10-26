import { useState, useRef, useEffect } from 'react';
import { FileText, CheckCircle, AlertTriangle, XCircle, ChevronDown } from 'lucide-react';
import { Document, DocumentAnnotation } from '../api';

interface DocumentAnnotationViewerProps {
  documents: Document[];
}

const DocumentAnnotationViewer = ({ documents }: DocumentAnnotationViewerProps) => {
  const [selectedDocIndex, setSelectedDocIndex] = useState(0);
  const [selectedAnnotation, setSelectedAnnotation] = useState<DocumentAnnotation | null>(null);
  const [highlightedRange, setHighlightedRange] = useState<{start: number, end: number} | null>(null);
  const documentTextRef = useRef<HTMLDivElement>(null);

  const currentDoc = documents[selectedDocIndex];

  useEffect(() => {
    // Reset selection when document changes
    setSelectedAnnotation(null);
    setHighlightedRange(null);
  }, [selectedDocIndex]);

  const handleAnnotationClick = (annotation: DocumentAnnotation) => {
    setSelectedAnnotation(annotation);

    if (annotation.start_index !== null && annotation.end_index !== null) {
      setHighlightedRange({
        start: annotation.start_index,
        end: annotation.end_index
      });

      // Scroll to the highlighted text
      if (documentTextRef.current) {
        const element = documentTextRef.current.querySelector(`[data-index="${annotation.start_index}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  };

  const getAnnotationIcon = (annotation: DocumentAnnotation) => {
    if (annotation.type === 'strength') {
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    } else {
      switch (annotation.severity) {
        case 'high':
          return <XCircle className="w-5 h-5 text-red-600" />;
        case 'medium':
          return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
        case 'low':
          return <AlertTriangle className="w-5 h-5 text-blue-600" />;
        default:
          return <AlertTriangle className="w-5 h-5 text-gray-600" />;
      }
    }
  };

  const getAnnotationBadgeClass = (annotation: DocumentAnnotation) => {
    if (annotation.type === 'strength') {
      switch (annotation.quality) {
        case 'excellent':
          return 'bg-green-100 text-green-800 border-green-300';
        case 'good':
          return 'bg-green-50 text-green-700 border-green-200';
        case 'adequate':
          return 'bg-green-50 text-green-600 border-green-100';
        default:
          return 'bg-green-100 text-green-800 border-green-300';
      }
    } else {
      switch (annotation.severity) {
        case 'high':
          return 'bg-red-100 text-red-800 border-red-300';
        case 'medium':
          return 'bg-yellow-100 text-yellow-800 border-yellow-300';
        case 'low':
          return 'bg-blue-100 text-blue-800 border-blue-300';
        default:
          return 'bg-gray-100 text-gray-800 border-gray-300';
      }
    }
  };

  const renderDocumentText = () => {
    if (!currentDoc) return null;

    const text = currentDoc.full_text;
    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    // Sort annotations by start_index to process them in order
    const sortedAnnotations = [...currentDoc.annotations]
      .filter(a => a.start_index !== null && a.end_index !== null)
      .sort((a, b) => (a.start_index || 0) - (b.start_index || 0));

    sortedAnnotations.forEach((annotation, idx) => {
      const start = annotation.start_index!;
      const end = annotation.end_index!;

      // Add non-highlighted text before this annotation
      if (lastIndex < start) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {text.substring(lastIndex, start)}
          </span>
        );
      }

      // Determine if this annotation is selected
      const isSelected = selectedAnnotation === annotation;
      const isHighlighted = highlightedRange &&
        highlightedRange.start === start &&
        highlightedRange.end === end;

      // Add highlighted text
      const highlightClass = annotation.type === 'strength'
        ? isHighlighted ? 'bg-green-300 border-2 border-green-600' : 'bg-green-100'
        : annotation.severity === 'high'
          ? isHighlighted ? 'bg-red-300 border-2 border-red-600' : 'bg-red-100'
          : annotation.severity === 'medium'
            ? isHighlighted ? 'bg-yellow-300 border-2 border-yellow-600' : 'bg-yellow-100'
            : isHighlighted ? 'bg-blue-300 border-2 border-blue-600' : 'bg-blue-100';

      parts.push(
        <mark
          key={`highlight-${idx}`}
          data-index={start}
          className={`${highlightClass} cursor-pointer transition-all duration-200 rounded px-1`}
          onClick={() => handleAnnotationClick(annotation)}
          title={annotation.title}
        >
          {text.substring(start, end)}
        </mark>
      );

      lastIndex = end;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {text.substring(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  if (!documents || documents.length === 0) {
    return null;
  }

  return (
    <div className="card mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <FileText className="w-6 h-6 text-primary-600" />
          <h3 className="text-2xl font-bold text-gray-900">Document Annotations</h3>
        </div>

        {/* Document Selector */}
        {documents.length > 1 && (
          <div className="relative">
            <select
              value={selectedDocIndex}
              onChange={(e) => setSelectedDocIndex(Number(e.target.value))}
              className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm font-medium text-gray-700 hover:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
            >
              {documents.map((doc, index) => (
                <option key={index} value={index}>
                  {doc.filename} ({doc.annotations.length} annotations)
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-gray-500 absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none" />
          </div>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Click on an annotation to highlight the relevant section in your document, or click on highlighted text to see details.
      </p>

      {/* Split View */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Document Text (Left) */}
        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 max-h-[600px] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">
              {currentDoc.filename}
            </h4>
            <span className="text-xs text-gray-500">
              {currentDoc.full_text.length} characters
            </span>
          </div>

          <div
            ref={documentTextRef}
            className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed"
          >
            {renderDocumentText()}
          </div>
        </div>

        {/* Annotations Panel (Right) */}
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          <h4 className="font-semibold text-gray-900 sticky top-0 bg-white pb-2">
            {currentDoc.annotations.length} Annotation{currentDoc.annotations.length !== 1 ? 's' : ''}
          </h4>

          {currentDoc.annotations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>No annotations for this document</p>
            </div>
          ) : (
            currentDoc.annotations.map((annotation, index) => (
              <button
                key={index}
                onClick={() => handleAnnotationClick(annotation)}
                className={`w-full text-left border rounded-lg p-4 transition-all duration-200 hover:shadow-md ${
                  selectedAnnotation === annotation
                    ? 'border-primary-500 bg-primary-50 shadow-md'
                    : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start space-x-2 flex-1">
                    {getAnnotationIcon(annotation)}
                    <div className="flex-1">
                      <h5 className="font-semibold text-gray-900 text-sm">
                        {annotation.title}
                      </h5>
                      <p className="text-xs text-gray-500 mt-1">
                        {annotation.rule_ref}
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold border ${getAnnotationBadgeClass(annotation)}`}>
                    {annotation.type === 'strength'
                      ? annotation.quality?.toUpperCase()
                      : annotation.severity?.toUpperCase()
                    }
                  </span>
                </div>

                <p className="text-xs text-gray-700 mt-2 leading-relaxed">
                  {annotation.explanation}
                </p>

                {annotation.text_snippet && (
                  <div className="mt-3 p-2 bg-gray-100 rounded text-xs text-gray-600 italic border-l-2 border-gray-400">
                    "{annotation.text_snippet}"
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h5 className="text-sm font-semibold text-gray-700 mb-3">Highlight Legend:</h5>
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
            <span className="text-gray-600">Strength</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-100 border border-red-300 rounded"></div>
            <span className="text-gray-600">High Severity Gap</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded"></div>
            <span className="text-gray-600">Medium Severity Gap</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-300 rounded"></div>
            <span className="text-gray-600">Low Severity Gap</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentAnnotationViewer;
