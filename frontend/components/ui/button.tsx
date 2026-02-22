import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = (
  variant: "default" | "outline" | "ghost" | "destructive",
  size?: "default" | "sm" | "lg" | "icon",
  className?: string
) =>
  cn(
    "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
    "motion-safe:transition-[color,background-color,border-color,box-shadow,transform] motion-safe:duration-200 motion-safe:ease-out",
    "motion-safe:hover:scale-[1.08] motion-safe:hover:-translate-y-2 motion-safe:hover:shadow-xl",
    "motion-safe:active:scale-[0.96] disabled:transform-none",
    size === "sm" && "h-8 px-3",
    size === "icon" && "h-9 w-9 shrink-0",
    (size === "default" || !size) && "h-9 px-4 py-2",
    size === "lg" && "h-11 px-6",
    variant === "default" && "bg-primary text-primary-foreground hover:bg-primary/90",
    variant === "outline" && "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    variant === "ghost" && "hover:bg-accent hover:text-accent-foreground",
    variant === "destructive" && "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    className
  );

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size, ...props }, ref) => (
    <button
      ref={ref}
      className={buttonVariants(variant, size, className)}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { Button };
