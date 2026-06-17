# FinOps Copilot — Design System & Component Guide

## Layout Architecture

### Main Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│                      App Container                          │
├──────────┬────────────────────────────────────────────────┤
│ Sidebar  │              Main Content Area                 │
│ (64px    │  • Chat Panel   (messages, input)              │
│  or      │  • Dashboard    (KPIs, charts)                 │
│  264px)  │  • Approvals    (action queue)                 │
│          │                                                 │
│          ├─ Header (sticky)                              │
│          ├─ Scrollable Content                           │
│          └─ Fixed Input/Footer                           │
└──────────┴────────────────────────────────────────────────┘
```

---

## Spacing System

### Vertical Spacing
- `py-2` = 8px
- `py-3` = 12px
- `py-4` = 16px
- `py-6` = 24px
- `py-8` = 32px

### Horizontal Padding
- `px-4` = 16px (mobile)
- `px-6` = 24px (tablet/desktop)

### Gap Between Elements
- `gap-1` = 4px (tight)
- `gap-2` = 8px (normal)
- `gap-3` = 12px (comfortable)
- `gap-4` = 16px (spacious)

---

## Typography

### Font Sizes & Weights

| Use Case | Size | Weight | Example |
|----------|------|--------|---------|
| Main Title | 28px-48px | Bold (700) | "How can I help?" |
| Section Title | 20px-24px | Bold (700) | "Cost Dashboard" |
| Subheading | 14px-16px | Semibold (600) | Card titles |
| Body Text | 14px-16px | Normal (400) | Message content |
| Label | 12px-13px | Medium (500) | "Tool calls" |
| Caption | 11px-12px | Normal (400) | Hints & helpers |

### Line Heights
- Headings: `tracking-tight`
- Body: `leading-relaxed` (1.75)
- Compact: `leading-[1.6]`

---

## Color System

### Grayscale
```
#ffffff    — Pure White (text, emphasis)
#ececec    — Body Text
#d1d5db    — Primary Gray
#9ca3af    — Secondary Gray
#6b7280    — Tertiary Gray
#4b5563    — Dark Gray
#2a2a2a    — Border Gray
#1a1a1a    — Container Gray
#0f0f0f    — Pure Black (background)
```

### Accent Colors
```
Emerald:   #10b981 (primary action, success)
Cyan:      #06b6d4 (secondary, gradients)
Orange:    #f97316 (warnings, pending)
Red:       #ef4444 (danger, high-risk)
Green:     #22c55e (positive metrics)
Yellow:    #eab308 (info, demo mode)
```

---

## Component Patterns

### Card Container (Base)
```jsx
className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] 
           rounded-2xl border border-[#1a1a1a] 
           shadow-sm hover:border-[#2a2a2a] 
           transition-all"
```

### Button (Primary)
```jsx
className="px-4 py-2.5 rounded-xl 
           bg-emerald-600 hover:bg-emerald-500 
           text-white text-sm font-semibold 
           transition-all hover:shadow-lg 
           hover:shadow-emerald-600/30"
```

### Button (Secondary)
```jsx
className="px-4 py-2.5 rounded-xl 
           bg-[#2a2a2a] hover:bg-[#333] 
           text-gray-300 text-sm font-semibold 
           border border-[#3a3a3a] 
           transition-all"
```

### Icon Container
```jsx
className="p-2.5 rounded-xl 
           bg-emerald-500/15 
           text-emerald-400"
```

### Input Field
```jsx
className="bg-transparent text-white 
           placeholder-gray-600 
           text-sm outline-none 
           rounded-2xl"
```

---

## Chat Interface Specifics

### User Message Bubble
- **Background:** `#2a2a2a`
- **Border:** `#3a3a3a`
- **Max Width:** 85% on desktop, 95% on mobile
- **Border Radius:** `rounded-2xl`
- **Padding:** `px-6 py-3.5`

### Assistant Message
- **Max Width:** `max-w-3xl`
- **Icon:** 8×8 gradient circle, `emerald-400` to `teal-600`
- **Text Color:** `#d1d5db`
- **Line Height:** `leading-relaxed`

### Input Container
- **Width:** `max-w-4xl` centered
- **Background:** `#1e1e1e`
- **Focus Border:** `#3a3a3a`
- **Placeholder:** `text-gray-600`

---

## Empty State Design

### Elements
1. **Icon:** 80px × 80px gradient circle with glow
2. **Title:** 36-48px bold white text
3. **Subtitle:** 14px gray text, max-width 448px
4. **Action Cards:** 2×2 grid (or responsive)

### Card Styling
- **Background:** `#1a1a1a`
- **Border:** `#2a2a2a`
- **Hover:** Slight lift effect, border change to `#3a3a3a`
- **Icon Background:** Gradient with 20% opacity

---

## Modal & Dialog Patterns

### Risk Badge Styling
```jsx
// High Risk
className="bg-red-600/20 text-red-400 
           border border-red-500/30 
           rounded-full px-3 py-1 
           font-bold text-xs"

// Medium Risk
className="bg-orange-600/20 text-orange-400 
           border border-orange-500/30 
           rounded-full px-3 py-1 
           font-bold text-xs"
```

### Status Indicator
```jsx
// Connected
className="text-green-400 drop-shadow-[0_0_4px_rgba(34,197,94,0.6)]"

// Demo Mode
className="text-yellow-400 drop-shadow-[0_0_4px_rgba(234,179,8,0.6)]"
```

---

## Responsive Behavior

### Breakpoints (Tailwind)
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Grid Adjustments
```
Mobile:  grid-cols-1
Tablet:  md:grid-cols-2
Desktop: lg:grid-cols-4
```

### Font Scaling
```
Mobile:  text-xs, text-sm
Desktop: text-sm, text-base
```

---

## Animation Guidelines

### Loading States
```jsx
// Pulse (gentle breathing)
animate-pulse

// Bounce (falling dots)
animate-[bounce_1.4s_infinite_0ms]
animate-[bounce_1.4s_infinite_200ms]
animate-[bounce_1.4s_infinite_400ms]

// Spin (rotating)
animate-spin
```

### Transition Timing
- **Fast:** `duration-150` (hover states)
- **Normal:** `duration-200` (UI changes)
- **Smooth:** `duration-300` (complex transitions)

### Hover Effects
- **Lift:** `-translate-y-0.5`
- **Shadow:** `hover:shadow-lg`
- **Color:** `hover:text-gray-300`

---

## Accessibility Considerations

### Keyboard Navigation
- All buttons are tab-accessible
- Enter/Space to activate
- Shift+Enter in textarea for multi-line

### Color Contrast
- Text on dark bg: WCAG AA compliant
- Icon colors have sufficient contrast
- Status indicators use color + icon

### Focus States
- Focus ring on buttons: `focus:outline-none focus:ring-2`
- Clear visual feedback on all interactive elements

---

## Dark Mode (Future)

Current implementation is "always-dark" mode. For light mode:
- Invert colors: `#0f0f0f` ↔ `#ffffff`
- Use subtle shadows instead of borders
- Reduce glow effects
- Use lighter accent colors

---

## Implementation Checklist

- [x] Sidebar (collapsed & expanded)
- [x] Chat panel with empty state
- [x] Message rendering (user & assistant)
- [x] Input field with auto-resize
- [x] Dashboard with KPI cards
- [x] Charts with Recharts
- [x] Approval queue with risk levels
- [x] Loading states & animations
- [x] Responsive design
- [ ] Dark/Light mode toggle
- [ ] Accessibility audit

---

## Resources

- **Tailwind CSS:** https://tailwindcss.com
- **Lucide Icons:** https://lucide.dev
- **Recharts:** https://recharts.org
- **Design Reference:** https://www.chatgpt.com, https://claude.ai

