export const colors = {
  sepia: '#f4efe6',
  warmGold: '#d4af37',
  charcoal: '#1c1917',
  darkCharcoal: '#12100e',
  parchment: '#f5f2eb',
  mutedSepia: '#8c7b6b',
  warmAccent: '#b8860b',
} as const;

export const typography = {
  serifHeader: '"Playfair Display", "Cormorant Garamond", Georgia, serif',
  body: '"Noto Sans Devanagari", Inter, sans-serif',
} as const;

export const fontWeights = {
  serifHeaderMin: 600,
  headerMin: 600,
  bold: 700,
  semiBold: 600,
  regular: 400,
} as const;

export const borders = {
  goldThin: '1px solid #d4af37',
  goldMedium: '2px solid #d4af37',
  goldThick: '4px solid #d4af37',
  sepiaThin: '1px solid #8c7b6b',
  sepiaMedium: '2px solid #8c7b6b',
  charcoalThin: '1px solid #1c1917',
  parchmentThin: '1px solid #f5f2eb',
} as const;

export const shadows = {
  warmGlow: '0 0 15px rgba(212, 175, 55, 0.4)',
  goldGlow: '0 0 20px rgba(212, 175, 55, 0.5)',
  deepSoft: '0 10px 30px rgba(18, 16, 14, 0.6)',
  subtlePaper: '0 4px 12px rgba(28, 25, 23, 0.15)',
  goldDrop: '0 2px 8px rgba(212, 175, 55, 0.3)',
} as const;

export const editorialTheme = {
  colors,
  typography,
  fontWeights,
  borders,
  shadows,
} as const;

export default editorialTheme;
