import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { RefreshCw, Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BillImageViewerProps {
  imageUrl: string | null;
  imageExpiresAt?: string | null;
  isLoading: boolean;
  alt?: string;
  onRefresh?: () => void;
}

export const BillImageViewer: React.FC<BillImageViewerProps> = ({
  imageUrl,
  imageExpiresAt,
  isLoading,
  alt = 'Zdjęcie paragonu',
  onRefresh,
}) => {
  const [imageError, setImageError] = useState(false);
  const [isImageLoading, setIsImageLoading] = useState(true);

  // Check if URL is expired
  const isUrlExpired = (): boolean => {
    if (!imageExpiresAt) {
      return false; // Cannot determine if expired without expiration date
    }
    try {
      const expiresAt = new Date(imageExpiresAt);
      return expiresAt < new Date();
    } catch {
      return false; // If parsing fails, assume not expired
    }
  };

  const handleImageLoad = () => {
    setIsImageLoading(false);
    setImageError(false);
  };

  const handleImageError = () => {
    setIsImageLoading(false);
    setImageError(true);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="rounded-md border overflow-hidden">
        <Skeleton className="w-full h-[400px]" />
      </div>
    );
  }

  // No image URL
  if (!imageUrl) {
    return (
      <div className="rounded-md border p-8 text-center text-muted-foreground">
        <ImageIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>Brak zdjęcia paragonu</p>
      </div>
    );
  }

  // URL expired
  if (isUrlExpired()) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground mb-4">
          Link do zdjęcia wygasł
        </p>
        {onRefresh && (
          <Button onClick={onRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Odśwież
          </Button>
        )}
      </div>
    );
  }

  // Image error
  if (imageError) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground mb-4">
          Nie można załadować zdjęcia paragonu
        </p>
        {onRefresh && (
          <Button onClick={onRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Odśwież
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-md border overflow-hidden">
      <Dialog>
        <DialogTrigger asChild>
          <button
            className="relative w-full cursor-pointer hover:opacity-90 transition-opacity"
            aria-label="Kliknij, aby powiększyć zdjęcie paragonu"
          >
            {isImageLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-muted">
                <Skeleton className="w-full h-full" />
              </div>
            )}
            <img
              src={imageUrl}
              alt={alt}
              className={cn(
                'w-full h-auto object-contain max-h-[600px]',
                isImageLoading && 'opacity-0'
              )}
              loading="lazy"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </button>
        </DialogTrigger>
        <DialogContent className="max-w-7xl w-full p-0">
          <div className="relative w-full h-[90vh] flex items-center justify-center bg-muted/50">
            <img
              src={imageUrl}
              alt={alt}
              className="max-w-full max-h-full object-contain"
              onError={handleImageError}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
