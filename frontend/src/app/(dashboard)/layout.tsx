'use client';

import { AppShell } from '@mantine/core';
import { PairProvider } from '@/contexts/PairContext';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <PairProvider>
      <AppShell
        header={{ height: 60 }}
        navbar={{ width: 260, breakpoint: 'sm' }}
        padding="md"
      >
        <AppShell.Header>
          <Header />
        </AppShell.Header>

        <AppShell.Navbar>
          <Sidebar />
        </AppShell.Navbar>

        <AppShell.Main>{children}</AppShell.Main>
      </AppShell>
    </PairProvider>
  );
}
