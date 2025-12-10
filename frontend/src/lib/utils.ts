/**
 * Utility functions for Legal AI application
 */

import { type ClassValue, clsx } from 'clsx';

/**
 * Merge class names with tailwind-merge to avoid conflicts
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format date to Georgian locale
 */
export function formatDate(date: string | Date, locale: 'ka' | 'en' = 'ka'): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  if (locale === 'ka') {
    return d.toLocaleDateString('ka-GE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format time ago (e.g., "5 minutes ago")
 */
export function formatTimeAgo(date: string | Date, locale: 'ka' | 'en' = 'ka'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const seconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  const intervals = {
    ka: {
      year: { singular: 'წელი', plural: 'წელი' },
      month: { singular: 'თვე', plural: 'თვე' },
      week: { singular: 'კვირა', plural: 'კვირა' },
      day: { singular: 'დღე', plural: 'დღე' },
      hour: { singular: 'საათი', plural: 'საათი' },
      minute: { singular: 'წუთი', plural: 'წუთი' },
      second: { singular: 'წამი', plural: 'წამი' },
      ago: 'წინ',
      just_now: 'ახლახან',
    },
    en: {
      year: { singular: 'year', plural: 'years' },
      month: { singular: 'month', plural: 'months' },
      week: { singular: 'week', plural: 'weeks' },
      day: { singular: 'day', plural: 'days' },
      hour: { singular: 'hour', plural: 'hours' },
      minute: { singular: 'minute', plural: 'minutes' },
      second: { singular: 'second', plural: 'seconds' },
      ago: 'ago',
      just_now: 'just now',
    },
  };

  const i = intervals[locale];

  if (seconds < 30) return i.just_now;

  type IntervalKey = 'year' | 'month' | 'week' | 'day' | 'hour' | 'minute' | 'second';
  const timeIntervals: [number, IntervalKey][] = [
    [31536000, 'year'],
    [2592000, 'month'],
    [604800, 'week'],
    [86400, 'day'],
    [3600, 'hour'],
    [60, 'minute'],
    [1, 'second'],
  ];

  for (const [secondsInInterval, name] of timeIntervals) {
    const interval = Math.floor(seconds / secondsInInterval);
    if (interval >= 1) {
      const unit = interval === 1 ? i[name].singular : i[name].plural;
      return locale === 'ka' ? `${interval} ${unit} ${i.ago}` : `${interval} ${unit} ${i.ago}`;
    }
  }

  return i.just_now;
}

/**
 * Truncate text to specified length
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}

/**
 * Extract article number from citation text
 */
export function extractArticleNumber(citation: string): string | null {
  // Match patterns like "მუხლი 168", "168-ე მუხლი", etc.
  const patterns = [
    /მუხლი\s*(\d+)/,
    /(\d+)-ე\s*მუხლ/,
    /article\s*(\d+)/i,
  ];

  for (const pattern of patterns) {
    const match = citation.match(pattern);
    if (match) return match[1];
  }

  return null;
}

/**
 * Validate Georgian text
 */
export function isGeorgianText(text: string): boolean {
  // Georgian Unicode range: U+10A0 to U+10FF
  const georgianRegex = /[\u10A0-\u10FF]/;
  return georgianRegex.test(text);
}

/**
 * Simple Georgian text detection for auto-switching language
 */
export function detectLanguage(text: string): 'ka' | 'en' {
  return isGeorgianText(text) ? 'ka' : 'en';
}

/**
 * Format processing time
 */
export function formatProcessingTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}
