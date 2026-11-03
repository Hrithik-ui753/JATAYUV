import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive" | "tactical";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading = false, children, disabled, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 disabled:opacity-50 disabled:pointer-events-none select-none tracking-tight";

    const variants = {
      primary: "bg-emerald-600 text-white hover:bg-emerald-500 border border-emerald-400/30 shadow-md shadow-emerald-950/50 hover:shadow-emerald-900/40",
      secondary: "bg-forest-800 text-foreground hover:bg-forest-700 border border-emerald-500/15",
      outline: "border border-emerald-500/25 bg-forest-900/50 hover:bg-emerald-500/10 hover:border-emerald-500/40 text-foreground hover:text-emerald-300",
      ghost: "hover:bg-forest-800/60 hover:text-emerald-300 text-muted-foreground",
      destructive: "bg-rose-900/80 text-rose-100 hover:bg-rose-800 border border-rose-500/30 shadow-sm",
      tactical: "bg-forest-900 text-emerald-400 hover:text-white hover:bg-emerald-600/20 border border-emerald-500/30 font-mono text-xs uppercase tracking-wider",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs gap-1.5",
      md: "h-9 px-4 text-sm gap-2",
      lg: "h-11 px-6 text-sm md:text-base gap-2.5",
      icon: "h-9 w-9 p-0",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
