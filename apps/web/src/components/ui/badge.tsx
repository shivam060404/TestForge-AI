import * as React from 'react';
import { cn } from '@/lib/utils';
import { getStatusColor } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'status';
  status?: string;
}

function Badge({ className, variant = 'default', status, ...props }: BadgeProps) {
  if (variant === 'status' && status) {
    return <div className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', getStatusColor(status), className)} {...props} />;
  }

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
        {
          'bg-primary/10 text-primary': variant === 'default',
          'bg-secondary/10 text-secondary-foreground': variant === 'secondary',
          'bg-destructive/10 text-destructive': variant === 'destructive',
          'border border-input bg-transparent': variant === 'outline',
        },
        className
      )}
      {...props}
    />
  );
}

export { Badge };