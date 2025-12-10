// Server component that marks this route as dynamic
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function ChatTemplate({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
