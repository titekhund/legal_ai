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
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'დაწერეთ თქვენი კითხვა...',
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-2 p-4 bg-white border-t border-gray-200">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          'flex-1 px-4 py-2 rounded-lg border border-gray-300 bg-white text-text',
          'placeholder:text-text-lighter resize-none',
          'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'min-h-[44px] max-h-[200px]'
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
        disabled={disabled || !input.trim()}
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
  );
};
