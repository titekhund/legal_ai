/**
 * Chat page
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { ChatWindow } from '@/components/chat/ChatWindow';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const conversationId = searchParams.get('id') || undefined;

  return <ChatWindow conversationId={conversationId} mode="tax" language="ka" />;
}
