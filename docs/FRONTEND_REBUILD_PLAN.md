# Frontend Rebuild Plan - Vue + Tailwind

**Created:** 2025-01-28  
**Status:** In Progress  
**Technology Stack:** Vue 3 + Vite + Tailwind CSS

---

## 📋 Table of Contents

1. [Phase 1: Foundation & Setup](#phase-1-foundation--setup)
2. [Phase 2: Request Management](#phase-2-request-management)
3. [Phase 3: Processing Pipeline](#phase-3-processing-pipeline)
4. [Phase 4: Rules Management](#phase-4-rules-management)
5. [Phase 5: Analysis & Reporting](#phase-5-analysis--reporting)
6. [Phase 6: Network Visualization](#phase-6-network-visualization)
7. [Phase 7: Asset Registry](#phase-7-asset-registry)
8. [Phase 8: Advanced Features & Polish](#phase-8-advanced-features--polish)

---

## Phase 1: Foundation & Setup

### 1.1 Project Initialization
- [ ] Vue 3 + Vite setup
- [ ] Tailwind CSS configuration
- [ ] TypeScript setup (optional but recommended)
- [ ] ESLint + Prettier configuration
- [ ] Project folder structure

### 1.2 Design System
- [ ] Color palette (primary, secondary, success, error, warning)
- [ ] Typography scale (headings, body, captions)
- [ ] Spacing system (Tailwind defaults + custom)
- [ ] Component library setup (shadcn-vue or similar)
- [ ] Icon library (Heroicons or Lucide)

### 1.3 Core Infrastructure
- [ ] API service layer (Axios with interceptors)
- [ ] Environment configuration (.env files)
- [ ] Error handling system
- [ ] Loading state management
- [ ] Toast/notification system
- [ ] Router setup (Vue Router)

### 1.4 Base Components
- [ ] Button (primary, secondary, outline, ghost)
- [ ] Input (text, file, number)
- [ ] Card
- [ ] Badge
- [ ] Spinner/Loader
- [ ] Alert/Toast
- [ ] Modal/Dialog
- [ ] Table (basic structure)

### 1.5 Layout Components
- [ ] App layout (header, sidebar, main content)
- [ ] Navigation menu
- [ ] Footer
- [ ] Page container

**Deliverables:** Working Vue app with design system and base components

---

## Phase 2: Request Management

### 2.1 Request List Page (`/requests`)
- [ ] Table view with columns: ID, Title, Status, External ID, Created Date, Actions
- [ ] Card/Grid view toggle
- [ ] Pagination (skip/limit)
- [ ] Search (by title, external ID)
- [ ] Filter (by status, date range)
- [ ] Sort (by date, title, status)
- [ ] Status badges (submitted, processing, completed, failed)
- [ ] Action buttons (View, Delete, Process)
- [ ] Empty state
- [ ] Loading skeleton

### 2.2 Request Upload Page (`/requests/new`)
- [ ] Form fields: Title (required), External ID (optional), File upload
- [ ] File validation: CSV only, Max size (50MB), File preview
- [ ] Upload progress indicator
- [ ] Success/error messages
- [ ] Redirect to detail page on success

### 2.3 Request Detail Page (`/requests/:id`)
- [ ] Request metadata display
- [ ] Status timeline/indicator
- [ ] Quick stats (Total rules, Endpoints, Services)
- [ ] Action buttons (Process CSV, Compute Facts, etc.)
- [ ] Tabs: Overview, Rules, Analysis, Visualization
- [ ] Processing history/log

### 2.4 Request Service Integration
- [ ] `GET /api/v1/far` - List requests
- [ ] `POST /api/v1/far` - Create request
- [ ] `GET /api/v1/far/{id}` - Get request details
- [ ] Error handling for all endpoints
- [ ] Loading states

**Components:**
- `RequestList.vue`
- `RequestCard.vue`
- `RequestTable.vue`
- `RequestUploadForm.vue`
- `RequestDetail.vue`
- `StatusBadge.vue`
- `FileUpload.vue`

**Deliverables:** Full CRUD for FAR requests

---

## Phase 3: Processing Pipeline

### 3.1 Processing Dashboard (`/requests/:id/process`)
- [ ] Step indicator (4 steps: Upload, Process CSV, Compute Facts, Compute Hybrid)
- [ ] Progress bar (overall + per step)
- [ ] Real-time status updates (polling or WebSocket)
- [ ] Step details (Status, Duration, Results, Errors)
- [ ] Auto-advance on completion
- [ ] Manual step trigger buttons

### 3.2 CSV Ingestion
- [ ] Trigger ingestion button
- [ ] Processing status (Queued, Processing, Completed, Failed)
- [ ] Results display (Rules created count, Errors/warnings, Processing time)
- [ ] Error details (if failed)
- [ ] Retry button

### 3.3 Facts Computation
- [ ] Standard facts: Trigger button, Progress indicator, Results summary
- [ ] Hybrid facts: Trigger button, Progress indicator, Results summary
- [ ] Batch processing status
- [ ] Cancel operation (if supported)

### 3.4 Processing History
- [ ] Timeline component
- [ ] Each step shows: Timestamp, Status, Duration, Results
- [ ] Expandable details
- [ ] Error logs (if any)

**Components:**
- `ProcessingDashboard.vue`
- `StepIndicator.vue`
- `ProcessingStatus.vue`
- `ResultsSummary.vue`
- `ProcessingTimeline.vue`

**Deliverables:** Complete processing pipeline UI

---

## Phase 4: Rules Management

### 4.1 Rules List Page (`/requests/:id/rules`)
- [ ] Table view with columns: ID, Action, Direction, Endpoints, Services, Facts, Created
- [ ] Pagination (skip/limit)
- [ ] Search (by ID, action)
- [ ] Filters: Action (allow/deny), Has facts (yes/no), Protocol
- [ ] Sort (by ID, date, action)
- [ ] Row actions (View Details)
- [ ] Bulk selection (if needed)
- [ ] Export (CSV, JSON)

### 4.2 Rule Detail View (`/rules/:id`)
- [ ] Rule header: ID, Action, Direction, Request ID
- [ ] Sources section: List of source IPs/CIDRs, Expandable list, Copy to clipboard
- [ ] Destinations section: List of destination IPs/CIDRs, Expandable list
- [ ] Services section: Protocol, Port ranges, Table format
- [ ] Facts section: Collapsible panel, Key-value display, Color-coded
- [ ] Related assets (if available)
- [ ] Security analysis badge
- [ ] Back to rules list button

### 4.3 Rules Explorer
- [ ] Advanced filters: IP range, Protocol, Port range, Facts-based
- [ ] Search: By IP address, By CIDR, By protocol/port
- [ ] View modes: Table, Cards, Compact
- [ ] Rule comparison (select 2+ rules)
- [ ] Export filtered results

### 4.4 Rule Components
- [ ] `RuleCard.vue` (compact view)
- [ ] `RuleTableRow.vue` (table row)
- [ ] `RuleDetailPanel.vue` (expanded view)
- [ ] `FactsDisplay.vue` (facts visualization)
- [ ] `EndpointList.vue` (sources/destinations)
- [ ] `ServiceList.vue` (protocols/ports)

**Components:**
- `RulesList.vue`
- `RuleDetail.vue`
- `RuleCard.vue`
- `RuleTable.vue`
- `FactsDisplay.vue`
- `EndpointList.vue`
- `ServiceList.vue`
- `RulesFilter.vue`

**Deliverables:** Complete rules browsing, filtering, and detailed views

---

## Phase 5: Analysis & Reporting

### 5.1 Request Summary Dashboard (`/requests/:id/summary`)
- [ ] Overview cards: Total Rules, Total Endpoints, Total Services, Estimated Tuples, Facts Coverage %
- [ ] Request info: Title, Status, External ID, Created Date
- [ ] Endpoint analysis: Total sources/destinations, Unique sources/destinations, Reuse ratios
- [ ] Protocol distribution: Pie chart (TCP, UDP, ICMP, etc.), Count per protocol
- [ ] Complexity analysis: Avg endpoints per rule, Avg services per rule, Avg tuples per rule
- [ ] Facts coverage: Progress bar, Rules with/without facts

### 5.2 Security Analysis Page (`/requests/:id/security`)
- [ ] Overall security score: Large score display (0-100), Color-coded, Trend indicator
- [ ] Risk distribution: Pie/bar chart (Low/Medium/High), Count per risk level
- [ ] Common issues panel: Issue type, Count, Severity, Expandable details
- [ ] Recommendations panel: List of recommendations, Priority indicators
- [ ] Rules by risk: Table/cards grouped by risk, Filter by risk level, Click to view rule details
- [ ] Security trends (if historical data)

### 5.3 Analytics Charts
- [ ] Protocol distribution: Pie chart (Chart.js or similar), Interactive
- [ ] Risk level distribution: Bar chart, Stacked by issue type
- [ ] Complexity metrics: Line/bar chart, Over time (if available)
- [ ] Facts coverage: Progress indicators, Breakdown by fact type

### 5.4 Export & Reporting
- [ ] Export options: PDF report, CSV export, JSON export
- [ ] Report builder: Select sections, Customize layout, Include/exclude data
- [ ] Scheduled reports (future)

**Components:**
- `SummaryDashboard.vue`
- `SecurityAnalysis.vue`
- `AnalyticsCharts.vue`
- `ProtocolChart.vue`
- `RiskDistributionChart.vue`
- `CommonIssuesPanel.vue`
- `RecommendationsPanel.vue`
- `ExportDialog.vue`

**Deliverables:** Comprehensive analytics dashboard and security analysis

---

## Phase 6: Network Visualization

### 6.1 Network Topology Viewer (`/requests/:id/visualization`)
- [ ] D3.js integration: Force-directed graph, Hierarchical layout, Circular layout
- [ ] Canvas/SVG rendering: Large network support, Smooth animations
- [ ] Node rendering: Network nodes (IPs/CIDRs), Size by connection count, Color by segment/risk, Labels
- [ ] Edge rendering: Connections between nodes, Thickness by rule count, Color by protocol, Animated flow (optional)
- [ ] Interactive features: Click node, Hover node, Drag nodes, Zoom in/out, Pan, Reset view

### 6.2 Visualization Controls
- [ ] Layout selector: Force-directed, Hierarchical, Circular
- [ ] Filters: By protocol, By risk level, By segment
- [ ] Highlight options: Highlight path between nodes, Highlight high-risk nodes, Highlight specific IP
- [ ] Search: Find node by IP, Center on node
- [ ] View options: Show/hide labels, Node size adjustment, Edge thickness adjustment

### 6.3 Node Details Panel
- [ ] Side panel (slide-in): IP address/CIDR, Asset information, Connected rules count, Protocols used, Risk level, Related assets
- [ ] Connected rules list: Click to view rule details, Filter by protocol
- [ ] Network statistics: Inbound/outbound connections, Total rules, Protocols breakdown

### 6.4 Advanced Visualization
- [ ] Segment grouping: Group nodes by segment, Collapse/expand groups
- [ ] Risk-based coloring: Color scale (green/yellow/red), Legend
- [ ] Animation: Smooth transitions, Loading animation, Highlight animations
- [ ] Export: PNG image, SVG export, JSON data export

**Components:**
- `NetworkVisualization.vue`
- `D3Graph.vue`
- `VisualizationControls.vue`
- `NodeDetailsPanel.vue`
- `GraphLegend.vue`
- `LayoutSelector.vue`

**Deliverables:** Interactive network topology visualization

---

## Phase 7: Asset Registry

### 7.1 Asset List Page (`/assets`)
- [ ] Table view: Columns (IP, Segment, Subnet, Gateway, VLAN, OS, Actions)
- [ ] Pagination
- [ ] Search: By IP address, By segment, By OS
- [ ] Filters: Segment, OS, VLAN
- [ ] Sort (by IP, segment, OS)
- [ ] Actions: View Details, Edit, Delete

### 7.2 Asset Upload (`/assets/upload`)
- [ ] CSV upload form: Drag & drop, File validation, Preview first few rows
- [ ] Upload progress
- [ ] Results display: Assets created, Errors/warnings, Skipped duplicates
- [ ] Success/error handling

### 7.3 Asset Detail View (`/assets/:id`)
- [ ] Asset information: IP address, Segment, Subnet, Gateway, VLAN, OS, OS Version, App Version, DB Version, vCPU, Memory
- [ ] Related rules: Rules where asset is source, Rules where asset is destination, Click to view rule details
- [ ] Asset analytics: Connection count, Protocols used, Risk assessment

### 7.4 Asset-Rule Integration
- [ ] In rule views: Show matching assets, Asset badges, Click to view asset
- [ ] Asset-based filtering: Filter rules by asset, Find rules for specific asset
- [ ] Asset coverage: Show which assets are covered by rules, Missing coverage indicators

### 7.5 Asset Analytics
- [ ] Asset distribution: By segment (pie chart), By OS (bar chart)
- [ ] Asset-rule relationships: Connection graph, Coverage statistics
- [ ] Asset search: Quick IP lookup, Range search

**Components:**
- `AssetList.vue`
- `AssetUpload.vue`
- `AssetDetail.vue`
- `AssetCard.vue`
- `AssetTable.vue`
- `AssetAnalytics.vue`

**Deliverables:** Complete asset management and rule integration

---

## Phase 8: Advanced Features & Polish

### 8.1 IP-based Queries (`/ip-query`)
- [ ] IP search interface: Single IP input, IP range input (CIDR), Multiple IPs (comma-separated)
- [ ] Query options: Include as source, Include as destination, Both
- [ ] Results display: Matching rules list, Rule count, Quick filters
- [ ] IP analysis: IP classification (public/private), Related assets, Network information

### 8.2 Comparison Tools
- [ ] Request comparison: Select 2 requests, Side-by-side view, Diff highlights, Statistics comparison
- [ ] Rule comparison: Select 2+ rules, Compare sources/destinations/services, Highlight differences
- [ ] Comparison charts: Overlay charts, Before/after views

### 8.3 User Experience Enhancements
- [ ] Loading states: Skeleton loaders, Progress indicators, Spinner overlays
- [ ] Error handling: Error boundaries, User-friendly error messages, Retry mechanisms
- [ ] Notifications: Toast notifications, Success/error alerts, Info messages
- [ ] Keyboard shortcuts: Navigation shortcuts, Action shortcuts, Search shortcuts
- [ ] Responsive design: Mobile optimization, Tablet layout, Desktop layout

### 8.4 Performance Optimizations
- [ ] Virtual scrolling: For large rule lists, For large asset lists
- [ ] Lazy loading: Route-based code splitting, Component lazy loading, Image lazy loading
- [ ] Caching: API response caching, Local storage caching, Service worker (optional)
- [ ] Optimistic updates: Immediate UI updates, Rollback on error

### 8.5 Settings & Preferences
- [ ] User preferences: Default view (table/cards), Items per page, Theme (light/dark)
- [ ] Display options: Show/hide columns, Default filters, Sort preferences
- [ ] Export settings: Default export format, Include options
- [ ] Notifications: Email preferences, In-app notifications

### 8.6 Additional Features
- [ ] Dashboard/homepage: Recent requests, Quick stats, Quick actions, Activity feed
- [ ] Help & documentation: In-app help, Tooltips, User guide
- [ ] Accessibility: ARIA labels, Keyboard navigation, Screen reader support, High contrast mode

**Components:**
- `IPQuery.vue`
- `ComparisonView.vue`
- `SettingsPage.vue`
- `Dashboard.vue`
- `HelpDialog.vue`
- `KeyboardShortcuts.vue`

**Deliverables:** Polished, performant, accessible application

---

## 📊 Summary by Phase

| Phase | Focus | Key Features | Components | Status |
|-------|-------|--------------|------------|--------|
| 1 | Foundation | Setup, Design System, Base Components | 10+ base components | ✅ Completed |
| 2 | Requests | CRUD, Upload, Detail View | 7 components | ⬜ Not Started |
| 3 | Processing | Pipeline, Progress, Status | 5 components | ⬜ Not Started |
| 4 | Rules | List, Detail, Filter, Search | 8 components | ⬜ Not Started |
| 5 | Analysis | Summary, Security, Charts | 8 components | ⬜ Not Started |
| 6 | Visualization | D3.js Graph, Interactive | 6 components | ⬜ Not Started |
| 7 | Assets | Asset Management, Integration | 6 components | ⬜ Not Started |
| 8 | Polish | Advanced Features, UX, Performance | 6+ components | ⬜ Not Started |

**Total:** ~56 components + base infrastructure

---

## 🗓️ Recommended Build Order

- **Week 1-2:** Phase 1 + Phase 2 (Foundation + Requests)
- **Week 3:** Phase 3 (Processing Pipeline)
- **Week 4:** Phase 4 (Rules Management)
- **Week 5:** Phase 5 (Analysis)
- **Week 6:** Phase 6 (Visualization)
- **Week 7:** Phase 7 (Assets)
- **Week 8:** Phase 8 (Polish)

---

## 📝 Implementation Notes

### Phase 1 Notes
**Completed: 2025-01-28**

✅ **Project Setup:**
- Vue 3 + Vite project structure created
- Tailwind CSS configured with custom design system
- ESLint + Prettier configured
- TypeScript-ready structure (optional)

✅ **Design System:**
- Color palette: Primary, Secondary, Success, Error, Warning
- Typography scale with semantic headings
- Custom Tailwind configuration
- Component utility classes

✅ **Core Infrastructure:**
- API service layer with Axios (interceptors for error handling)
- Vue Router setup with routes
- Toast notification system (composable)
- Environment configuration

✅ **Base Components Created:**
- Button (primary, secondary, outline, ghost variants)
- Input (with validation, error states)
- Card (with header/footer slots)
- Badge (multiple variants)
- Spinner/Loader
- Toast (with auto-dismiss)
- Modal/Dialog

✅ **Layout Components:**
- AppLayout (main container)
- AppHeader (navigation)
- AppFooter

✅ **Views Created:**
- Home page (placeholder)
- RequestsList (placeholder for Phase 2)
- RequestNew (placeholder for Phase 2)
- RequestDetail (placeholder for Phase 2)

**Next Steps:** Ready to begin Phase 2 (Request Management)

### Phase 2 Notes
_Add notes here as you implement..._

### Phase 3 Notes
_Add notes here as you implement..._

### Phase 4 Notes
_Add notes here as you implement..._

### Phase 5 Notes
_Add notes here as you implement..._

### Phase 6 Notes
_Add notes here as you implement..._

### Phase 7 Notes
_Add notes here as you implement..._

### Phase 8 Notes
_Add notes here as you implement..._

---

## 🔗 Related Documentation

- [API Documentation](../API_DOCUMENTATION.md)
- [FAR System Docs](./FAR_SYSTEM_DOCS.md)
- [Project Structure](./PROJECT_STRUCTURE.md)

---

## 📅 Changelog

### 2025-01-28
- Created frontend rebuild plan
- Defined 8 phases with detailed functionality lists
- Technology stack: Vue 3 + Vite + Tailwind CSS

