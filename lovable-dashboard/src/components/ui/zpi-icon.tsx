import * as React from "react";

interface ZpiIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

export const ZpiIcon = React.forwardRef<SVGSVGElement, ZpiIconProps>(
  ({ size = 18, className, ...props }, ref) => (
    <svg
      ref={ref}
      width={size}
      height={size * 1.32}
      viewBox="0 0 140 185"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="ZIP archive icon"
      {...props}
    >
      {/* Main document */}
      <rect
        x="10"
        y="6"
        width="120"
        height="168"
        rx="20"
        fill="currentColor"
        fillOpacity="0.06"
        stroke="currentColor"
        strokeWidth="1.5"
      />

      {/* Top-right page curl */}
      <path d="M118 6 L132 20 L118 20 Z" fill="currentColor" fillOpacity="0.12" />
      <path
        d="M118 6 Q133 10 133 22"
        stroke="currentColor"
        strokeOpacity="0.4"
        strokeWidth="1.25"
        fill="none"
      />

      {/* Zipper pull tab body */}
      <rect x="57" y="24" width="26" height="52" rx="13" fill="currentColor" />

      {/* Finger hole */}
      <circle cx="70" cy="46" r="10" fill="white" />

      {/* Top cap of zipper */}
      <rect x="62" y="19" width="16" height="9" rx="4.5" fill="currentColor" />

      {/* Zipper teeth bars */}
      <rect x="63" y="84" width="14" height="5" rx="2.5" fill="currentColor" />
      <rect x="60" y="94" width="20" height="5" rx="2.5" fill="currentColor" />
      <rect x="63" y="104" width="14" height="5" rx="2.5" fill="currentColor" />
      <rect x="66" y="114" width="9" height="5" rx="2.5" fill="currentColor" />

      {/* ZIP text */}
      <text
        x="70"
        y="158"
        fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        fontSize="23"
        fontWeight="700"
        letterSpacing="4.5"
        fill="currentColor"
        textAnchor="middle"
        dominantBaseline="middle"
      >
        ZIP
      </text>
    </svg>
  )
);

ZpiIcon.displayName = "ZpiIcon";
