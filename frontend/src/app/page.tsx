/**
 * Landing page
 */

import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                />
              </svg>
            </div>
            <span className="text-xl font-semibold text-text">
              {process.env.NEXT_PUBLIC_APP_NAME || 'TaxCode AI'}
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-text mb-4">
            საგადასახადო კოდექსის AI ასისტენტი
          </h1>
          <p className="text-xl text-text-light mb-8 max-w-3xl mx-auto">
            ხელოვნური ინტელექტის საშუალებით მიიღეთ სწრაფი და ზუსტი პასუხები
            საქართველოს საგადასახადო კოდექსთან დაკავშირებული კითხვებზე
          </p>
          <Link href="/chat">
            <Button size="lg" className="text-lg px-8">
              დაიწყეთ საუბარი
              <svg
                className="w-5 h-5 ml-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </Button>
          </Link>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card variant="bordered">
            <CardHeader>
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <CardTitle>სწრაფი პასუხები</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                მიიღეთ დაუყოვნებლივ პასუხები თქვენს კითხვებზე AI-ის საშუალებით
              </p>
            </CardContent>
          </Card>

          <Card variant="bordered">
            <CardHeader>
              <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-accent"
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
              </div>
              <CardTitle>ზუსტი ციტირება</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                ყველა პასუხი აღჭურვილია კონკრეტული მუხლებისა და ნორმების ციტატებით
              </p>
            </CardContent>
          </Card>

          <Card variant="bordered">
            <CardHeader>
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
              </div>
              <CardTitle>საუბრების ისტორია</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                შეინახეთ და დაუბრუნდით თქვენს წინა საუბრებს ნებისმიერ დროს
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Info Section */}
        <Card variant="elevated" className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>როგორ მუშაობს?</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4 text-text-light">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </span>
                <span>
                  დაუსვით კითხვა საქართველოს საგადასახადო კოდექსთან დაკავშირებით
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </span>
                <span>
                  AI სისტემა გაანალიზებს თქვენს კითხვას და მოიძიებს შესაბამის ინფორმაციას
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </span>
                <span>
                  მიიღეთ დეტალური პასუხი კონკრეტული მუხლებისა და ნორმების მითითებით
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  4
                </span>
                <span>
                  გადადით matsne.gov.ge-ზე სრული ტექსტის სანახავად
                </span>
              </li>
            </ol>
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-text-light">
            © {new Date().getFullYear()} Georgian Legal AI. ყველა უფლება დაცულია.
          </div>
        </div>
      </footer>
    </div>
  );
}
