import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './app/App'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              borderRadius: '10px',
              padding: '14px 18px',
              fontSize: '14px',
              fontWeight: '500',
              maxWidth: '440px',
              boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
            },
            success: {
              style: { background: '#16a34a', color: '#fff' },
              iconTheme: { primary: '#fff', secondary: '#16a34a' },
              duration: 6000,
            },
            error: {
              style: { background: '#dc2626', color: '#fff' },
              iconTheme: { primary: '#fff', secondary: '#dc2626' },
              duration: 6000,
            },
            duration: 5000,
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
