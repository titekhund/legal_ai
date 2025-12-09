/**
 * Root layout with Georgian font support
 */

import type { Metadata } from 'next';
import { Noto_Sans_Georgian } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import './globals.css';

const notoSansGeorgian = Noto_Sans_Georgian({
  subsets: ['latin', 'georgian'],
  variable: '--font-noto-sans-georgian',
  display: 'swap',
});

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || 'საგადასახადო კოდექსის AI ასისტენტი';

export const metadata: Metadata = {
  title: {
    default: APP_NAME,
    template: `%s | ${APP_NAME}`,
  },
  description: 'ხელოვნური ინტელექტის იურიდიული ასისტენტი საქართველოს საგადასახადო კოდექსისთვის. დასვით კითხვა და მიიღეთ სწრაფი, ზუსტი პასუხები კონკრეტული მუხლების ციტირებით.',
  keywords: [
    'საგადასახადო კოდექსი',
    'საქართველო',
    'AI ასისტენტი',
    'იურიდიული კონსულტაცია',
    'Tax Code',
    'Georgia',
    'Legal AI',
  ],
  authors: [{ name: 'Georgian Legal AI' }],
  icons: {
    icon: '/favicon.ico',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ka" className={notoSansGeorgian.variable}>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className={notoSansGeorgian.className}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#fff',
              color: '#1f2937',
              border: '1px solid #e5e7eb',
              fontFamily: 'var(--font-noto-sans-georgian)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </body>
    </html>
  );
}
