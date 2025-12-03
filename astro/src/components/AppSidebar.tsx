import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Receipt, 
  Store, 
  Package, 
  FolderTree,
  Menu,
  X,
  LogOut,
  User
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { title: 'Paragony', href: '/bills', icon: Receipt },
  { title: 'Sklepy', href: '/shops', icon: Store },
  { title: 'Produkty', href: '/products', icon: Package },
  { title: 'Kategorie', href: '/categories', icon: FolderTree },
];

interface AppSidebarProps {
  className?: string;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({ className }) => {
  const [currentPath, setCurrentPath] = useState<string>('');

  useEffect(() => {
    setCurrentPath(window.location.pathname);
    
    // Listen for navigation changes
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    
    window.addEventListener('popstate', handleLocationChange);
    // Also check on any link click
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      if (link && link.href) {
        setTimeout(() => {
          setCurrentPath(window.location.pathname);
        }, 100);
      }
    };
    
    document.addEventListener('click', handleClick);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      document.removeEventListener('click', handleClick);
    };
  }, []);

  // Mock data - w przyszłości z API
  const usageLimit = 45; // 45/100
  const usagePercentage = 45;
  const userName = 'Użytkownik';

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return currentPath === '/' || currentPath === '/dashboard';
    }
    return currentPath.startsWith(href);
  };

  return (
    <aside className={cn("flex flex-col h-screen border-r bg-background", className)}>
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <h1 className="text-xl font-bold">Bills</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          
          return (
            <a
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.title}
            </a>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t p-4 space-y-4">
        {/* Usage Limit */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Limit paragonów</span>
            <span className="font-medium">{usageLimit}/100</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-primary/20">
            <div
              className={cn(
                "h-full transition-all",
                usagePercentage >= 90 ? "bg-destructive" : "bg-primary"
              )}
              style={{ width: `${usagePercentage}%` }}
            />
          </div>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-3">
          <Avatar>
            <AvatarFallback>
              <User className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{userName}</p>
            <p className="text-xs text-muted-foreground truncate">Freemium</p>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
};

// Mobile Sidebar (Sheet)
export const MobileSidebar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [currentPath, setCurrentPath] = useState<string>('');

  useEffect(() => {
    setCurrentPath(window.location.pathname);
    
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return currentPath === '/' || currentPath === '/dashboard';
    }
    return currentPath.startsWith(href);
  };

  // Mock data
  const usageLimit = 45;
  const usagePercentage = 45;
  const userName = 'Użytkownik';

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-6 w-6" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[250px] p-0">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex h-16 items-center border-b px-6">
            <h1 className="text-xl font-bold">Bills</h1>
            <Button
              variant="ghost"
              size="icon"
              className="ml-auto h-8 w-8"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              
              return (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.title}
                </a>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="border-t p-4 space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Limit paragonów</span>
                <span className="font-medium">{usageLimit}/100</span>
              </div>
              <div className="relative h-2 w-full overflow-hidden rounded-full bg-primary/20">
                <div
                  className={cn(
                    "h-full transition-all",
                    usagePercentage >= 90 ? "bg-destructive" : "bg-primary"
                  )}
                  style={{ width: `${usagePercentage}%` }}
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback>
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{userName}</p>
                <p className="text-xs text-muted-foreground truncate">Freemium</p>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

