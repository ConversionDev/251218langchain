'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Users, 
  BrainCircuit, 
  ShieldCheck, 
  BarChart3,
  LayoutDashboard
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  {
    name: '대시보드',
    href: '/v20',
    icon: LayoutDashboard,
  },
  {
    name: 'Core HR',
    href: '/v20/core',
    icon: Users,
  },
  {
    name: 'Talent Intelligence',
    href: '/v20/intelligence',
    icon: BrainCircuit,
  },
  {
    name: 'Verified Credential',
    href: '/v20/credential',
    icon: ShieldCheck,
  },
  {
    name: 'Performance Analytics',
    href: '/v20/performance',
    icon: BarChart3,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex h-16 items-center border-b border-slate-200 px-6 dark:border-slate-800">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          Success DNA
        </h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
