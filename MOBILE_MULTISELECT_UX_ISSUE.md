# Mobile Multiselect Dropdown UX Issue - Context for Review

**Date**: October 19, 2025
**Component**: MultiCombobox (Boats & Species filters)
**Platform**: Mobile (iOS/Android)
**Severity**: Medium - UX friction prevents efficient filtering

---

## Problem Statement

Users cannot easily apply multiselect filters on mobile devices. The current implementation requires users to **tap outside the dropdown** to close it and apply selections, which is difficult on mobile due to:

1. **No visual "Apply" button** - users don't know how to confirm their selections
2. **Small tap target outside dropdown** - limited screen space makes "tap outside" unreliable
3. **Unintuitive close mechanism** - no clear affordance for completing the action
4. **Accidental dismissals** - users may close dropdown without realizing selections aren't applied

---

## Current Implementation

### Architecture

**File**: `src/components/ui/multi-combobox.tsx` (132 lines)

**Component**: `MultiCombobox` - shadcn/ui based multiselect dropdown

**Key behavior**:
```tsx
const handleOpenChange = (isOpen: boolean) => {
  setOpen(isOpen)

  // When closing, apply the filters
  if (!isOpen && onApply) {
    onApply(pendingValues)
  }
}
```

**Flow**:
1. User taps "All Boats" or "All Species" trigger button
2. Popover opens with searchable list
3. User taps items to select/deselect (checkmarks appear)
4. **NO APPLY BUTTON** - user must tap outside to close
5. `onOpenChange(false)` fires when popover closes
6. `onApply(pendingValues)` is called with selections
7. Filters update, data refreshes

### Usage Context

**File**: `src/components/HeaderFilters.tsx` (lines 354-377)

```tsx
{/* Boat Filter */}
<MultiCombobox
  options={availableBoats}
  values={pendingBoats}
  onValuesChange={setPendingBoats}
  onApply={(values) => onFiltersChange({ ...filters, boat: values })}
  placeholder="All Boats"
  searchPlaceholder="Search boats..."
  className="h-8 w-full md:w-[200px]"
/>

{/* Species Filter */}
<MultiCombobox
  options={availableSpecies}
  values={pendingSpecies}
  onValuesChange={setPendingSpecies}
  onApply={handleSpeciesApply}
  placeholder="All Species"
  searchPlaceholder="Search species..."
  className="h-8 w-full md:w-[200px]"
/>
```

**Pending state management**:
- `pendingBoats` / `pendingSpecies` - local state for selections in dropdown
- Only committed to actual filters when dropdown closes
- Visual chips update immediately for feedback (`onValuesChange`)
- But data doesn't refresh until `onApply` is called

---

## Mobile UX Problems (Detailed)

### 1. **No Visual Confirmation Mechanism**

**Issue**: Users don't see a clear "Done" or "Apply" button

**User impact**:
- Confusion about how to confirm selections
- Trial-and-error tapping to figure out close mechanism
- Frustration when nothing happens after selecting items

**Example user flow**:
```
User: *taps "All Boats"*
User: *searches "Polaris"*
User: *taps "Polaris Supreme" ✓*
User: *waits... nothing happens*
User: *looks for Apply button... doesn't find one*
User: *taps "Polaris Supreme" again thinking it didn't work*
User: *now it's deselected ✗*
User: *confused, gives up*
```

### 2. **Small Tap Target Outside Dropdown**

**Issue**: On mobile, the area outside the dropdown is small

**Layout breakdown**:
- Filter bar takes full width on mobile (`w-full`)
- Popover dropdown: 300px width (`w-[300px]`)
- On 375px iPhone: only ~37px on each side to tap
- On 414px Android: only ~57px on each side to tap

**User impact**:
- Hard to accurately tap outside on small screens
- Accidental taps inside dropdown deselect items
- Users may tap browser chrome/status bar thinking it's "outside"

### 3. **Unintuitive Interaction Pattern**

**Issue**: "Tap outside to close" is not standard for mobile multiselect

**Industry standards comparison**:

| Platform | Multiselect Pattern | Apply Mechanism |
|----------|-------------------|----------------|
| **Material Design 3** | Bottom sheet with checkboxes | "Done" button in header |
| **iOS HIG** | Modal with list | "Done" button top-right |
| **Stripe Dashboard** | Dropdown with footer | "Apply Filters" button at bottom |
| **Linear** | Popover with footer | "Apply" button in footer |
| **Amplitude** | Modal picker | "Save" button at bottom |

**Our current pattern**: Tap outside to close (uncommon for mobile multiselect)

### 4. **Lost Context on Accidental Dismissals**

**Issue**: If user taps outside accidentally, dropdown closes immediately

**User impact**:
- Loses search context (search term cleared)
- Loses scroll position in long lists
- Has to start selection process over
- No "cancel" option to discard changes

---

## Technical Architecture

### Component Hierarchy

```
HeaderFilters.tsx
  ├─ MultiCombobox (Boats)
  │   ├─ Popover
  │   │   ├─ PopoverTrigger (Button with badge)
  │   │   └─ PopoverContent
  │   │       └─ Command (shadcn command palette)
  │   │           ├─ CommandInput (search)
  │   │           └─ CommandList
  │   │               └─ CommandItem (each option with checkbox)
  │   └─ State:
  │       ├─ open (boolean)
  │       ├─ pendingValues (string[])
  │       └─ search (string)
  └─ MultiCombobox (Species)
      └─ [same structure]
```

### State Flow

```
1. User opens dropdown:
   setOpen(true) → PopoverContent renders

2. User selects item:
   handleSelect(option) → setPendingValues([...values, option])
                        → onValuesChange(newValues) [updates chips]

3. User taps outside:
   handleOpenChange(false) → setOpen(false)
                           → onApply(pendingValues) [applies filters]
                           → parent state updates
                           → API call refreshes data
```

### Key Code Sections

**Trigger button** (lines 74-94):
```tsx
<Button variant="outline" role="combobox">
  {pendingValues.length === 0 ? (
    <span className="text-muted-foreground">{placeholder}</span>
  ) : (
    <Badge variant="secondary">{pendingValues.length} selected</Badge>
  )}
  <ChevronsUpDown className="ml-2 h-4 w-4" />
</Button>
```

**Popover content** (lines 95-129):
- Fixed width: `w-[300px]` (doesn't adapt to mobile screen size)
- No footer with action buttons
- No "Apply" or "Cancel" buttons
- Relies on Popover's `onOpenChange` to detect close

**Apply logic** (lines 58-65):
```tsx
const handleOpenChange = (isOpen: boolean) => {
  setOpen(isOpen)

  // When closing, apply the filters
  if (!isOpen && onApply) {
    onApply(pendingValues)
  }
}
```

---

## Proposed Solutions (For Team Discussion)

### Option 1: Add Footer with Apply/Cancel Buttons (Recommended)

**Changes**:
```tsx
<PopoverContent className="w-[300px] p-0">
  <Command shouldFilter={false}>
    <CommandInput placeholder={searchPlaceholder} />
    <CommandList>
      {/* ... options ... */}
    </CommandList>
  </Command>

  {/* NEW: Footer with action buttons */}
  <div className="border-t p-2 flex gap-2">
    <Button
      variant="outline"
      size="sm"
      className="flex-1"
      onClick={() => {
        setPendingValues(values) // Revert to original
        setOpen(false)
      }}
    >
      Cancel
    </Button>
    <Button
      size="sm"
      className="flex-1"
      onClick={() => {
        onApply?.(pendingValues)
        setOpen(false)
      }}
    >
      Apply ({pendingValues.length})
    </Button>
  </div>
</PopoverContent>
```

**Pros**:
- Clear visual affordance for confirmation
- Standard mobile pattern (matches industry)
- Cancel button allows discarding changes
- Apply button shows selection count
- No behavior change on desktop

**Cons**:
- Slightly taller popover (adds ~48px footer)
- Two-step interaction (select + apply)

**Mobile UX improvements**:
- ✅ Clear "Apply" button with selection count
- ✅ "Cancel" button to discard changes
- ✅ No need to tap outside
- ✅ Prevents accidental dismissals

---

### Option 2: Switch to Bottom Sheet on Mobile

**Changes**:
```tsx
// Use Popover on desktop, Sheet (bottom drawer) on mobile
const isMobile = useMediaQuery('(max-width: 768px)')

{isMobile ? (
  <Sheet open={open} onOpenChange={handleOpenChange}>
    <SheetTrigger asChild>
      <Button>...</Button>
    </SheetTrigger>
    <SheetContent side="bottom" className="h-[80vh]">
      <SheetHeader>
        <SheetTitle>{placeholder}</SheetTitle>
      </SheetHeader>
      <Command>...</Command>
      <SheetFooter>
        <Button variant="outline" onClick={handleCancel}>Cancel</Button>
        <Button onClick={handleApply}>Apply ({count})</Button>
      </SheetFooter>
    </SheetContent>
  </Sheet>
) : (
  <Popover>...</Popover>
)}
```

**Pros**:
- Native mobile pattern (bottom drawers)
- More screen space for long lists
- Clear header and footer context
- Easier to dismiss (swipe down)

**Cons**:
- More complex implementation
- Separate mobile/desktop code paths
- Requires media query hook
- Different UX on mobile vs desktop

**Mobile UX improvements**:
- ✅ Full-height drawer for better visibility
- ✅ Native swipe-to-dismiss gesture
- ✅ Clear header with title
- ✅ Footer with Apply/Cancel buttons

---

### Option 3: Auto-Apply on Selection (Simplest)

**Changes**:
```tsx
const handleSelect = (option: string) => {
  const newValues = pendingValues.includes(option)
    ? pendingValues.filter((v) => v !== option)
    : [...pendingValues, option]

  setPendingValues(newValues)
  onValuesChange(newValues)
  onApply?.(newValues) // AUTO-APPLY immediately
}
```

**Pros**:
- Simplest implementation (1 line change)
- No UI changes needed
- Immediate feedback (data refreshes instantly)
- No need for Apply button

**Cons**:
- API call on every selection (performance impact)
- No way to "try out" selections before applying
- Can't batch multiple selections
- Jarring UX if data refresh is slow

**Mobile UX improvements**:
- ✅ No need to close dropdown
- ✅ Immediate results
- ⚠️ May cause UI jank if API is slow

---

## 2025 Mobile UX Best Practices

### Industry Standards for Mobile Multiselect

**Material Design 3** (Google):
- Use bottom sheets for mobile pickers
- Include "Done" button in header or footer
- Show selection count in trigger button
- Support swipe-to-dismiss gesture

**iOS Human Interface Guidelines** (Apple):
- Use modal sheets for pickers
- "Done" button in top-right of navigation bar
- "Cancel" button in top-left
- Show checkmarks for selected items

**Web Best Practices** (Stripe, Linear, Amplitude):
- Add footer with "Apply" and "Cancel" buttons
- Show selection count in Apply button text
- Keep dropdown open during selection
- Provide clear visual feedback for selections

### Accessibility Considerations

**Current issues**:
- No ARIA live region announces applied filters
- No keyboard shortcut to apply (Enter key doesn't work)
- No visual feedback when filters are applied
- Screen readers don't announce "tap outside to close"

**Recommended improvements**:
- Add `aria-label` to Apply button: "Apply 3 selected boats"
- Add live region: "Filters applied: Polaris Supreme, Dolphin, Excel"
- Support Enter key to apply, Escape to cancel
- Add loading state during API call

---

## Implementation Recommendations

### Priority: **Option 1** (Footer with Apply/Cancel buttons)

**Rationale**:
- Matches 2025 industry standards
- Low implementation complexity
- Works well on both mobile and desktop
- Provides clear affordance for confirmation
- Allows cancel/discard functionality

**Implementation steps**:
1. Update `MultiCombobox` to include footer section
2. Add Apply and Cancel buttons to footer
3. Update `handleOpenChange` logic to not auto-apply
4. Move apply logic to Apply button click handler
5. Add Cancel button to revert pending changes
6. Test on mobile devices (iOS Safari, Chrome Android)

**Estimated effort**: 2-3 hours

**Files to modify**:
- `src/components/ui/multi-combobox.tsx` (add footer, update handlers)
- `src/components/HeaderFilters.tsx` (no changes needed)

---

## Visual Mockup (Option 1)

```
┌─────────────────────────────────────┐
│ 🔍 Search boats...                  │
├─────────────────────────────────────┤
│ ✓ Polaris Supreme                   │
│ ✓ Dolphin                            │
│   Excel                              │
│   Fortune                            │
│   Tribute                            │
│   (... more boats ...)               │
├─────────────────────────────────────┤
│ [  Cancel  ]  [  Apply (2)  ]       │ ← NEW FOOTER
└─────────────────────────────────────┘
```

---

## Testing Checklist

### Desktop
- [ ] Apply button works
- [ ] Cancel button reverts changes
- [ ] Selection count updates in Apply button
- [ ] Keyboard shortcuts work (Enter/Escape)
- [ ] Popover closes after Apply
- [ ] Popover closes after Cancel

### Mobile (iOS)
- [ ] Footer buttons are easily tappable (44px min height)
- [ ] Apply button works on Safari
- [ ] Cancel button works on Safari
- [ ] Scrolling list doesn't dismiss popover
- [ ] Selection count visible in button

### Mobile (Android)
- [ ] Footer buttons work on Chrome
- [ ] No layout issues on small screens (320px)
- [ ] No z-index issues with browser chrome

### Accessibility
- [ ] Screen reader announces Apply button with count
- [ ] Screen reader announces selections
- [ ] Keyboard navigation works
- [ ] Focus management correct (closes → focus returns to trigger)

---

## Questions for Other Team

1. **Does Option 1 (footer with buttons) align with your design system?**
2. **Should we implement Option 2 (bottom sheet) for a more native mobile experience?**
3. **Are there brand guidelines for filter interaction patterns?**
4. **Should Apply button be primary color or stay outline variant?**
5. **Do you want loading state shown during filter application?**
6. **Should we add animation when filters are applied?**
7. **Any concerns about the additional height from footer (~48px)?**

---

## Related Components

This issue affects:
- **Boat filter** (MultiCombobox in HeaderFilters)
- **Species filter** (MultiCombobox in HeaderFilters)

Does NOT affect:
- **Date range selector** (uses Select with presets, no multiselect)
- **Trip duration filter** (single select dropdown)

---

## References

- **Component file**: `src/components/ui/multi-combobox.tsx`
- **Usage file**: `src/components/HeaderFilters.tsx`
- **Design system**: shadcn/ui (Popover, Command, Button components)
- **Current behavior**: Filters apply on popover close (tap outside)
- **Proposed behavior**: Filters apply on Apply button click

---

**Document prepared by**: Claude Code
**For review by**: [Other Team Name]
**Next steps**: Await feedback, implement approved solution, test on devices
