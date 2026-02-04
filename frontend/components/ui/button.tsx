import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = (
  variant: "default" | "outline" | "ghost" | "destructive",
  className?: string
) =>
  cn(
    "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2",
    variant === "default" && "bg-primary text-primary-foreground hover:bg-primary/90",
    variant === "outline" && "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    variant === "ghost" && "hover:bg-accent hover:text-accent-foreground",
    variant === "destructive" && "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    className
  );

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "destructive";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={buttonVariants(variant, className)}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { Button };
