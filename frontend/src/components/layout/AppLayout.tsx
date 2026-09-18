import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  ClipboardCheck,
  ShieldCheck,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/upload', label: 'Upload', icon: UploadCloud, end: false },
  { to: '/invoices', label: 'Invoices', icon: FileText, end: false },
  { to: '/review', label: 'Review queue', icon: ClipboardCheck, end: false },
]

export default function AppLayout() {
  const { pathname } = useLocation()

  // Route changes should start at the top of the page.
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [pathname])

  return (
    <div className="min-h-screen bg-paper-100 bg-paper-fade">
      <header className="sticky top-0 z-40 border-b border-paper-300 bg-paper-100">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
          {/* Wordmark */}
          <NavLink to="/" className="flex shrink-0 items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-stone-900 text-paper-50">
              <ShieldCheck className="h-4 w-4" strokeWidth={2} />
            </span>
            <span className="flex items-baseline gap-2.5">
              <span className="font-serif text-[19px] font-semibold tracking-tight text-stone-900">
                InvoiceIQ
              </span>
              <span className="hidden text-[10px] uppercase tracking-[0.18em] text-stone-500 sm:block">
                Invoice verification
              </span>
            </span>
          </NavLink>

          {/* Desktop nav — ruled underline marks the active page */}
          <nav className="ml-auto hidden items-stretch gap-6 md:flex">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    '-mb-px inline-flex items-center gap-2 border-b-2 pb-0.5 text-[13px] font-medium transition-colors',
                    isActive
                      ? 'border-stone-900 text-stone-900'
                      : 'border-transparent text-stone-600 hover:text-stone-900',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={cn('h-3.5 w-3.5', isActive ? 'text-stone-900' : 'text-stone-400')}
                      strokeWidth={2}
                    />
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="hidden h-5 w-px bg-paper-300 md:block" />

          <a
            href="/api/health"
            target="_blank"
            rel="noreferrer"
            className="hidden items-center gap-1.5 text-[10px] uppercase tracking-[0.16em] text-stone-500 transition-colors hover:text-stone-900 md:inline-flex"
            title="Backend health check"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#2f6b47]" />
            API
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-24 pt-10 sm:px-6 md:pb-14 lg:px-8">
        <Outlet />
      </main>

      <footer className="hidden border-t border-paper-300 md:block">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-6 text-[11px] text-stone-500 sm:px-6 lg:px-8">
          <p>
            InvoiceIQ — deterministic verification, AI explanation. Risk scores are computed by the
            backend, never by the model.
          </p>
          <p className="tabular shrink-0 uppercase tracking-[0.16em]">v0.1.0</p>
        </div>
      </footer>

      {/* Mobile navigation */}
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-paper-300 bg-paper-100 pb-[env(safe-area-inset-bottom)] md:hidden">
        <div className="grid grid-cols-4">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium tracking-wide transition-colors',
                  isActive ? 'text-stone-900' : 'text-stone-500',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cn(
                      'flex h-7 w-10 items-center justify-center border-b-2',
                      isActive ? 'border-stone-900' : 'border-transparent',
                    )}
                  >
                    <Icon className="h-[17px] w-[17px]" strokeWidth={1.8} />
                  </span>
                  <span className="truncate">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
