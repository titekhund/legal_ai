/**
 * ExampleQuestions component - Shows mode-specific example questions
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { QueryMode } from '@/lib/types';

export interface ExampleQuestionsProps {
  mode: QueryMode;
  onQuestionClick: (question: string) => void;
  language?: 'ka' | 'en';
}

const EXAMPLE_QUESTIONS: Record<QueryMode, { ka: string[]; en: string[] }> = {
  auto: {
    ka: [
      'რა არის დღგ-ს განაკვეთი საქართველოში?',
      'როგორ განიმარტა მუხლი 168 დავების პრაქტიკაში?',
      'როგორ ხდება საშემოსავლო გადასახადის გამოთვლა?',
      'რა პრეცედენტები არსებობს დღგ-ის ჩათვლასთან დაკავშირებით?',
      'რა არის საგადასახადო ანგარიშგების ვადები?',
    ],
    en: [
      'What is the VAT rate in Georgia?',
      'How was Article 168 interpreted in dispute practice?',
      'How is income tax calculated?',
      'What precedents exist regarding VAT deduction?',
      'What are the tax reporting deadlines?',
    ],
  },
  tax: {
    ka: [
      'რა არის დღგ-ს განაკვეთი საქართველოში?',
      'როგორ ხდება საშემოსავლო გადასახადის გამოთვლა?',
      'რა არის საგადასახადო ანგარიშგების ვადები?',
      'როგორია ქონების გადასახადის წესები?',
      'რა არის საგადასახადო დავალიანების ჯარიმა?',
    ],
    en: [
      'What is the VAT rate in Georgia?',
      'How is income tax calculated?',
      'What are the tax reporting deadlines?',
      'What are the property tax rules?',
      'What are the penalties for tax debt?',
    ],
  },
  dispute: {
    ka: [
      'როგორ განიმარტა მუხლი 168 დავების პრაქტიკაში?',
      'რა პრეცედენტები არსებობს დღგ-ის ჩათვლასთან დაკავშირებით?',
      'რა გადაწყვეტილებები არსებობს საწარმოო საქმიანობის განმარტებაზე?',
      'როგორ წყდება დავები საგადასახადო ვალდებულებებთან დაკავშირებით?',
      'რა საბუთებია საჭირო დავის განხილვისთვის?',
    ],
    en: [
      'How was Article 168 interpreted in dispute practice?',
      'What precedents exist regarding VAT deduction?',
      'What decisions exist on the interpretation of production activity?',
      'How are disputes related to tax obligations resolved?',
      'What documents are required for dispute review?',
    ],
  },
  document: {
    ka: [
      'როგორ შევავსო საგადასახადო დეკლარაცია?',
      'რა ფორმატში უნდა იყოს საბუღალტრო დოკუმენტები?',
      'როგორ მოვამზადო საჩივარი დავების საბჭოსთვის?',
    ],
    en: [
      'How to fill out a tax declaration?',
      'What format should accounting documents be in?',
      'How to prepare an appeal to the disputes council?',
    ],
  },
};

export const ExampleQuestions: React.FC<ExampleQuestionsProps> = ({
  mode,
  onQuestionClick,
  language = 'ka',
}) => {
  const questions = EXAMPLE_QUESTIONS[mode]?.[language] || EXAMPLE_QUESTIONS.auto[language];

  return (
    <div className="w-full mb-6">
      <h3 className="text-sm font-medium text-text-light mb-3">
        {language === 'ka' ? 'მაგალითები:' : 'Examples:'}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className={cn(
              'text-left px-4 py-3 rounded-lg border border-gray-200',
              'bg-white hover:bg-gray-50 hover:border-primary',
              'transition-colors duration-200',
              'text-sm text-text-light hover:text-text'
            )}
          >
            <div className="flex items-start gap-2">
              <svg
                className="w-4 h-4 mt-0.5 shrink-0 text-accent"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{question}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
