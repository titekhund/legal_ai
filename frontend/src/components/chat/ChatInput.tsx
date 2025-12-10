/**
 * ChatInput component
 */

'use client';

import React, { useState, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

const MAX_CHARS = 2000;

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'დასვით კითხვა საგადასახადო კოდექსის შესახებ...',
  maxLength = MAX_CHARS,
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled && input.length <= maxLength) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter to send
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
    // Plain Enter for new line (default behavior)
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    // Only update if within limit
    if (newValue.length <= maxLength) {
      setInput(newValue);
    }
  };

  const charCount = input.length;
  const isNearLimit = charCount > maxLength * 0.8;
  const isOverLimit = charCount > maxLength;

  return (
    <div className="bg-white border-t border-gray-200">
      <div className="flex flex-col gap-2 p-4">
        {/* Character count indicator */}
        {charCount > 0 && (
          <div className="flex items-center justify-between text-xs">
            <div className="text-text-lighter">
              Ctrl+Enter გასაგზავნად
            </div>
            <div
              className={cn(
                'font-medium',
                isOverLimit && 'text-red-500',
                isNearLimit && !isOverLimit && 'text-accent-600',
                !isNearLimit && 'text-text-light'
              )}
            >
              {charCount} / {maxLength}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              'flex-1 px-4 py-2 rounded-lg border border-gray-300 bg-white text-text',
              'placeholder:text-text-lighter resize-none',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'min-h-[44px] max-h-[200px]',
              isOverLimit && 'border-red-500 focus:ring-red-500'
            )}
            style={{
              height: 'auto',
              minHeight: '44px',
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
            }}
          />
          <Button
            onClick={handleSend}
            disabled={disabled || !input.trim() || isOverLimit}
            className="shrink-0"
          >
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
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
};
