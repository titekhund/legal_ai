/**
 * Landing page
 */

'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Header } from '@/components/layout/Header';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      {/* Header with auth */}
      <Header />

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-text mb-4">
            საგადასახადო კოდექსის AI ასისტენტი
          </h1>
          <p className="text-xl text-text-light mb-8 max-w-3xl mx-auto">
            დასვით ნებისმიერი კითხვა საქართველოს საგადასახადო კანონმდებლობის შესახებ
          </p>

          {!isLoading && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              {isAuthenticated ? (
                <Link href="/chat">
                  <Button size="lg" className="text-lg px-8">
                    ჩატის დაწყება
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
              ) : (
                <>
                  <Link href="/auth/register">
                    <Button size="lg" className="text-lg px-8">
                      უფასო რეგისტრაცია
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
                  <Link href="/auth/login">
                    <Button variant="outline" size="lg" className="text-lg px-8">
                      შესვლა
                    </Button>
                  </Link>
                </>
              )}
            </div>
          )}

          {/* Free tier info */}
          {!isAuthenticated && !isLoading && (
            <p className="mt-4 text-sm text-gray-500">
              უფასო ანგარიშით მიიღებთ 50 მოთხოვნას დღეში
            </p>
          )}
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Tax Code - Available */}
          <Card variant="bordered" className="relative">
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
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <CardTitle>საგადასახადო კოდექსი</CardTitle>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-2">
                ხელმისაწვდომია
              </span>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                დასვით კითხვა საქართველოს საგადასახადო კოდექსის შესახებ და მიიღეთ
                დეტალური პასუხი კონკრეტული მუხლების ციტირებით
              </p>
            </CardContent>
          </Card>

          {/* Court Cases - Coming Soon */}
          <Card variant="bordered" className="relative opacity-75">
            <CardHeader>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-gray-600"
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
              <CardTitle>სასამართლო პრაქტიკა</CardTitle>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 mt-2">
                მალე
              </span>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                იპოვეთ შესაბამისი სასამართლო გადაწყვეტილებები და პრეცედენტები
                თქვენი საქმის დასასაბუთებლად
              </p>
            </CardContent>
          </Card>

          {/* Document Generation - Coming Soon */}
          <Card variant="bordered" className="relative opacity-75">
            <CardHeader>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </div>
              <CardTitle>დოკუმენტების გენერაცია</CardTitle>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 mt-2">
                მალე
              </span>
            </CardHeader>
            <CardContent>
              <p className="text-text-light">
                შექმენით სამართლებრივი დოკუმენტები, განცხადებები და სარჩელები
                AI-ის დახმარებით
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
                  დარეგისტრირდით უფასოდ თქვენი ელ-ფოსტით
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </span>
                <span>
                  დაუსვით კითხვა საქართველოს საგადასახადო კოდექსთან დაკავშირებით
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </span>
                <span>
                  AI სისტემა გაანალიზებს თქვენს კითხვას და მოიძიებს შესაბამის ინფორმაციას
                </span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
                  4
                </span>
                <span>
                  მიიღეთ დეტალური პასუხი კონკრეტული მუხლებისა და ნორმების მითითებით
                </span>
              </li>
            </ol>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <svg
                className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-amber-900 mb-1">
                  გაფრთხილება
                </h4>
                <p className="text-sm text-amber-800">
                  ეს არის AI ასისტენტი და არ ცვლის პროფესიონალურ იურიდიულ კონსულტაციას.
                  რთული ან სპეციფიკური საქმეების შემთხვევაში მიმართეთ კვალიფიციურ იურისტს.
                </p>
              </div>
            </div>
          </div>
        </div>
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
