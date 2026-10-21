# NiyamSetu: UI/UX Design Document
## 1. Purpose

This document defines how NiyamSetu looks and behaves: visual style, layout system, components, screens per role and accessibility rules. It supports the PRD and the technical design, and the frontend (React, Vite, Tailwind CSS, Recharts) is built to follow it.

## 2. Design direction

NiyamSetu is a working tool for officers who spend hours in it, and for institution staff who open it only when something is due. The interface should be calm, readable and quick to scan. Colour is reserved for status, so a red or amber item stands out immediately.

Three decisions are fixed:

1. **Light theme only.** There is no dark mode and no theme switch. This keeps the status colours consistent, simplifies testing and suits printed reports and screen-shared demos.
2. **Liquid (fluid) layout.** Layouts stretch and shrink continuously with the viewport using fractions, percentages and `clamp()`. They do not jump between fixed-width designs.
3. **Responsive across devices.** The same screens work on a phone, tablet and widescreen monitor. The content reflows and changes shape, never just shrinks.

## 3. Design principles

1. **Status first.** The first thing a user sees is what is late, what is due soon and what needs their action.
2. **One obvious next step.** Each screen has one primary action.
3. **Show the reason.** Whenever the system raises an alert or an escalation, the screen says why, with the rule and the date.
4. **Officers decide.** Anything system-generated is labelled "Draft" or "Suggested" until a person confirms it.
5. **Consistency over decoration.** The same component looks and behaves the same everywhere.
6. **Plain language.** Short labels, no jargon beyond AICTE's own terms.

## 4. Light theme and colour system

The app always renders in light mode. The HTML declares `color-scheme: light` and the stylesheet contains no `prefers-color-scheme: dark` rules, so a device set to dark mode does not alter the app.

Colours are defined once as CSS variables and mapped into the Tailwind config.

### 4.1 Core palette

| Token | Value | Use |
|---|---|---|
| `--bg` | #F6F8FB | Page background |
| `--surface` | #FFFFFF | Cards, tables, panels |
| `--surface-alt` | #EEF2F7 | Table headers, subtle blocks |
| `--border` | #DDE3EC | Dividers and outlines |
| `--text` | #1B2433 | Main text |
| `--text-muted` | #5A6678 | Secondary text, hints |
| `--primary` | #1F4E8C | Primary buttons, links, active navigation |
| `--primary-hover` | #173D70 | Hover and pressed state |
| `--primary-tint` | #E6EEF8 | Selected rows, soft highlights |
| `--focus` | #2B6CD4 | Keyboard focus ring |

### 4.2 Status colours

Status colours are always paired with a text label or icon, never used alone.

| Status | Text/Icon | Tint background | Meaning |
|---|---|---|---|
| On track | #1E6B3A | #E5F4EA | Within timeline |
| Due soon (amber) | #8A5A00 | #FFF3D6 | 75% or more of timeline used |
| Overdue (red) | #B42318 | #FDE8E6 | Past the deadline |
| Information | #1F4E8C | #E6EEF8 | Neutral notices |
| On hold / inactive | #4B5565 | #EDEFF3 | Timeline paused or closed |

Escalation levels use the same red scale with increasing weight: L1 is outlined, L2 is tinted and L3 is solid.

### 4.3 Contrast

Body text on the page and surface backgrounds meets WCAG AA contrast (4.5:1). All status text and tint pairs above are chosen to meet AA. Large text and icons meet 3:1 as a minimum.

## 5. Typography

- **Typeface:** Inter, with a system sans-serif fallback. Noto Sans is added where Devanagari text is needed.
- **Fluid scale:** sizes use `clamp()` so type scales smoothly with the viewport.

| Role | Size | Weight |
|---|---|---|
| Page title | clamp(1.5rem, 1.2rem + 1.2vw, 2rem) | 600 |
| Section heading | clamp(1.125rem, 1rem + 0.5vw, 1.375rem) | 600 |
| Body | clamp(0.9375rem, 0.9rem + 0.2vw, 1rem) | 400 |
| Table and label text | 0.875rem | 400 / 500 |
| Caption and hints | 0.8125rem | 400 |
| Key figure on tiles | clamp(1.75rem, 1.4rem + 1.5vw, 2.5rem) | 600 |

Line height is 1.5 for body text and 1.25 for headings. Minimum body size on mobile is 15px.

## 6. Liquid layout system

### 6.1 Rules

- No fixed pixel widths on containers. Widths use `%`, `fr`, `minmax()` and `auto`.
- Page content sits in a container with `width: min(100% - 2rem, 90rem)`, centred. On very wide screens, content stops growing at 1440px so lines stay readable.
- Spacing is fluid too. Page padding is `clamp(1rem, 2vw, 2rem)`.
- Cards and tiles use auto-fit grids, so the number of columns follows the available width:

```css
.tile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
  gap: clamp(0.75rem, 1.5vw, 1.5rem);
}
```

- Images and charts are `max-width: 100%`. Charts resize with their container.
- Units are `rem` and `%`, never fixed `px`, except for borders and shadows.

### 6.2 Breakpoints

Breakpoints exist to change structure, not to switch between fixed layouts. Between them, the layout stays liquid.

| Name | From | Typical device | Structural change |
|---|---|---|---|
| xs | 0 | Small phones (360px and up) | Single column, bottom navigation |
| sm | 640px | Large phones | Two-column tiles where space allows |
| md | 768px | Tablets | Collapsible side navigation appears |
| lg | 1024px | Small laptops | Persistent side navigation, tables show full columns |
| xl | 1280px | Desktops | Side panels for filters and details |
| 2xl | 1536px | Wide monitors | More tiles per row, content capped at 1440px |

### 6.3 App shell

- **Phone:** top bar (logo, notifications, profile) with a bottom navigation bar holding the four or five most used sections. Everything else sits in a "More" menu.
- **Tablet:** a collapsible side drawer, closed by default.
- **Desktop:** a persistent left sidebar (about 16 rem wide, collapsible to icons only), a top bar with search, the notification bell and the profile menu, and a main content area that takes all remaining width.

The shell uses CSS Grid, so the main area expands to fill the space whichever navigation is shown.

## 7. Visual style

The style is clean and light, with soft depth, in keeping with a "liquid" feel without hurting readability.

- **Corner radius:** 12px on cards and panels, 8px on inputs and buttons, full round on badges and avatars.
- **Elevation:** cards use a very soft shadow (`0 1px 2px rgba(27,36,51,0.06), 0 4px 12px rgba(27,36,51,0.04)`) with a 1px border. Popovers and dialogs use a slightly stronger shadow.
- **Surfaces:** solid white. No transparency or blur on content areas, so text stays crisp and prints well.
- **Motion:** short, smooth transitions (150–250ms ease-out) for hover, expanding panels, drawers and number changes. Layout changes animate smoothly where it helps the user follow what happened. Motion is disabled when the user's device requests reduced motion.
- **Icons:** one outline icon set (Lucide), 20px by default, always paired with text for important actions.
- **Charts:** one primary blue for single-series data. Status colours are used only when the chart actually shows status. Every chart has a data table or text summary available.

## 8. Components

### 8.1 Buttons

- **Primary:** solid blue, one per screen area.
- **Secondary:** white with blue outline.
- **Tertiary:** text only.
- **Destructive:** solid red, used only for return, reject and similar, and always followed by a confirmation that asks for a reason.
- Minimum touch target 44 by 44px. Buttons have a visible loading state and are disabled while a request is running.

### 8.2 Status badge

A rounded label with a dot or icon and text, for example "Overdue · 6 days", "Due in 3 days", "On hold". Colours come from Section 4.2.

### 8.3 Summary tile

A card with a label, a large number, a small trend or context line, and a link into the filtered list. Tiles are clickable and keyboard focusable.

### 8.4 Data table

- Sticky header, sortable columns, a filter bar above and pagination below.
- Row height is comfortable by default, with a compact option for officers.
- On desktop, all columns are shown.
- On narrow screens, each row turns into a stacked card: title and status on top, key fields below, secondary fields behind an expand control. Horizontal scrolling is avoided for main lists.
- Bulk actions appear when rows are selected.

### 8.5 Filters

On desktop, filters sit in a bar above the table (Region, stage, route type, status, date range). On phones, they collapse into a "Filters" button that opens a bottom sheet. Active filters appear as removable chips.

### 8.6 Forms

- Labels above fields, never only placeholders.
- Inline validation with plain error text beneath the field.
- Required fields marked in text, not only with a symbol.
- Reason fields for return, reject and snooze are mandatory, with a minimum length and a character counter.
- File upload shows accepted types, size limit, progress and a preview of the file name before submit.
- Long forms are split into steps on mobile.

### 8.7 Timeline and history

A vertical list of events (stage, actor, date, reason) used on the application detail page. The current stage is highlighted, and returned steps show the reason in an indented note.

### 8.8 Alerts and notifications

- **Bell menu:** unread count, grouped by Today, This week and Earlier. Each item shows the event, the item concerned, the due date and one action.
- **Banners:** page-level notices for overdue or escalated items.
- **Toasts:** short confirmations such as "Application returned to institution".
- Acknowledge and snooze controls are available on each alert. Snoozing opens a small reason prompt.

### 8.9 Dialogs and sheets

Dialogs are used for confirmations that need a reason. On phones, they appear as bottom sheets. Focus is trapped inside, Escape closes them and focus returns to the trigger.

### 8.10 Empty, loading and error states

- **Loading:** skeleton shapes matching the final layout, not spinners over blank pages.
- **Empty:** a short sentence saying what is missing and what to do next.
- **Error:** what went wrong, whether data was lost and a retry button.

## 9. Navigation by role

| Role | Main sections |
|---|---|
| Institution | Home, My Applications, Undertakings, Documents, Notifications |
| Scrutiny Officer | My Queue, Applications, Notifications |
| Regional Officer | Dashboard, Applications, EVC, Undertakings, Documents, Reports |
| Bureau Officer | Dashboard, Regions, Escalations, Reports, Audit |
| Committee Member | My Cases, EVC Schedule, Notifications |
| Senior Authority | Escalations, Performance, Reports |
| Administrator | Users, Regions, Routes and Timelines, Rules, Templates, Scheduler, Audit |

The navigation shows only what the role can access. The server enforces the same permissions, so the interface never depends on hiding links alone.

## 10. Key screens

### 10.1 Login

Centred card on a plain light background with the NiyamSetu name, tagline, email and password fields and an OTP step for officers. The error messages do not reveal whether an email exists.

### 10.2 Regional Officer dashboard

- **Top row:** tiles for Open applications, Due soon, Overdue, EVCs pending and Documents expiring.
- **Ageing chart:** applications grouped by days in stage, coloured by status.
- **Stage pendency:** a bar chart showing counts per stage with the average dwell time against the allowed timeline.
- **Workload:** a ranked list of officers with open items.
- **Needs attention:** a short list of the oldest overdue items, each with the reason and a direct action.

### 10.3 Bureau Officer dashboard

A Region comparison view with a table and chart for pendency and on-time percentage, a bottleneck panel, and an escalations list ordered by level and age.

### 10.4 Institution home

A plain, uncluttered page. At the top, a "What needs your action" panel lists deficiencies to answer, undertakings due and documents expiring, each with a due date and a button. Below it, a status timeline for each application.

### 10.5 Application detail

- **Header:** reference number, institution, route type, current stage and status badge.
- **Main area:** tabs for Summary, History, Documents, EVC, Undertakings and Audit.
- **Side panel (desktop) or collapsible section (mobile):** current owner, time in stage against the timeline, next stage, and available actions (Advance, Return, Hold).
- The "Return" action opens a dialog with a mandatory reason.
- The case summary carries a "Draft" label until reviewed.

### 10.6 EVC queue and calendar

A list view and a calendar view of EVCs by Region. Each entry shows its status, due date and assigned members, with delayed items marked red. Scheduling uses a side panel with date, members and notes. The calendar collapses to an agenda list on phones.

### 10.7 Undertakings

A list grouped by status, with due dates and an evidence column. The detail page shows the condition, the deadline, submitted files and the review panel (Accept or Reject with remarks) for officers. Institutions see an upload area and the review result.

### 10.8 Document validity

Four tiles (Valid, Expiring soon, Expired, Renewal under verification) over a table sorted by expiry date. The detail page shows the alert schedule that has already fired and the next one due.

### 10.9 Escalations

A table of open escalations showing item, level, who it was raised to, how long it has been open and the reason. Resolution requires a note.

### 10.10 Reports

A report picker, filters and a preview table, with CSV and PDF export buttons. The figures are the same as on the dashboards.

### 10.11 Admin: rules and timelines

Editable tables for route stages, timelines, reminder intervals and escalation chains. Each change shows a "what will change" summary, is versioned and is written to the audit log. The scheduler page has a "Run now" button and, outside production, a simulated-date control. When a simulated date is active, a visible banner appears at the top of every page.

## 11. Responsive behaviour summary

| Element | Phone | Tablet | Desktop |
|---|---|---|---|
| Navigation | Bottom bar + More | Slide-in drawer | Persistent sidebar |
| Tiles | 1 column, auto-fit up | 2–3 columns | 4–5 columns |
| Tables | Stacked cards | Table with fewer columns | Full table |
| Filters | Bottom sheet | Inline bar | Inline bar or side panel |
| Detail page | Single column, collapsible sections | Single column with side summary | Two columns with side panel |
| Dialogs | Bottom sheet | Centred dialog | Centred dialog |
| Calendar | Agenda list | Week view | Month view |
| Charts | Simplified, scrollable legends | Full | Full with side legend |

## 12. Accessibility

The target is WCAG 2.1 AA, in line with government accessibility guidelines.

- Full keyboard operation, logical tab order and a visible focus ring on every interactive element.
- Semantic HTML with correct headings, landmarks, table headers and form labels.
- ARIA is used only where native elements fall short, for example live regions for toasts and new alerts.
- Status is never conveyed by colour alone. A label or icon is always present.
- Text can be resized to 200% without loss of content or function. The fluid layout supports this.
- Touch targets are at least 44px.
- Reduced-motion preference is respected.
- Charts have text alternatives and an accessible data table.
- Language attribute is set, and the interface is structured so that Hindi labels can be added later.

## 13. Content and tone

- Use sentence case for labels and headings.
- Buttons say what they do: "Return to institution", "Verify document", "Schedule visit".
- Dates are shown as 21 Oct 2026, with relative text beside them ("in 3 days", "6 days overdue").
- Alerts state the item, the rule and the action, for example "Lease for [Institution] expires in 30 days. Renewal not yet submitted."
- Error messages say what happened and what to do next.

## 14. Implementation notes

- Colours, spacing and radii are defined as CSS variables and exposed through the Tailwind config, so a change to the palette happens in one place.
- The document root sets `color-scheme: light` and the meta tag `<meta name="color-scheme" content="light">`. No dark variants are written.
- Layout uses Grid for the shell and tile areas and Flexbox inside components.
- Components are built once in a shared library (button, badge, tile, table, dialog, form fields) and reused by every screen.
- Recharts charts sit inside responsive containers.
- Print styles for reports remove navigation and use black text on white.

## 15. Design checks before demo

1. Test at 360, 768, 1024, 1440 and 1920 pixel widths, and drag the browser edge across the range to confirm nothing breaks between breakpoints.
2. Turn on dark mode in the operating system and confirm the app stays light.
3. Navigate each role's main flow with the keyboard only.
4. Run an automated accessibility check (axe or Lighthouse) on the main screens.
5. Zoom the browser to 200% and confirm the content is still usable.
6. Check that every red or amber item also shows text.

