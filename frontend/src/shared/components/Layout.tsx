import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Footer } from './Footer'
import { ChatWidget } from '@/features/diretor-virtual/ChatWidget'

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <main className="flex-1 container max-w-6xl mx-auto px-4 py-8 animate-fade-in">
        <Outlet />
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
