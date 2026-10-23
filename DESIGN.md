---
name: Candor
description: Local job-application assistant; jobs read as a ranked league table with drawn threshold lines.
colors:
  green: "#0f3b2a"
  green-deep: "#0a2b1e"
  green-line: "#2d5c47"
  green-hover: "#164a35"
  on-green: "#f2f6f3"
  on-green-2: "#b6cdbf"
  yellow: "#f5c518"
  yellow-hover: "#e3b406"
  yellow-edge: "#c99f00"
  yellow-soft: "#fdf3c6"
  yellow-text: "#7a5c00"
  claret: "#7b1e3a"
  claret-soft: "#f7e8ed"
  claret-rule: "#d9b3bf"
  up: "#1b6a46"
  up-soft: "#e3f1ea"
  ground: "#f3f6f5"
  paper: "#ffffff"
  ink: "#121614"
  ink-2: "#44514d"
  ink-3: "#5c6865"
  rule: "#d4dcd9"
  rule-2: "#a9b6b1"
  zone-strong: "#fffcf0"
  zone-weak: "#f7f8f8"
typography:
  display:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "2.6rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.005em"
  headline:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.1
  title:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.03em"
  body:
    fontFamily: "'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "0.86rem"
    fontWeight: 600
    letterSpacing: "0.06em"
  field-label:
    fontFamily: "'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 600
  figure:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "1.45rem"
    fontWeight: 700
    fontFeature: "'tnum' 1, 'lnum' 1"
rounded:
  sm: "2px"
  md: "3px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "28px"
  gutter: "44px"
components:
  button-primary:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "42px"
  button-primary-hover:
    backgroundColor: "{colors.yellow-hover}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "42px"
  button-secondary-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "42px"
  button-quiet-hover:
    backgroundColor: "{colors.paper}"
  button-on-dark:
    backgroundColor: "transparent"
    textColor: "{colors.on-green}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "42px"
  button-on-dark-hover:
    backgroundColor: "{colors.on-green}"
    textColor: "{colors.green-deep}"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "9px 12px"
    height: "42px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.on-green-2}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "44px"
  nav-item-hover:
    backgroundColor: "{colors.green-hover}"
    textColor: "{colors.on-green}"
  nav-item-active:
    backgroundColor: "{colors.green-deep}"
    textColor: "{colors.on-green}"
  nav-badge:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    height: "22px"
  count-tab:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    padding: "4px 10px 5px"
  status-strong:
    backgroundColor: "{colors.up-soft}"
    textColor: "{colors.up}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  status-possible:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  status-set-aside:
    backgroundColor: "{colors.claret}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  form-chip:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    size: "24px"
  threshold-80-tag:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    padding: "1px 8px 2px"
  threshold-60-tag:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    padding: "1px 8px 2px"
---

# Design System: Candor

## Overview

**Creative North Star: "The Printed League Table"**

Candor looks like the results page of a sports paper: a ranked table of jobs with position numbers on the left, condensed figures, ruled rows, and lines drawn across the table at 80 and 60. A flat bottle-green rail holds the name and navigation; the work sits on a cool white ground. Colour is applied in large flat fields (the rail, the run panel, the mobile top bar) and in a small set of signals that each mean one thing: yellow for what to do next and the 80 line, claret for anything blocked or set aside, signal green for success and links.

Density is medium. Screens are built from ruled sections, tables and lists rather than cards. Every screen opens with a condensed uppercase heading and one plain sentence of status, then the main action. The run panel is the only place the green field carries running text; it reads as a log of what the assistant is doing, step by step.

The interface is light only (`color-scheme: light`). There is no dark theme.

**Key Characteristics:**
- Bottle-green rail and run panel as flat fields; no green tints on the work ground.
- Barlow Condensed for headings, table heads and every number; system sans for prose.
- Sections are a 2px ink top rule with an ink count tab, not boxed cards.
- The jobs table draws a yellow 80 line and an ink 60 line where the ranking crosses them.
- Each application shows its journey as a row of small square result chips (the form guide).
- Square-ish corners (2px and 3px), one-pixel rules, no shadows on the work ground.

## Colors

A deep green field, a cool white ground, near-black ink, and three signal colours with fixed meanings.

### Primary
- **Bottle Green** (green): the rail, the mobile top bar, and the run panel's inner surfaces. Always a full region, never an accent on white.
- **Deep Bottle Green** (green-deep): the run panel background and the current nav item.
- **Rail Rule Green** (green-line): one-pixel dividers and button borders inside green fields.
- **Rail Hover Green** (green-hover): hover fill for nav items and rail buttons.
- **Rail Text** (on-green) and **Rail Secondary Text** (on-green-2): text on green; the secondary tone is the resting nav colour and the engine status line.

### Secondary
- **Kit Yellow** (yellow): the primary button, nav count badges, the 80 threshold line and its number tag, the current run step, the current wizard step, the "ready" status, the "You do this" share of the time bar, text selection, and the focus ring inside green fields.
- **Kit Yellow Hover** (yellow-hover): primary button hover.
- **Yellow Edge** (yellow-edge): the one-pixel border on yellow fills (primary button, ready status, current wizard step, "you" time segment). It is a literal in `app.css`, not a custom property.
- **Yellow Wash** (yellow-soft): the "You do this" tag, the "what you do" note on an application, flags on the profile, and the selected application row.
- **Yellow Ink** (yellow-text): words that belong to the yellow family on a light ground (the 80 line's caption, profile flags). Yellow itself is never used for text on white.

### Tertiary
- **Claret** (claret): gate-fail and set-aside rows (title, score and position turn claret), the "Set aside" status, the reason line under a blocked job, inline errors, error toasts, the failed run state, and the "bad" form chip.
- **Claret Wash** (claret-soft) and **Claret Rule** (claret-rule): set-aside row background, rejected/withdrawn/no-response status fill and border.
- **Signal Green** (up) and **Signal Green Wash** (up-soft): "Strong fit" and "Qualified" status, done markers, the calm action row's top rule, links, the drop zone on hover, interview/hired chips, and the focus ring on light surfaces.

### Neutral
- **Cool Ground** (ground): page background behind everything.
- **Paper** (paper): tables, inputs, toasts, the dialog, the action row, secondary buttons.
- **Ink** (ink): text, section rules, count tabs, the 60 line, selected tabs and segments, form chips.
- **Ink Secondary** (ink-2) and **Ink Tertiary** (ink-3): supporting text, table heads, muted figures and timestamps.
- **Rule** (rule): row dividers and light borders. **Strong Rule** (rule-2): input borders, the drop zone's dashed border, placeholder-weight lines.
- **Strong-Fit Zone** (zone-strong) and **Weak-Fit Zone** (zone-weak): faint row backgrounds above the 80 line and below the 60 line in the jobs table. Both are literals in `app.css`.

### Named Rules
**The Flat Field Rule.** Bottle green appears only as a whole region (rail, top bar, run panel). On the white ground, green means success or a link and uses signal green, not bottle green.

**The Act-Now Yellow Rule.** Yellow marks the thing the person should act on or the line that decides drafting. It is never decoration, and it is never a text colour on white; yellow-family words use yellow ink.

**The Claret-Means-Blocked Rule.** Claret is reserved for blocked, set-aside, failed and rejected states, and always travels with words saying why.

## Typography

**Display Font:** Barlow Condensed 500/600/700, self-hosted woff2 (with Arial Narrow, sans-serif)
**Body Font:** Segoe UI (with system-ui, -apple-system, Helvetica Neue, Arial)
**Mono (incidental):** Consolas / Cascadia Mono, only in the Settings diagnostics block and inline code in the run panel.

**Character:** A tall condensed sports-print face for headings and figures, set against the plain Windows system sans for anything the person reads as sentences.

### Hierarchy
- **Display** (700, 2.6rem, line-height 1, uppercase): the page heading on every screen; on Today it is the date. 2.1rem below 860px.
- **Headline** (600, 1.75rem, line-height 1.1): the main action on Today. 1.5rem on mobile. Dialog and empty-state headings sit in the same family at 1.6 to 1.8rem.
- **Title** (600, 1.2rem, uppercase, 0.03em tracking): section headings beside the count tab, and collapsible section summaries.
- **Body** (400, 15px, line-height 1.55): all prose. Ledes run 1.08rem at up to 68ch; panel intros and notes cap at 62 to 72ch.
- **Label** (600, 0.86rem, uppercase, 0.06em tracking, condensed): table column heads, threshold captions, capacity labels, the speaker label in the run panel.
- **Field label** (600, 0.9rem, system sans): form labels and button text (buttons run 0.95rem).
- **Figure** (700, tabular and lining figures, condensed): every number. Scores 1.45rem, the Today action number 3rem, the setup time estimate 3.2rem, position numbers 1.15rem in ink-3.

### Named Rules
**The Condensed Figures Rule.** Every number (scores, positions, counts, dates, durations) is set in Barlow Condensed with tabular lining figures so columns align.

**The Uppercase-Is-Structure Rule.** Uppercase appears only in the condensed face for headings, table heads and captions. Prose and buttons stay sentence case in the system sans.

## Layout

Desktop is a CSS grid shell: a 232px sticky rail, a fluid main column, and, while a run is active, a 384px sticky run panel on the right. Main has 36px top and 44px side padding and a 1180px maximum width for its content stack, which spaces sections 28px apart.

Main is a size container, so screen layouts respond to the space left after the rail and run panel, not to the viewport:
- At 1080px of main width or more, Today splits into two columns (actions on the left, the strong-fits table preview on the right) with a 36px gap.
- At 900px or more, Profile splits into two columns.
- Below 1000px, the jobs table drops the location, board and posted columns and moves the location under the job title.
- Below 640px, each job becomes a wrapped two-line entry instead of a table row, with no sideways scrolling.

Below 860px viewport width the rail becomes a 56px green top bar with a menu button and an Ask button; the rail slides in from the left as a drawer, and the run panel becomes a bottom sheet up to 78vh tall. Main padding drops to 22px/16px with 120px at the bottom to clear the sheet.

Spacing is not tokenised in CSS. The values that recur are 4, 8, 12, 16 and 28px, with 44px as the desktop gutter. Interactive targets are 40 to 44px tall.

## Elevation & Depth

The work ground is flat. Depth comes from colour fields (green beside white), ink rules, and paper-white surfaces sitting on the cool ground. Shadows appear only on things that float over the page.

### Shadow Vocabulary
- **Floating panel** (`box-shadow: 0 8px 24px rgba(10, 43, 30, 0.28)`): the minimised run panel docked at the bottom right.
- **Bottom sheet** (`box-shadow: 0 -8px 24px rgba(10, 43, 30, 0.25)`): the run panel on mobile.
- **Drawer scrim** (`box-shadow: 0 0 0 100vmax rgba(10, 43, 30, 0.4)`): dims the page behind the open mobile rail. The ask dialog uses the same green-black at 0.5 as its backdrop.

### Named Rules
**The Flat Ground Rule.** Nothing on the work ground casts a shadow. A surface earns a shadow only when it floats above the page (minimised panel, bottom sheet, drawer).

## Shapes

Corners are nearly square: 3px on buttons, nav items, tabs, the drop zone and the dialog; 2px on inputs, status labels, chips, badges and tags. The engine dot is the only circle. Borders are one pixel, except section tops and table heads (2px ink), the dialog and confirm box (2px ink), and the drop zone (2px dashed). Segmented controls and the capacity bar butt their items edge to edge with shared borders. "Not yet" and weak states use dashed borders.

## Components

### Buttons
Plain, firm, and labelled with a verb.
- **Shape:** nearly square (3px), 42px tall, 18px side padding; small size is 40px tall with 12px padding.
- **Primary:** kit yellow with ink text and a yellow-edge border. One per view, for the next action.
- **Secondary:** paper with a 1px ink border; inverts to ink on hover. Used for row actions such as Prepare.
- **Quiet:** transparent with a strong-rule border; border turns ink and fill turns paper on hover.
- **On dark:** transparent with a rail-secondary border inside green fields; fills with rail text on hover.
- **Hover / Focus:** 160ms colour transitions; 1px press-down on active. Focus is a 3px signal-green outline offset 2px (yellow inside green fields).
- **Disabled:** 45% opacity, with a short reason line beneath where the build supplies one.

### Status labels and badges
- **Style:** small 2px-cornered labels, 0.82rem semibold, 1px border.
- **Variants:** strong/qualified in signal-green wash; possible on paper; weak, not drafted and unresolved transparent with a dashed border; set aside solid claret; applied solid ink; ready solid yellow; interview and hired solid signal green; rejected, withdrawn, no response and offer declined in claret wash.
- **Nav badge:** a yellow block with an ink condensed count, shown only when there is something to act on.

### Sections (in place of cards)
- **Structure:** a 2px ink top rule; the condensed uppercase title sits under it on the left and an ink count tab hangs from it on the right.
- **Background:** none; contents sit on the ground, with tables and lists on paper.
- **Exception:** Settings shows engine status as 1px-bordered paper boxes (signal green border when working, claret when not), and radio choices as bordered rows that gain an inset ink ring when selected.

### Inputs / Fields
- **Style:** paper fill, 1px strong-rule border, 2px corners, 42px minimum height, 9px/12px padding. Labels sit above in field-label type.
- **Hover / Focus:** border darkens to ink-3 on hover; focus adds a 3px signal-green outline flush to the edge and an ink border.
- **Error:** an inline claret-on-claret-wash message block below the field.
- **Segmented choice:** edge-to-edge ink-bordered segments; the selected one fills ink.
- **Drop zone:** 2px dashed strong-rule border on paper; turns signal green with a green wash on hover or drag-over.

### Navigation
- **Rail:** wordmark in 700 condensed uppercase at 2.35rem with the promise line beneath, then nav items 44px tall in rail-secondary text. Hover fills rail-hover green; the current page fills deep green, its text brightens and its icon turns yellow. An outlined Ask button and the engine and privacy lines sit below; the engine dot pulses yellow while work runs.
- **Mobile:** a 56px green top bar with menu, small wordmark and Ask; the rail becomes a drawer.
- **Tabs (document viewer):** a 2px ink baseline; the selected tab is a solid ink block with paper text.

### League Table (signature)
The jobs ranking. Ink-ruled column heads in condensed uppercase, a paper body, 1px rule between rows, position and score as condensed figures. Rows above 80 sit on the strong-fit zone, rows below 60 on the weak-fit zone, and set-aside rows on claret wash with their title and score in claret and the reason written underneath. Threshold rows draw a full-width 3px yellow line tagged "80" and a 2px ink line tagged "60", each with a condensed caption, and are drawn only where the ranking crosses them. Today reuses the table in a compact four-column form.

### Form Guide Chips (signature)
Each application's stages as a row of 24px ink squares with a condensed initial (F, D, S, I, O). Interview and offer chips are signal green, a hire is yellow, a rejection is claret, and stages not yet reached are dashed empty squares. A legend explains the letters, and the detail view shows the same chips at full width with the stage names spelled out.

### Capacity Bar
On an application's detail: the page budget as edge-to-edge ink-bordered blocks (filled ink when used), and the time split as joined segments, the assistant's share in signal-green wash and the person's share in yellow.

### Run Panel
A deep-green column (or bottom sheet) headed by an uppercase condensed title and a status label: deep green while running, yellow when it needs an answer, claret when failed, light when done. Steps list below with small square markers, filled when done and a pulsing yellow marker for the current step, which flashes a brief yellow wash as it arrives. Assistant messages carry a small condensed speaker label; the person's reply area sits in a bordered green box. It can minimise to a floating bar.

### Toasts and Dialog
Toasts are paper boxes with a 1px ink border, top right, sliding down 6px in 220ms; error toasts are solid claret. The Ask dialog is paper with a 2px ink border, a display-face heading, and a green-black backdrop.

## Do's and Don'ts

### Do:
- **Do** set every number in Barlow Condensed with tabular lining figures.
- **Do** open each section with the 2px ink rule and an ink count tab.
- **Do** keep one yellow primary button per view, on the next thing the person should do.
- **Do** write the reason next to anything claret: a set-aside job, a failed run, a rejection.
- **Do** draw the 80 and 60 lines only where the ranking crosses them.
- **Do** keep targets 40 to 44px tall and keep the 3px focus ring visible (yellow on green, signal green on light).
- **Do** let layout respond to main's width through the container queries, so an open run panel reflows the screen.

### Don't:
- **Don't** use bottle green as an accent on the white ground; use signal green for success and links.
- **Don't** set yellow text on white or paper; use yellow ink.
- **Don't** wrap sections in shadowed or rounded cards.
- **Don't** add shadows to anything that does not float over the page.
- **Don't** use claret for emphasis or decoration.
- **Don't** set prose or button labels in uppercase or in the condensed face.
