# UX Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Design Philosophy

The platform serves two very different user groups with opposing needs:

| User | Context | Need |
|------|---------|------|
| Citizen | Mobile, multilingual, low-tech comfort | Simple, fast, native-language signal submission |
| Policymaker | Desktop, high-stakes, time-limited | Dense, evidence-grounded, actionable intelligence |

The UX must make the AI reasoning **understandable without technical knowledge** and the evidence **trustworthy without domain expertise**.

---

## 2. Design System

### 2.1 Visual Identity

**Palette:** Governance Dark + Trust Blue

```css
/* Primary tokens */
--color-bg-base:       #0A0F1E;   /* Deep navy -- authority */
--color-bg-surface:    #111827;   /* Raised surfaces */
--color-bg-card:       #1C2435;   /* Cards and panels */
--color-border:        #2D3748;   /* Subtle borders */

--color-primary:       #3B82F6;   /* Trust blue */
--color-primary-hover: #60A5FA;
--color-accent:        #10B981;   /* Evidence green */
--color-warning:       #F59E0B;   /* Partial/conflict amber */
--color-critical:      #EF4444;   /* Missing data / critical priority */
--color-synthetic:     #8B5CF6;   /* Purple -- synthetic data marker */

/* Text */
--color-text-primary:  #F9FAFB;
--color-text-secondary:#9CA3AF;
--color-text-muted:    #6B7280;
```

**Typography:**
- Headings: `Inter` (weight 600-700) -- clarity and authority
- Body: `Inter` (weight 400) -- readable in data-dense contexts
- Data/code: `JetBrains Mono` -- evidence provenance, codes
- Civic need labels: `Inter` (weight 500, uppercase tracking)

**Motion:** Subtle only -- policy context demands seriousness over delight
- Page transitions: 150ms fade
- Card reveals: 200ms ease-out
- Chart animations: 300ms ease-in-out
- No decorative animations

### 2.2 Component Tokens

```css
--radius-card:    12px;
--radius-badge:   6px;
--radius-input:   8px;

--shadow-card:    0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
--shadow-modal:   0 20px 60px rgba(0,0,0,0.6);

--spacing-xs:     4px;
--spacing-sm:     8px;
--spacing-md:     16px;
--spacing-lg:     24px;
--spacing-xl:     32px;
--spacing-2xl:    48px;
```

---

## 3. Application Structure

```
/                    -- Landing / route guard
/citizen             -- Citizen signal submission portal
/dashboard           -- Policymaker main dashboard (auth required)
/dashboard/map       -- Interactive map view
/dashboard/hotspots  -- Hotspot list and filters
/dashboard/report/[id] -- Civic Intelligence Report detail
/dashboard/copilot   -- AI Copilot interface
/dashboard/conflicts -- Evidence conflict review
/admin               -- Admin panel (data quality, weights) -- future
```

---

## 4. Citizen Signal Submission

### 4.1 Screen: Citizen Portal

**Design intent:** Approachable, native-language first, zero learning curve.

```
+------------------------------------------+
| [Flag] Submit a Development Request       |
| Apna vikas mantaniya bhejein              |  (Hindi subtitle)
+------------------------------------------+
|                                           |
| [Language selector: EN | HI | TE | TA |  |
|  KN | MR | BN | Auto-detect]             |
|                                           |
| How would you like to submit?             |
| [  Voice  ]  [  Text  ]                  |
|                                           |
+------------------------------------------+
| [Voice active: recording...]             |
| OR                                       |
| [Text area: Describe what your community |
|  needs... -- multilingual placeholder]   |
|                                           |
| [Submit Request]                         |
|                                           |
| Your privacy: We do not store your name  |
| or contact details. Location extracted   |
| from your description only.              |
+------------------------------------------+
| [SYNTHETIC DATA MODE indicator if active]|
+------------------------------------------+
```

**States:**
- `idle` -- Blank form
- `recording` -- Voice: animated waveform indicator
- `processing` -- Spinner with "Analyzing your request..."
- `success` -- "Your request has been recorded. Reference: [ID]"
- `error` -- "Unable to process. Please try again or submit as text."
- `synthetic_mode` -- Purple banner: "[SYNTHETIC SIGNAL] This submission is test data"

---

## 5. Policymaker Dashboard

### 5.1 Navigation

```
Sidebar (collapsed on mobile):
  [Map Icon]       Map View
  [Chart Icon]     Hotspots
  [Report Icon]    Intelligence Reports
  [AI Icon]        Copilot
  [Alert Icon]     Conflicts
  [Settings]       Admin (future)

Top bar:
  [Platform name]  [District selector]  [Sector filter]  [User avatar]
```

### 5.2 Screen: Map View (Default Landing)

**Design intent:** Geographic at-a-glance; click to drill down.

```
+---------------------------------------------------+
| [Filter bar: District | Sector | Priority | Date]  |
+---------------------------------------------------+
|                                                   |
|   [Google Maps -- India district pins]            |
|                                                   |
|   Pins color-coded by priority tier:             |
|   RED=Critical  ORANGE=High  YELLOW=Medium        |
|   GREEN=Low  GREY=No data                        |
|                                                   |
|   Pin size proportional to demand signal count   |
|                                                   |
|   [Click pin -> Hotspot panel slides in]         |
|                                                   |
+---------------------------------------------------+
| [Legend]  [Data as of: 2025-03-01]  [Refresh]   |
+---------------------------------------------------+
```

**Hotspot panel (right slide-in):**
```
West Godavari District
Water Supply Deficit
Priority: CRITICAL (0.78)

Demand Signals: 847
Gap: 41,230 households (16.04%)
Population Context: ~280,000 (Census 2011 -- historical)

Evidence Quality: [AVAILABLE] JJM 2025-01-01
[View Full Report] [Ask Copilot]
```

### 5.3 Screen: Civic Intelligence Report

**Design intent:** Dense but navigable. Evidence must be traceable.

```
+--------------------------------------------------+
| Civic Intelligence Report                        |
| West Godavari -- Water Supply Deficit            |
| Report ID: CIR-2025-0847  |  Generated: 2025-03 |
+--------------------------------------------------+

[NEED]
Drinking Water Access -- WATER_SUPPLY_DEFICIT
LGD District: 527 (West Godavari, Andhra Pradesh)

[CITIZEN DEMAND]
847 signals in the last 90 days
Trend: +12% month-over-month
[SYNTHETIC: 23 of 847 signals are synthetic test data]

[INFRASTRUCTURE STATE]
Total Households:  2,58,000
With Tap Connection: 2,16,770 (84.0%)
Without Connection:  41,230 (16.0%)
Source: JJM District Report | Data as of: 2025-01-01
Quality: [AVAILABLE -- GREEN]

[GAP ASSESSMENT]
Unmet Demand: 41,230 households
Gap Percentage: 16.04%
Additional Context: 3 habitations with fluoride contamination
Calculation: gap.water.v1.0

[PRIORITY SCORE]
0.78 / 1.00 -- CRITICAL
  Infrastructure Gap (40%):   0.16 x 0.40 = 0.064
  Citizen Demand (30%):       0.847 x 0.30 = 0.254
  Population Impact (20%):    0.72 x 0.20 = 0.144
  Evidence Quality (10%):     1.00 x 0.10 = 0.100
  Formula: priority.v1.0.0

[CONFLICTS]
[!] None detected

[EVIDENCE TRAIL]
Step 1: Signal received -- 2025-03-01
Step 2: Need extracted -- WATER_SUPPLY_DEFICIT (Gemini)
Step 3: Geography resolved -- LGD 527 (confidence: 0.94)
Step 4: JJM evidence queried -- data_as_of 2025-01-01
Step 5: Gap calculated -- gap.water.v1.0
Step 6: Priority scored -- priority.v1.0.0

[AI EXPLANATION] -- labeled
"West Godavari District shows a persistent water access gap affecting
approximately 41,000 households. The combination of high citizen demand
and documented infrastructure deficit makes this a Critical priority.
The fluoride contamination in 3 habitations adds urgency to FHTC rollout."

[ASSUMPTIONS]
- Population context from Census 2011 (15+ year old data; treat as directional)
- JJM data as of 2025-01-01; current state may vary

[ACTIONS]
[Download PDF]  [Share]  [Flag for Review]  [Ask Copilot]
```

### 5.4 Screen: AI Copilot

**Design intent:** Conversational but evidence-anchored. Not a chatbot -- a grounded analyst.

```
+--------------------------------------------------+
| [AI Icon] Policy Copilot                        |
| Grounded answers from official evidence only    |
+--------------------------------------------------+
|                                                  |
| [Chat history]                                  |
|                                                  |
| Policymaker: "Why is West Godavari ranked       |
| higher than YSR Kadapa?"                        |
|                                                  |
| [AI EXPLANATION]                                |
| "Based on the official JJM evidence (as of     |
| 2025-01-01), West Godavari has 16% of          |
| households without tap connections (41,230),   |
| while YSR Kadapa reports 100% coverage.        |
| The priority formula weights the gap at 40%,   |
| which drives the significant difference in     |
| scores. Evidence sources shown below."         |
|                                                  |
| Sources used:                                   |
| - JJM District Report (West Godavari, 2025-01) |
| - JJM District Report (YSR Kadapa, 2025-01)   |
| - Priority Formula v1.0.0                      |
|                                                  |
| [Type a question...]           [Send]           |
+--------------------------------------------------+
| Rate this answer: [Helpful] [Not helpful]       |
+--------------------------------------------------+
```

### 5.5 Screen: Evidence Conflicts

```
+--------------------------------------------------+
| Evidence Conflicts                              |
| 2 open conflicts requiring review               |
+--------------------------------------------------+
| [!] West Godavari -- Water Coverage             |
|                                                  |
| Source A: JJM Dashboard (2025-01-01)            |
|   Coverage: 84.0%                               |
|                                                  |
| Source B: Citizen Reports (last 30 days)        |
|   Claim: "No water in our ward"                |
|   Signals: 23 (of which 10 are synthetic)      |
|                                                  |
| Resolution: OPEN                               |
| [Dismiss]  [Flag for Field Verification]       |
+--------------------------------------------------+
```

---

## 6. Key UX States

| State | Trigger | UI Treatment |
|-------|---------|-------------|
| Loading | Data fetch in progress | Skeleton screens, not spinners |
| Empty | No signals for area/sector | "No signals yet -- Be the first to report" |
| Missing data | Evidence quality = MISSING | Grey "No official data" badge |
| Partial data | Evidence quality = PARTIAL | Yellow "Partial data" badge |
| Conflicting data | Two sources disagree | Orange "! Conflict" badge + link to conflict screen |
| Synthetic signal | `is_synthetic = true` | Purple "[SYNTHETIC]" badge on every instance |
| Low confidence | Resolution confidence < 0.85 | "Probable match" label on geography |
| AI explanation | Gemini narrative | Blue "[AI EXPLANATION]" label -- always visible |
| Report outdated | data_as_of > 90 days | Yellow "Data may be outdated" banner |
| Auth required | Unauthenticated policymaker | Redirect to login; citizen portal stays open |

---

## 7. Confidence and Data Quality Communication

Every evidence field in the report carries a visual indicator:

| Indicator | Color | Meaning |
|-----------|-------|---------|
| AVAILABLE | Green dot | Full, recent, authoritative data |
| PARTIAL | Yellow dot | Some fields missing or old |
| MISSING | Grey dot | No authoritative data found |
| CONFLICTING | Orange ! | Two sources disagree |
| LOW_CONFIDENCE | Yellow ~ | Data exists but questionable |
| SYNTHETIC | Purple S | Test data -- not real evidence |

---

## 8. Accessibility

- Minimum WCAG 2.1 AA compliance
- All color indicators have text labels (color not sole indicator)
- Keyboard navigable dashboard
- Screen reader labels on all interactive elements
- Map alternative: tabular hotspot list (accessible equivalent of map view)
- Audio submission has text fallback
- Language selector at top of every citizen-facing page

---

## 9. Responsive Strategy

| Breakpoint | Primary Use | Layout |
|-----------|-------------|--------|
| < 640px | Citizen mobile | Single column; voice/text toggle |
| 640-1024px | Tablet / hybrid | Sidebar collapsed; report scrollable |
| 1024px+ | Policymaker desktop | Full sidebar; map + panel split |

Dashboard is **desktop-first** (policymaker context). Citizen portal is **mobile-first**.

---

## 10. Information Hierarchy

```
Dashboard:
  L1: Priority tier (CRITICAL / HIGH / MEDIUM / LOW)
  L2: District + Sector
  L3: Gap percentage + demand count
  L4: Evidence quality indicator
  L5: Report ID + date

Report Detail:
  L1: Need + Geography
  L2: Gap + Priority score
  L3: Demand trend + evidence state
  L4: Factor breakdown
  L5: Full evidence trail + assumptions
```

---

*Architecture V1 -- 2026-09-24*
