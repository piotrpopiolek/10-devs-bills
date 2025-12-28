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
  User,
  UserCheck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { authService } from '@/lib/services/auth';
import type { UserProfile } from '@/types';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { title: 'Paragony', href: '/bills', icon: Receipt },
  { title: 'Sklepy', href: '/shops', icon: Store },
  { title: 'Produkty', href: '/product-indexes', icon: Package },
  { title: 'Kandydaci', href: '/product-candidates', icon: UserCheck },
  { title: 'Kategorie', href: '/categories', icon: FolderTree },
];

interface AppSidebarProps {
  className?: string;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({ className }) => {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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

  // Fetch user profile data
  useEffect(() => {
    // Small delay to ensure localStorage is available after page load/redirect
    const timer = setTimeout(() => {
      const fetchUserProfile = async () => {
        if (!authService.isAuthenticated()) {
          setIsLoading(false);
          return;
        }

        try {
          setIsLoading(true);
          setError(null);
          const profile = await authService.getUserProfile();
          setUserProfile(profile);
        } catch (err) {
          console.error('Error fetching user profile:', err);
          setError(err instanceof Error ? err.message : 'Błąd pobierania danych');
        } finally {
          setIsLoading(false);
        }
      };

      fetchUserProfile();
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  // Calculate usage stats from user profile
  const usageLimit = userProfile?.usage.bills_this_month ?? 0;
  const monthlyLimit = userProfile?.usage.monthly_limit ?? 100;
  const usagePercentage = monthlyLimit > 0 ? Math.round((usageLimit / monthlyLimit) * 100) : 0;
  const userName = userProfile?.external_id 
    ? `Użytkownik ${userProfile.external_id}` 
    : 'Użytkownik';

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return currentPath === '/' || currentPath === '/dashboard';
    }
    return currentPath.startsWith(href);
  };

  const handleLogout = () => {
    authService.clearSession();
    window.location.href = '/';
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
            <span className="font-medium">
              {isLoading ? '...' : `${usageLimit}/${monthlyLimit}`}
            </span>
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
            <p className="text-sm font-medium truncate">
              {isLoading ? 'Ładowanie...' : userName}
            </p>
            <p className="text-xs text-muted-foreground truncate">Freemium</p>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8"
            onClick={handleLogout}
            title="Wyloguj"
          >
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
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setCurrentPath(window.location.pathname);
    
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  // Fetch user profile data
  useEffect(() => {
    // Small delay to ensure localStorage is available after page load/redirect
    const timer = setTimeout(() => {
      const fetchUserProfile = async () => {
        if (!authService.isAuthenticated()) {
          setIsLoading(false);
          return;
        }

        try {
          setIsLoading(true);
          setError(null);
          const profile = await authService.getUserProfile();
          setUserProfile(profile);
        } catch (err) {
          console.error('Error fetching user profile:', err);
          setError(err instanceof Error ? err.message : 'Błąd pobierania danych');
        } finally {
          setIsLoading(false);
        }
      };

      fetchUserProfile();
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return currentPath === '/' || currentPath === '/dashboard';
    }
    return currentPath.startsWith(href);
  };

  const handleLogout = () => {
    authService.clearSession();
    setOpen(false); // Close mobile sidebar
    window.location.href = '/';
  };

  // Calculate usage stats from user profile
  const usageLimit = userProfile?.usage.bills_this_month ?? 0;
  const monthlyLimit = userProfile?.usage.monthly_limit ?? 100;
  const usagePercentage = monthlyLimit > 0 ? Math.round((usageLimit / monthlyLimit) * 100) : 0;
  const userName = userProfile?.external_id 
    ? `Użytkownik ${userProfile.external_id}` 
    : 'Użytkownik';

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
                <span className="font-medium">
                  {isLoading ? '...' : `${usageLimit}/${monthlyLimit}`}
                </span>
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
                <p className="text-sm font-medium truncate">
                  {isLoading ? 'Ładowanie...' : userName}
                </p>
                <p className="text-xs text-muted-foreground truncate">Freemium</p>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8"
                onClick={handleLogout}
                title="Wyloguj"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

