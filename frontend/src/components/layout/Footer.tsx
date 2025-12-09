/**
 * Footer component
 */

'use client';

import React from 'react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 py-4">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-sm text-text-light">
            © {currentYear} Georgian Legal AI. ყველა უფლება დაცულია.
          </div>
          <div className="flex items-center gap-6 text-sm text-text-light">
            <a
              href="https://matsne.gov.ge"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary transition-colors"
            >
              matsne.gov.ge
            </a>
            <span className="text-text-lighter">|</span>
            <span>
              Powered by AI
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
