/**
 * ModeSelector component - Tab-style mode selector for chat
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { QueryMode } from '@/lib/types';

export interface ModeSelectorProps {
  currentMode: QueryMode;
  onModeChange: (mode: QueryMode) => void;
  availableModes: {
    id: QueryMode;
    label: string;
    labelKa: string;
    available: boolean;
    icon: React.ReactNode;
  }[];
  language?: 'ka' | 'en';
}

export const ModeSelector: React.FC<ModeSelectorProps> = ({
  currentMode,
  onModeChange,
  availableModes,
  language = 'ka',
}) => {
  return (
    <div className="w-full border-b border-gray-200 bg-white">
      <div className="flex gap-1 p-2">
        {availableModes.map((mode) => {
          const isActive = currentMode === mode.id;
          const isDisabled = !mode.available;

          return (
            <button
              key={mode.id}
              onClick={() => !isDisabled && onModeChange(mode.id)}
              disabled={isDisabled}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
                'text-sm whitespace-nowrap',
                isActive && [
                  'bg-primary text-white shadow-sm',
                ],
                !isActive && !isDisabled && [
                  'text-text-light hover:bg-gray-100',
                ],
                isDisabled && [
                  'text-text-lighter cursor-not-allowed opacity-50',
                ],
              )}
              title={isDisabled ? (language === 'ka' ? 'მალე მოვა' : 'Coming Soon') : ''}
            >
              {/* Icon */}
              <span className={cn(
                'w-5 h-5',
                isActive && 'text-white',
                !isActive && !isDisabled && 'text-text-light',
                isDisabled && 'text-text-lighter'
              )}>
                {mode.icon}
              </span>

              {/* Label */}
              <span>{language === 'ka' ? mode.labelKa : mode.label}</span>

              {/* Coming soon badge for disabled modes */}
              {isDisabled && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                  {language === 'ka' ? 'მალე' : 'Soon'}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

// Default modes configuration
export const DEFAULT_MODES = [
  {
    id: 'auto' as QueryMode,
    label: 'Auto',
    labelKa: 'ავტომატური',
    available: true,
    icon: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
  },
  {
    id: 'tax' as QueryMode,
    label: 'Tax Code',
    labelKa: 'საგადასახადო კოდექსი',
    available: true,
    icon: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
  },
  {
    id: 'dispute' as QueryMode,
    label: 'Disputes',
    labelKa: 'დავების პრაქტიკა',
    available: true,
    icon: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
        />
      </svg>
    ),
  },
  {
    id: 'document' as QueryMode,
    label: 'Documents',
    labelKa: 'დოკუმენტები',
    available: false, // Phase 3
    icon: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
    ),
  },
];
