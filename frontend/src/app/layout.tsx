/**
 * Root layout with Georgian font support
 */
import type { Metadata, Viewport } from 'next';
import { Toaster } from 'react-hot-toast';
import './globals.css';

// Use system fonts as fallback for Georgian support
// Vercel will automatically optimize fonts if Google Fonts are available
const fontVariable = 'var(--font-noto-sans-georgian, system-ui, -apple-system, "Segoe UI", sans-serif)';

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || 'საგადასახადო კოდექსის AI ასისტენტი';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

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
    <html lang="ka">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+Georgian:wght@100..900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ fontFamily: fontVariable }}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#fff',
              color: '#1f2937',
              border: '1px solid #e5e7eb',
              fontFamily: fontVariable,
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
