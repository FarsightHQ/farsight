# Frontend conventions

Vue 3 (Composition API, `<script setup>`), Vite, Vue Router, Tailwind CSS, and optional incremental TypeScript in `src/services`, `src/utils`, `src/composables`, and typed UI SFCs.

## Layout and shells

- **[`PageFrame.vue`](src/components/layout/PageFrame.vue)** — Standard app pages: breadcrumbs bar, title/subtitle/actions header, scrollable body. Use for most CRUD and list/detail views under the main sidebar layout.
- **[`VizWorkspaceLayout.vue`](src/components/layout/VizWorkspaceLayout.vue)** — Full-bleed visualization workspace (~80% canvas / ~20% side panel), breadcrumbs compact strip, fullscreen toggle. Use for graph/topology routes (see router `meta.vizWorkspace`).
- **Full-bleed** — Routes that set `meta` to hide chrome (e.g. viz fullscreen) rely on [`useVizAppChrome`](src/composables/useVizAppChrome.ts) with [`AppLayout.vue`](src/components/layout/AppLayout.vue).

## Import boundaries

- **`components/ui/`** — Shared primitives: buttons, inputs, cards, modals, [`StatusBadge`](src/components/ui/StatusBadge.vue), loading/error blocks ([`DetailPageSkeleton`](src/components/ui/DetailPageSkeleton.vue), [`CardSkeleton`](src/components/ui/CardSkeleton.vue), [`ErrorCallout`](src/components/ui/ErrorCallout.vue), [`EmptyState`](src/components/ui/EmptyState.vue)). Import these from feature folders and views when the UI is generic.
- **`components/requests/`** — Request/rule pipeline and network visualization. Prefer not to import “requests” components from registry-only features unless the UI is truly shared; consider promoting to `ui/` if reuse grows.
- **`components/assets/`** — Asset tables, cards, coverage, analytics.
- **`services/`** — HTTP and API clients (axios instance in [`api.ts`](src/services/api.ts)).
- **`composables/`** — Reusable state and side effects (toast, breadcrumbs, auth, graphs).
- **`utils/`** — Pure helpers (graph math, IP/port formatting, project routing helpers).

## Styling

- **Design tokens** — Prefer Tailwind `theme-*`, semantic palettes (`primary`, `secondary`, `error`, `success`, `warning`), and shared neutrals over raw `gray-*` in new code.
- **Global component classes** — [`main.css`](src/assets/css/main.css) defines `@layer components` utilities: `.btn`, `.btn-primary`, `.btn-danger`, `.input`, `.card`. [`Button.vue`](src/components/ui/Button.vue) composes `btn` + variant classes; Tailwind [`safelist`](tailwind.config.js) keeps dynamic `btn-*` classes in production builds.

## Loading, errors, and empty states

- **Detail list loading** — [`DetailPageSkeleton`](src/components/ui/DetailPageSkeleton.vue) (title strip + grid of placeholders).
- **Project overview loading** — [`ProjectOverviewSkeleton`](src/components/ui/ProjectOverviewSkeleton.vue).
- **Card-shaped loading** — [`CardSkeleton`](src/components/ui/CardSkeleton.vue).
- **Errors** — [`ErrorCallout`](src/components/ui/ErrorCallout.vue) with `variant="inline"` or `variant="card"` and optional `centered` + default slot for actions.
- **Not found / empty** — [`EmptyState`](src/components/ui/EmptyState.vue) with `message` and optional actions slot.

## Tooling

- **Tests** — `npm test` (Vitest, `happy-dom` for component tests). Specs live next to components (e.g. `*.spec.ts`).
- **Types** — `npm run typecheck` (`vue-tsc --noEmit`).

## Bundle and runtime

- **Analyze** — `npm run build:analyze` runs a production build in `analyze` mode and writes `dist/stats.html` (treemap of chunk sizes; open locally in a browser). Uses `rollup-plugin-visualizer`.
- **Code splitting** — Vite [`build.rollupOptions.output.manualChunks`](vite.config.js) keeps **`d3`** and **`keycloak-js`** in separate vendor chunks so graph/auth code does not inflate the main entry.
- **Heavy UI** — [`NetworkGraphModal.vue`](src/components/requests/NetworkGraphModal.vue) is loaded with **`defineAsyncComponent`** from [`RequestDetail.vue`](src/views/RequestDetail.vue), [`RuleDetail.vue`](src/views/RuleDetail.vue), and [`AllRules.vue`](src/views/AllRules.vue) so the graph bundle is fetched only when the modal is needed.

## Accessibility

- **Linting** — [`eslint-plugin-vuejs-accessibility`](https://github.com/vuejs/eslint-plugin-vuejs-accessibility) is enabled (rules set to **warn** so existing screens can be fixed incrementally).
- **Toasts** — [`Toast.vue`](src/components/ui/Toast.vue) uses a live **`role="region"`** with **`aria-live="polite"`**, per-message **`role="status"`** / **`role="alert"`** (errors), dismiss control with **`aria-label`**, decorative icons **`aria-hidden`**.
- **Modals** — [`Modal.vue`](src/components/ui/Modal.vue) uses **`role="dialog"`**, **`aria-modal="true"`**, **`aria-labelledby`** when a title is set, **Escape** closes, initial **focus** moves to the dialog surface, close control **`aria-label="Close dialog"`**.
