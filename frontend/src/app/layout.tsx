/**
 * Root layout with Georgian font support
 */

import type { Metadata } from 'next';
import { Noto_Sans_Georgian } from 'next/font/google';
import './globals.css';

const notoSansGeorgian = Noto_Sans_Georgian({
  subsets: ['latin', 'georgian'],
  variable: '--font-noto-sans-georgian',
  display: 'swap',
});

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME || 'TaxCode AI',
  description: 'AI-powered legal assistant for Georgian Tax Code | ხელოვნური ინტელექტის იურიდიული ასისტენტი საქართველოს საგადასახადო კოდექსისთვის',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ka" className={notoSansGeorgian.variable}>
      <body className={notoSansGeorgian.className}>
        {children}
      </body>
    </html>
  );
}
