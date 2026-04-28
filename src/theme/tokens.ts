/**
 * RGT V2 Design Tokens
 * 
 * Synchronized with Google Stitch Design System:
 * Project: RGT V2
 * Theme: Light Mode, Inter Font, Round 8
 */

export const COLORS = {
    primary: '#135bec', // Stitch Custom Color
    secondary: '#4f46e5',
    background: '#ffffff',
    surface: '#f8fafc',
    text: {
        primary: '#1e293b',
        secondary: '#64748b',
        inverse: '#ffffff',
    },
    status: {
        open: '#059669',
        caution: '#f59e0b',
        closed: '#dc2626',
        uncertain: '#64748b',
    },
    border: '#e2e8f0',
} as const;

export const TYPOGRAPHY = {
    fontFamily: 'Inter',
    sizes: {
        xs: 10,
        sm: 12,
        base: 14,
        lg: 16,
        xl: 20,
        xxl: 24,
    },
    weights: {
        regular: '400',
        medium: '500',
        bold: '700',
        black: '900',
    }
} as const;

export const SHAPES = {
    borderRadius: 8, // Stitch ROUND_EIGHT
    elevation: {
        sm: 2,
        md: 5,
        lg: 10,
    }
} as const;
