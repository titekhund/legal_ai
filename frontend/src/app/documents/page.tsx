'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Briefcase, FileCheck, Users, ScrollText, DollarSign, AlertCircle } from 'lucide-react';

interface DocumentType {
  id: string;
  name_ka: string;
  name_en: string;
  description_ka: string;
  description_en?: string;
  required_fields: string[];
  optional_fields: string[];
}

// Icon mapping for document types
const documentIcons: Record<string, any> = {
  nda: FileCheck,
  employment_contract: Briefcase,
  board_resolution: Users,
  shareholder_agreement: ScrollText,
  service_agreement: FileText,
  loan_agreement: DollarSign,
};

export default function DocumentsPage() {
  const router = useRouter();
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocumentTypes();
  }, []);

  const loadDocumentTypes = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/documents/types');

      if (!response.ok) {
        throw new Error('Failed to load document types');
      }

      const data = await response.json();
      setDocumentTypes(data.types || []);
    } catch (err) {
      console.error('Error loading document types:', err);
      setError('დოკუმენტის ტიპების ჩატვირთვა ვერ მოხერხდა');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDocumentType = (typeId: string) => {
    router.push(`/documents/generate?type=${typeId}`);
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

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center gap-3 p-6">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          დოკუმენტების გენერირება
        </h1>
        <p className="text-gray-600">
          აირჩიეთ დოკუმენტის ტიპი და შექმენით პროფესიონალური იურიდიული დოკუმენტი
        </p>
      </div>

      {/* Document Type Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {documentTypes.map((docType) => {
          const Icon = documentIcons[docType.id] || FileText;

          return (
            <Card
              key={docType.id}
              className="hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-blue-500"
              onClick={() => handleSelectDocumentType(docType.id)}
            >
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">{docType.name_ka}</CardTitle>
                </div>
                <CardDescription className="text-sm text-gray-600">
                  {docType.description_ka}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">
                      სავალდებულო ველები:
                    </span>
                    <span className="ml-2 text-gray-600">
                      {docType.required_fields.length}
                    </span>
                  </div>
                  {docType.optional_fields.length > 0 && (
                    <div>
                      <span className="font-medium text-gray-700">
                        არასავალდებულო ველები:
                      </span>
                      <span className="ml-2 text-gray-600">
                        {docType.optional_fields.length}
                      </span>
                    </div>
                  )}
                </div>
                <Button className="w-full mt-4" variant="outline">
                  შექმნა
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {documentTypes.length === 0 && !loading && !error && (
        <Card className="border-gray-200">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              დოკუმენტების შაბლონები არ მოიძებნა
            </h3>
            <p className="text-gray-600 max-w-md">
              ამჟამად დოკუმენტების შაბლონები მიუწვდომელია. გთხოვთ დაგვიკავშირდეთ ადმინისტრატორთან.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
