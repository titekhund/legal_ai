'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import DocumentForm from '@/components/documents/DocumentForm';
import DocumentPreview from '@/components/documents/DocumentPreview';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DocumentTemplate {
  id: string;
  type: string;
  name_ka: string;
  name_en: string;
  language: string;
  content: string;
  variables: TemplateVariable[];
  related_articles: string[];
  category?: string;
  tags: string[];
}

interface TemplateVariable {
  name: string;
  label_ka: string;
  label_en: string;
  type: string;
  required: boolean;
  default?: string;
  choices?: string[];
  placeholder_ka?: string;
  placeholder_en?: string;
}

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

function DocumentGenerateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentType = searchParams.get('type');

  const [template, setTemplate] = useState<DocumentTemplate | null>(null);
  const [generatedDocument, setGeneratedDocument] = useState<GeneratedDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (documentType) {
      loadTemplate();
    }
  }, [documentType]);

  const loadTemplate = async () => {
    if (!documentType) return;

    try {
      setLoading(true);
      setError(null);

      // Get templates for this document type
      const response = await fetch(
        `/api/documents/templates?document_type=${documentType}&language=ka&limit=1`
      );

      if (!response.ok) {
        throw new Error('Failed to load template');
      }

      const data = await response.json();

      if (data.templates && data.templates.length > 0) {
        setTemplate(data.templates[0]);
      } else {
        setError('შაბლონი ვერ მოიძებნა ამ დოკუმენტის ტიპისთვის');
      }
    } catch (err) {
      console.error('Error loading template:', err);
      setError('შაბლონის ჩატვირთვა ვერ მოხერხდა');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = (document: GeneratedDocument) => {
    setGeneratedDocument(document);
  };

  const handleBack = () => {
    if (generatedDocument) {
      // If viewing generated document, go back to form
      setGeneratedDocument(null);
    } else {
      // Go back to document types list
      router.push('/documents');
    }
  };

  const handleNewDocument = () => {
    setGeneratedDocument(null);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">იტვირთება...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={() => router.push('/documents')}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          უკან
        </Button>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'დოკუმენტის შაბლონი ვერ მოიძებნა'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" onClick={handleBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          უკან
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {generatedDocument ? 'დოკუმენტის გადახედვა' : template.name_ka}
          </h1>
          {!generatedDocument && (
            <p className="text-sm text-gray-600 mt-1">
              შეავსეთ ველები დოკუმენტის გენერირებისთვის
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      {generatedDocument ? (
        <DocumentPreview
          document={generatedDocument}
          onEdit={handleNewDocument}
          onNewDocument={handleNewDocument}
        />
      ) : (
        <DocumentForm template={template} onGenerate={handleGenerate} />
      )}
    </div>
  );
}

export default function DocumentGeneratePage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">იტვირთება...</p>
            </div>
          </div>
        </div>
      }
    >
      <DocumentGenerateContent />
    </Suspense>
  );
}
