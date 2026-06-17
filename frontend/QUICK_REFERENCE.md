# Quick Component Reference Guide

## Common Tailwind Classes Used

### Backgrounds
```jsx
// Cards
bg-gradient-to-br from-[#1a1a1a] to-[#121212]
bg-[#0f0f0f]
bg-[#1a1a1a]
bg-[#1e1e1e]

// Hover states
hover:bg-[#1e1e1e]
hover:bg-[#222]
hover:bg-[#333]
```

### Borders
```jsx
// Borders
border border-[#1a1a1a]
border border-[#2a2a2a]
border border-[#3a3a3a]

// Hover borders
hover:border-[#2a2a2a]
hover:border-[#3a3a3a]

// Focus borders
focus-within:border-[#3a3a3a]
```

### Rounded Corners
```jsx
rounded-lg      // 8px
rounded-xl      // 12px
rounded-2xl     // 16px
rounded-full    // 50%
```

### Padding & Spacing
```jsx
// Padding
p-4, p-5, p-6
px-4, px-6      // horizontal
py-3, py-4      // vertical

// Margins
mb-2, mb-4, mb-6, mb-8
mt-1, mt-2, mt-3
ml-2, mr-auto

// Gaps
gap-1, gap-2, gap-3, gap-4
```

### Typography
```jsx
// Sizes
text-xs         // 12px
text-sm         // 14px
text-base       // 16px
text-lg         // 18px
text-2xl        // 24px
text-3xl        // 30px

// Weights
font-normal     // 400
font-medium     // 500
font-semibold   // 600
font-bold       // 700

// Colors
text-white
text-gray-300
text-gray-400
text-gray-500
text-gray-600

// Styling
tracking-tight  // -0.015em
tracking-wide   // 0.025em
leading-relaxed // 1.75
```

### Flexbox & Grid
```jsx
// Flex
flex
flex-1
flex-col
flex-shrink-0

// Items alignment
items-start
items-center
items-end

// Justification
justify-start
justify-center
justify-between

// Grid
grid
grid-cols-1
md:grid-cols-2
lg:grid-cols-4
gap-4
gap-6
```

### Shadows & Effects
```jsx
shadow-sm
shadow-lg
shadow-emerald-500/30
drop-shadow-[0_0_4px_rgba(34,197,94,0.6)]
```

### Transitions & Animations
```jsx
transition-all
transition-colors
duration-150
duration-200
duration-300

animate-pulse
animate-spin
animate-[bounce_1.4s_infinite_0ms]
```

---

## Component Templates

### Primary Button
```jsx
<button className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-all hover:shadow-lg hover:shadow-emerald-600/30">
  {text}
</button>
```

### Secondary Button
```jsx
<button className="px-4 py-2.5 rounded-xl bg-[#2a2a2a] hover:bg-[#333] text-gray-300 text-sm font-semibold border border-[#3a3a3a] transition-all">
  {text}
</button>
```

### Card Container
```jsx
<div className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] rounded-2xl border border-[#1a1a1a] shadow-sm hover:border-[#2a2a2a] transition-all p-6">
  {content}
</div>
```

### Badge
```jsx
<span className="text-xs px-3 py-1 rounded-full font-bold bg-orange-600/20 text-orange-400 border border-orange-500/30">
  {label}
</span>
```

### Icon Container
```jsx
<div className="w-11 h-11 rounded-xl flex items-center justify-center bg-emerald-500/15 text-emerald-400">
  <Icon size={20} strokeWidth={1.5} />
</div>
```

### Text Input
```jsx
<textarea
  className="w-full bg-transparent text-white text-sm pl-5 pr-14 py-4 resize-none outline-none placeholder-gray-600 max-h-[160px] rounded-2xl"
  placeholder="Message FinOps Copilot..."
/>
```

### Loading Spinner (3 dots)
```jsx
<div className="flex gap-1.5">
  <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_0ms]"></div>
  <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_200ms]"></div>
  <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_400ms]"></div>
</div>
```

### Status Badge (Connected/Demo)
```jsx
// Connected
<CircleDot size={10} className="text-green-400 drop-shadow-[0_0_3px_rgba(34,197,94,0.6)]" />

// Demo Mode
<CircleDot size={10} className="text-yellow-400 drop-shadow-[0_0_3px_rgba(234,179,8,0.6)]" />
```

---

## Responsive Patterns

### Responsive Padding
```jsx
px-4 sm:px-6        // 16px → 24px
py-4 sm:py-6        // 16px → 24px
```

### Responsive Grid
```jsx
grid-cols-1 md:grid-cols-2 lg:grid-cols-4
gap-4 md:gap-6
```

### Responsive Typography
```jsx
text-sm sm:text-base
text-3xl sm:text-4xl
```

### Responsive Containers
```jsx
max-w-2xl           // tablet max
max-w-4xl           // standard max
max-w-7xl           // dashboard max
```

---

## State Combinations

### Button States
```jsx
// Normal
bg-emerald-600 text-white

// Hover
hover:bg-emerald-500

// Focus
focus:ring-2 focus:ring-emerald-500/50

// Disabled
disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed

// Combined
"transition-all duration-200 hover:shadow-lg disabled:opacity-50"
```

### Card States
```jsx
// Normal
border border-[#1a1a1a]

// Hover
hover:border-[#2a2a2a]

// Combined
"transition-all hover:shadow-lg hover:border-[#2a2a2a]"
```

---

## Color Reference Quick Map

```
Emerald (Primary):
  100: #d1fae5
  300: #6ee7b7
  400: #34d399
  500: #10b981
  600: #059669
  700: #047857

Gray (Text):
  300: #d1d5db (light text)
  400: #9ca3af (muted)
  500: #6b7280 (secondary)
  600: #4b5563 (tertiary)
  700: #374151

Orange (Warning):
  400: #fb923c
  500: #f97316
  600: #ea580c

Red (Error):
  400: #f87171
  500: #ef4444

Green (Success):
  400: #4ade80
  500: #22c55e
```

---

## Useful Utilities

### Center Content
```jsx
flex items-center justify-center
```

### Flex Space Between
```jsx
flex items-center justify-between
```

### Stack Items
```jsx
flex flex-col gap-4
```

### Grid of Items
```jsx
grid grid-cols-3 gap-4
```

### Truncate Text
```jsx
truncate
overflow-ellipsis
```

### Hide on Mobile
```jsx
hidden md:block
```

### Full Width Child
```jsx
flex-1 min-w-0
```

---

## Animation Timings

| Duration | Class |
|----------|-------|
| 150ms | `duration-150` |
| 200ms | `duration-200` |
| 300ms | `duration-300` |
| 500ms | `duration-500` |

---

## Lucide Icon Sizing

```jsx
size={12}   // xs
size={14}   // sm
size={16}   // md
size={18}   // base
size={20}   // lg
size={24}   // xl
size={32}   // 2xl

strokeWidth={1}     // thin
strokeWidth={1.5}   // normal
strokeWidth={2}     // bold
```

---

## Copy-Paste Ready Snippets

### Empty State Container
```jsx
<div className="flex-1 flex flex-col items-center justify-center px-4 pb-[160px]">
  <div className="w-full max-w-[900px] mx-auto flex flex-col items-center">
    {/* content */}
  </div>
</div>
```

### Sticky Header
```jsx
<div className="flex-shrink-0 sticky top-0 z-20 flex items-center justify-between px-6 py-4 border-b border-[#2a2a2a]/50 bg-[#0f0f0f]/80 backdrop-blur-sm">
  {/* content */}
</div>
```

### Scrollable Content
```jsx
<div className="flex-1 overflow-y-auto">
  <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-8">
    {/* content */}
  </div>
</div>
```

### Footer Sticky
```jsx
<div className="flex-shrink-0 bg-gradient-to-t from-[#0f0f0f] via-[#0f0f0f]/95 to-[#0f0f0f]/0 border-t border-[#1a1a1a] px-4 pt-6 pb-6">
  {/* content */}
</div>
```

---

## Debugging Tips

### Show Element Bounds
```jsx
className="border border-red-500"  // temporary
```

### Check Spacing
```jsx
className="bg-yellow-500/20"  // temporary
```

### Verify Alignment
```jsx
className="text-center"  // check if centered
```

### Test Responsiveness
- Open DevTools (F12)
- Toggle device toolbar (Ctrl+Shift+M)
- Test at: 375px (mobile), 768px (tablet), 1024px (desktop)

