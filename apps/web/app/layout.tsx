import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Alma Intake',
  description: 'Lead intake workflow for Alma',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
