/**
 * CitationPanel component - Shows sources with tabs for different types
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

type SourceTab = 'articles' | 'disputes';

export const CitationPanel: React.FC<CitationPanelProps> = ({
  sources,
  isOpen,
  onToggle,
}) => {
  const [activeTab, setActiveTab] = useState<SourceTab>('articles');
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  const hasArticles = sources && sources.tax_articles.length > 0;
  const hasDisputes = sources && sources.cases.length > 0;
  const hasSources = hasArticles || hasDisputes;

  const handleCopy = async (text: string, index: string) => {
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

  const totalSources = (sources.tax_articles.length || 0) + (sources.cases.length || 0);

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
            მოიძებნა {totalSources} წყარო
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
        <div className="mt-2">
          {/* Tabs */}
          {hasArticles && hasDisputes && (
            <div className="flex gap-2 border-b border-gray-200 mb-3">
              <button
                onClick={() => setActiveTab('articles')}
                className={cn(
                  'px-4 py-2 font-medium text-sm transition-colors border-b-2',
                  activeTab === 'articles'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-light hover:text-text'
                )}
              >
                მუხლები ({sources.tax_articles.length})
              </button>
              <button
                onClick={() => setActiveTab('disputes')}
                className={cn(
                  'px-4 py-2 font-medium text-sm transition-colors border-b-2',
                  activeTab === 'disputes'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-light hover:text-text'
                )}
              >
                დავები ({sources.cases.length})
              </button>
            </div>
          )}

          {/* Articles Tab Content */}
          {(activeTab === 'articles' || !hasDisputes) && hasArticles && (
            <div className="space-y-2">
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
                        onClick={() => handleCopy(citationText, `article-${index}`)}
                        className={cn(
                          'shrink-0 p-2 rounded-lg transition-colors',
                          copiedIndex === `article-${index}`
                            ? 'bg-green-100 text-green-700'
                            : 'hover:bg-gray-100 text-text-light'
                        )}
                        title="ციტატის კოპირება"
                      >
                        {copiedIndex === `article-${index}` ? (
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

          {/* Disputes Tab Content */}
          {(activeTab === 'disputes' || !hasArticles) && hasDisputes && (
            <div className="space-y-2">
              {sources.cases.map((disputeCase, index) => {
                const citationText = `დავა #${disputeCase.doc_number || 'N/A'}${
                  disputeCase.date ? `\nთარიღი: ${disputeCase.date}` : ''
                }${
                  disputeCase.category ? `\nკატეგორია: ${disputeCase.category}` : ''
                }${
                  disputeCase.decision_type ? `\nგადაწყვეტილება: ${disputeCase.decision_type}` : ''
                }${
                  disputeCase.snippet ? `\n\n${disputeCase.snippet}` : ''
                }`;

                return (
                  <Card key={index} variant="bordered" className="p-4 bg-purple-50 border-purple-200">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            დავა #{disputeCase.doc_number || 'N/A'}
                          </span>
                          {disputeCase.decision_type && (
                            <span className={cn(
                              'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                              disputeCase.decision_type === 'satisfied' && 'bg-green-100 text-green-800',
                              disputeCase.decision_type === 'rejected' && 'bg-red-100 text-red-800',
                              disputeCase.decision_type === 'partially_satisfied' && 'bg-yellow-100 text-yellow-800'
                            )}>
                              {disputeCase.decision_type === 'satisfied' && 'დაკმაყოფილდა'}
                              {disputeCase.decision_type === 'rejected' && 'არ დაკმაყოფილდა'}
                              {disputeCase.decision_type === 'partially_satisfied' && 'ნაწილობრივ'}
                              {!['satisfied', 'rejected', 'partially_satisfied'].includes(disputeCase.decision_type) && disputeCase.decision_type}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-text-light mb-2">
                          {disputeCase.date && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {disputeCase.date}
                            </span>
                          )}
                          {disputeCase.category && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                              </svg>
                              {disputeCase.category}
                            </span>
                          )}
                        </div>
                        {disputeCase.snippet && (
                          <p className="text-sm text-text-light line-clamp-3">
                            {disputeCase.snippet}
                          </p>
                        )}
                      </div>

                      {/* Copy button */}
                      <button
                        onClick={() => handleCopy(citationText, `dispute-${index}`)}
                        className={cn(
                          'shrink-0 p-2 rounded-lg transition-colors',
                          copiedIndex === `dispute-${index}`
                            ? 'bg-green-100 text-green-700'
                            : 'hover:bg-purple-100 text-text-light'
                        )}
                        title="ციტატის კოპირება"
                      >
                        {copiedIndex === `dispute-${index}` ? (
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
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
