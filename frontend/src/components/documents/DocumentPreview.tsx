'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Download,
  Edit,
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface GeneratedDocument {
  content: string;
  document_type: string;
  template_used: string;
  cited_articles: string[];
  variables_used: Record<string, any>;
  disclaimer: string;
  format: string;
  warnings: string[];
  processing_time_ms: number;
  download_links: {
    markdown: string;
    docx: string;
    pdf: string | null;
  };
}

interface DocumentPreviewProps {
  document: GeneratedDocument;
  onEdit: () => void;
  onNewDocument: () => void;
}

export default function DocumentPreview({
  document,
  onEdit,
  onNewDocument,
}: DocumentPreviewProps) {
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (format: 'markdown' | 'docx' | 'pdf') => {
    try {
      setDownloading(format);

      const link = document.download_links[format];
      if (!link) {
        alert(`${format} ფორმატი მიუწვდომელია`);
        return;
      }

      // Create download link
      const a = window.document.createElement('a');
      a.href = link;
      a.download = `document-${document.document_type}-${Date.now()}.${format === 'markdown' ? 'md' : format}`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
    } catch (err) {
      console.error('Download error:', err);
      alert('ჩამოტვირთვა ვერ მოხერხდა');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Success Message */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="flex items-start gap-3 p-6">
          <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-green-900 mb-1">
              დოკუმენტი წარმატებით შეიქმნა!
            </h3>
            <p className="text-sm text-green-800">
              დოკუმენტი გენერირდა {document.processing_time_ms} მილიწამში
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Warnings */}
      {document.warnings && document.warnings.length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-semibold mb-2">გაფრთხილებები:</div>
            <ul className="list-disc list-inside space-y-1">
              {document.warnings.map((warning, index) => (
                <li key={index} className="text-sm">
                  {warning}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            ჩამოტვირთვა
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <Button
              variant="outline"
              onClick={() => handleDownload('markdown')}
              disabled={!!downloading}
            >
              {downloading === 'markdown' ? 'იტვირთება...' : 'Markdown (.md)'}
            </Button>
            <Button
              variant="outline"
              onClick={() => handleDownload('docx')}
              disabled={!!downloading}
            >
              {downloading === 'docx' ? 'იტვირთება...' : 'Word (.docx)'}
            </Button>
            {document.download_links.pdf && (
              <Button
                variant="outline"
                onClick={() => handleDownload('pdf')}
                disabled={!!downloading}
              >
                {downloading === 'pdf' ? 'იტვირთება...' : 'PDF (.pdf)'}
              </Button>
            )}
          </div>

          <div className="flex gap-3 pt-2 border-t">
            <Button variant="ghost" onClick={onEdit}>
              <Edit className="mr-2 h-4 w-4" />
              რედაქტირება
            </Button>
            <Button variant="ghost" onClick={onNewDocument}>
              <FileText className="mr-2 h-4 w-4" />
              ახალი დოკუმენტი
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document Preview */}
      <Card>
        <CardHeader>
          <CardTitle>დოკუმენტის გადახედვა</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <div className="bg-white border rounded-lg p-6 shadow-sm">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold mb-4 text-gray-900">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold mb-3 mt-6 text-gray-900">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold mb-2 mt-4 text-gray-900">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-4 text-gray-700 leading-relaxed">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside mb-4 space-y-2">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside mb-4 space-y-2">
                      {children}
                    </ol>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-gray-900">
                      {children}
                    </strong>
                  ),
                  hr: () => <hr className="my-6 border-gray-300" />,
                }}
              >
                {document.content}
              </ReactMarkdown>
            </div>
          </div>

          {/* Disclaimer - Prominent Display */}
          <Alert className="mt-6 border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-900">
              <div className="font-semibold mb-2">⚠️ გაფრთხილება:</div>
              <div className="text-sm whitespace-pre-line">
                {document.disclaimer}
              </div>
            </AlertDescription>
          </Alert>

          {/* Metadata */}
          {document.cited_articles && document.cited_articles.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-sm text-blue-900 mb-2">
                დაკავშირებული მუხლები:
              </h4>
              <div className="flex flex-wrap gap-2">
                {document.cited_articles.map((article) => (
                  <span
                    key={article}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded"
                  >
                    მუხლი {article}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
