/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Aerospace Forest & Charcoal Palette
        forest: {
          950: "#040706",
          900: "#070D0B",
          850: "#0A120F",
          800: "#0E1814",
          700: "#13221C",
          600: "#1B3028",
          500: "#244237",
        },
        charcoal: {
          950: "#050606",
          900: "#0B0E0D",
          850: "#101413",
          800: "#161B1A",
          700: "#222A28",
        },
        mint: {
          300: "#6EE7B7",
          400: "#34D399",
          500: "#10B981",
          bright: "#00F5A0",
        },
        aerial: {
          depth: "#06b6d4",
          damage: "#ef4444",
          change: "#f59e0b",
          vegetation: "#10b981",
          water: "#3b82f6",
          building: "#8b5cf6",
          road: "#64748b"
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      keyframes: {
        scanDown: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(1000%)" },
        },
        radarPulse: {
          "0%": { transform: "scale(0.8)", opacity: "0.8" },
          "50%": { transform: "scale(1.05)", opacity: "0.4" },
          "100%": { transform: "scale(0.8)", opacity: "0.8" },
        },
        hudFlicker: {
          "0%, 100%": { opacity: "1" },
          "92%": { opacity: "0.95" },
          "96%": { opacity: "0.85" },
        },
        floatDrone: {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "50%": { transform: "translateY(-8px) rotate(0.5deg)" },
        }
      },
      animation: {
        "scan-down": "scanDown 6s linear infinite",
        "radar-pulse": "radarPulse 4s ease-in-out infinite",
        "hud-flicker": "hudFlicker 8s ease-in-out infinite",
        "float-drone": "floatDrone 5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
