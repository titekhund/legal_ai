'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, FileText, Loader2 } from 'lucide-react';

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

interface DocumentTemplate {
  id: string;
  type: string;
  name_ka: string;
  variables: TemplateVariable[];
}

interface DocumentFormProps {
  template: DocumentTemplate;
  onGenerate: (document: any) => void;
}

export default function DocumentForm({ template, onGenerate }: DocumentFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    // Initialize with default values
    const initial: Record<string, any> = {};
    template.variables.forEach((variable) => {
      if (variable.default) {
        initial[variable.name] = variable.default;
      }
    });
    return initial;
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (name: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    template.variables.forEach((variable) => {
      if (variable.required && !formData[variable.name]) {
        newErrors[variable.name] = 'ეს ველი სავალდებულოა';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      setError('გთხოვთ შეავსოთ ყველა სავალდებულო ველი');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/documents/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_type: template.type,
          template_id: template.id,
          variables: formData,
          language: 'ka',
          include_legal_references: true,
          format: 'markdown',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'დოკუმენტის გენერირება ვერ მოხერხდა');
      }

      const data = await response.json();
      onGenerate(data);
    } catch (err: any) {
      console.error('Error generating document:', err);
      setError(err.message || 'დოკუმენტის გენერირება ვერ მოხერხდა');
    } finally {
      setLoading(false);
    }
  };

  const renderField = (variable: TemplateVariable) => {
    const fieldId = `field-${variable.name}`;
    const hasError = !!errors[variable.name];

    switch (variable.type) {
      case 'text':
        return (
          <div key={variable.name} className="space-y-2">
            <Label htmlFor={fieldId}>
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={fieldId}
              type="text"
              value={formData[variable.name] || ''}
              onChange={(e) => handleChange(variable.name, e.target.value)}
              placeholder={variable.placeholder_ka || ''}
              className={hasError ? 'border-red-500' : ''}
              disabled={loading}
            />
            {hasError && (
              <p className="text-sm text-red-500">{errors[variable.name]}</p>
            )}
          </div>
        );

      case 'date':
        return (
          <div key={variable.name} className="space-y-2">
            <Label htmlFor={fieldId}>
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={fieldId}
              type="date"
              value={formData[variable.name] || ''}
              onChange={(e) => handleChange(variable.name, e.target.value)}
              className={hasError ? 'border-red-500' : ''}
              disabled={loading}
            />
            {hasError && (
              <p className="text-sm text-red-500">{errors[variable.name]}</p>
            )}
          </div>
        );

      case 'number':
        return (
          <div key={variable.name} className="space-y-2">
            <Label htmlFor={fieldId}>
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={fieldId}
              type="number"
              value={formData[variable.name] || ''}
              onChange={(e) => handleChange(variable.name, e.target.value)}
              placeholder={variable.placeholder_ka || ''}
              className={hasError ? 'border-red-500' : ''}
              disabled={loading}
            />
            {hasError && (
              <p className="text-sm text-red-500">{errors[variable.name]}</p>
            )}
          </div>
        );

      case 'choice':
        return (
          <div key={variable.name} className="space-y-2">
            <Label htmlFor={fieldId}>
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Select
              value={formData[variable.name] || ''}
              onValueChange={(value) => handleChange(variable.name, value)}
              disabled={loading}
            >
              <SelectTrigger className={hasError ? 'border-red-500' : ''}>
                <SelectValue placeholder="აირჩიეთ..." />
              </SelectTrigger>
              <SelectContent>
                {variable.choices?.map((choice) => (
                  <SelectItem key={choice} value={choice}>
                    {choice}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasError && (
              <p className="text-sm text-red-500">{errors[variable.name]}</p>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div key={variable.name} className="flex items-center space-x-2">
            <input
              id={fieldId}
              type="checkbox"
              checked={formData[variable.name] || false}
              onChange={(e) => handleChange(variable.name, e.target.checked)}
              disabled={loading}
              className="rounded"
            />
            <Label htmlFor={fieldId} className="cursor-pointer">
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
          </div>
        );

      default:
        // Fallback for text area for longer text
        return (
          <div key={variable.name} className="space-y-2">
            <Label htmlFor={fieldId}>
              {variable.label_ka}
              {variable.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Textarea
              id={fieldId}
              value={formData[variable.name] || ''}
              onChange={(e) => handleChange(variable.name, e.target.value)}
              placeholder={variable.placeholder_ka || ''}
              className={hasError ? 'border-red-500' : ''}
              disabled={loading}
              rows={3}
            />
            {hasError && (
              <p className="text-sm text-red-500">{errors[variable.name]}</p>
            )}
          </div>
        );
    }
  };

  // Separate required and optional fields
  const requiredFields = template.variables.filter((v) => v.required);
  const optionalFields = template.variables.filter((v) => !v.required);

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            დოკუმენტის დეტალები
          </CardTitle>
          <CardDescription>
            შეავსეთ ყველა სავალდებულო ველი დოკუმენტის გენერირებისთვის
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Required Fields */}
          {requiredFields.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-lg text-gray-900">
                სავალდებულო ველები
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requiredFields.map(renderField)}
              </div>
            </div>
          )}

          {/* Optional Fields */}
          {optionalFields.length > 0 && (
            <div className="space-y-4 pt-4 border-t">
              <h3 className="font-semibold text-lg text-gray-900">
                არასავალდებულო ველები
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {optionalFields.map(renderField)}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 md:flex-none"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  გენერირდება...
                </>
              ) : (
                'დოკუმენტის გენერირება'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}
