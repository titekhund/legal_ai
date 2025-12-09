/**
 * CitationPanel component
 */

'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import type { ChatSources } from '@/lib/types';

export interface CitationPanelProps {
  sources: ChatSources | null;
  isOpen: boolean;
  onToggle: () => void;
}

export const CitationPanel: React.FC<CitationPanelProps> = ({
  sources,
  isOpen,
  onToggle,
}) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const hasSources = sources && sources.tax_articles.length > 0;

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Show empty state when no sources
  if (!hasSources) {
    return (
      <div className="w-full">
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 text-text-light text-sm">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>არჩეული პასუხისთვის ციტატები არ არის</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center justify-between p-3 rounded-lg',
          'bg-accent-50 hover:bg-accent-100 transition-colors',
          'text-accent-800 font-medium'
        )}
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span>
            მოიძებნა {sources.tax_articles.length} მუხლი
          </span>
        </div>
        <svg
          className={cn(
            'w-5 h-5 transition-transform',
            isOpen && 'transform rotate-180'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2">
          {sources.tax_articles.map((article, index) => {
            const citationText = `მუხლი ${article.article}${
              article.title ? `: ${article.title}` : ''
            }\n${article.content}${
              article.matsne_url ? `\n\nწყარო: ${article.matsne_url}` : ''
            }`;

            return (
              <Card key={index} variant="bordered" className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-100 text-accent-800">
                        მუხლი {article.article}
                      </span>
                      {article.relevance_score && (
                        <span className="text-xs text-text-light">
                          {Math.round(article.relevance_score * 100)}% რელევანტურობა
                        </span>
                      )}
                    </div>
                    <h4 className="font-medium text-text mb-1">{article.title}</h4>
                    <p className="text-sm text-text-light line-clamp-3">
                      {article.content}
                    </p>
                  </div>

                  {/* Copy button */}
                  <button
                    onClick={() => handleCopy(citationText, index)}
                    className={cn(
                      'shrink-0 p-2 rounded-lg transition-colors',
                      copiedIndex === index
                        ? 'bg-green-100 text-green-700'
                        : 'hover:bg-gray-100 text-text-light'
                    )}
                    title="ციტატის კოპირება"
                  >
                    {copiedIndex === index ? (
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                      </svg>
                    )}
                  </button>
                </div>

                {article.matsne_url && (
                  <div className="mt-3 flex items-center gap-2">
                    <a
                      href={article.matsne_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-sm text-primary hover:text-primary-600 font-medium"
                    >
                      <span>ნახე matsne.gov.ge-ზე</span>
                      <svg
                        className="w-4 h-4 ml-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </a>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
