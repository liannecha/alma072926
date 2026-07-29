# Alma-Inspired UI Style Guide

Use this guide when updating the intake app so it feels closer to Alma's public `get-started` page. The target look is calm, polished, spacious, and form-first: a warm off-white site chrome, a pale green stage, dark green brand/action elements, and a clean white intake card.

## Product Feeling

- Calm and trustworthy, not flashy.
- Premium but approachable, with generous spacing and soft edges.
- The first screen should be the actual intake workflow, not a marketing splash page.
- Keep copy direct and human. Avoid explaining the UI inside the UI.
- Let the form feel like the primary product surface.

## Color Tokens

Use a restrained warm green palette.

```css
:root {
  --alma-ink: #071411;
  --alma-green-900: #234f45;
  --alma-green-800: #2f6658;
  --alma-green-700: #3c7668;
  --alma-green-soft: #e4f6bd;
  --alma-cream: #fbf5ec;
  --alma-surface: #ffffff;
  --alma-border: #dedfd8;
  --alma-muted: #70737a;
  --alma-yellow: #ffdc82;
}
```

Guidance:

- Page background: `--alma-cream`.
- Main intake stage: `--alma-green-soft`.
- Form card: `--alma-surface`.
- Primary buttons and logo/nav accents: `--alma-green-800` or `--alma-green-900`.
- Body text: `--alma-ink`.
- Secondary text and placeholders: `--alma-muted`.
- Decorative geometric accent, if needed: `--alma-yellow`.

Avoid bright blues, harsh blacks, saturated gradients, and heavy shadows.

## Typography

Alma's page uses a rounded, geometric sans-serif feeling. In implementation, prefer a soft modern sans stack or a bundled web font if available.

```css
body {
  font-family: "Inter", "Avenir Next", "Helvetica Neue", Arial, sans-serif;
  color: var(--alma-ink);
}
```

Type scale:

- Logo: 32-40px, bold, lowercase if using text.
- Nav: 18-20px, regular weight.
- Hero heading: 52-64px desktop, 40-48px tablet, 32-38px mobile.
- Form heading: 24-28px, medium or semibold.
- Inputs: 18-20px.
- Legal/helper text: 13-14px.

Rules:

- Use line-height around `1.08-1.15` for the large hero heading.
- Use line-height around `1.45-1.65` for testimonials, helper copy, and legal text.
- Do not use all caps except for small eyebrow labels.
- Eyebrows should be small, bold, and paired with a small green dot.
- Keep letter spacing at `0`.

## Layout

The page should feel like a large soft panel underneath a simple navigation bar.

Desktop structure:

```text
cream page
  sticky/standard cream nav, 88-100px tall
  pale green rounded stage, inset 20px from viewport edges
    two-column content
      left: intro/testimonial/business link
      right: white form card
```

Sizing:

- Nav horizontal padding: `clamp(24px, 5vw, 96px)`.
- Stage margin: `20px`.
- Stage border radius: `8px`.
- Stage padding: `clamp(48px, 6vw, 100px)`.
- Main grid max width: around `1680px`.
- Desktop grid: left column `minmax(360px, 0.9fr)`, right column `minmax(560px, 0.95fr)`.
- Column gap: `clamp(56px, 8vw, 140px)`.
- Form card width: about `760-840px`.

Mobile:

- Stack intro above form.
- Reduce stage margin to `12px`.
- Use `24px` stage padding.
- Form fields become one column.
- Keep the form card white and spacious, but reduce padding to `24px`.

## Navigation

The nav should be quiet and brand-led.

- Background: `--alma-cream`.
- Height: roughly `90px`.
- Logo on the left in dark green.
- Center nav links with simple chevron icons for dropdown items.
- Right actions: search icon, outline `Log In`, filled `Get Started`.
- Buttons should be rounded rectangles, not pills.
- Use dark green borders on outline buttons.

Button examples:

```css
.nav-button {
  min-height: 52px;
  border-radius: 10px;
  padding: 0 22px;
  font-size: 20px;
}

.nav-button.primary {
  background: var(--alma-green-800);
  color: white;
  border-color: var(--alma-green-800);
}
```

## Intake Hero

Left intro area:

- Eyebrow: green dot plus `GET STARTED`.
- Heading: `Schedule a free immigration consultation`.
- Star rating: five dark green stars.
- Testimonial: large, readable paragraph with the customer attribution in bold.
- Secondary business promo: small eyebrow plus short stacked title and arrow.

Keep the left column text dark, spacious, and editorial. Do not put it in a card.

## Form Card

The form card is the main surface.

```css
.form-card {
  background: var(--alma-surface);
  border-radius: 8px;
  padding: clamp(28px, 4vw, 60px);
  box-shadow: none;
}
```

Rules:

- Use a white card directly on the pale green stage.
- Border radius should be subtle: `8px`, not large rounded blobs.
- Avoid strong shadows. A faint border is enough if separation is needed.
- Form heading should read like: `Just provide a few details, and we'll get you started.`
- Required fields note appears underneath in muted text.

## Inputs

Inputs should be large, airy, and low-contrast.

```css
.input,
.select,
.textarea {
  width: 100%;
  min-height: 62px;
  border: 1px solid var(--alma-border);
  border-radius: 10px;
  background: #ffffff;
  color: var(--alma-ink);
  font-size: 20px;
  padding: 0 20px;
}

.textarea {
  min-height: 240px;
  padding-top: 18px;
  resize: vertical;
}

.input::placeholder,
.textarea::placeholder {
  color: var(--alma-muted);
}
```

Layout:

- First/last name: two columns on desktop.
- Email/company: two columns.
- LinkedIn/phone: two columns.
- Upload control: compact gray upload button plus helper text below.
- Selects and textarea: full width.
- Submit: dark green button, modest width, left-aligned.
- Legal text: small muted paragraphs below submit.

## Buttons

- Primary actions: dark green fill, white text.
- Secondary actions: cream/white fill, dark green border and text.
- Border radius: `8-10px`.
- Padding: `14-20px` vertical, `20-28px` horizontal.
- Hover: subtle darkening or lift, no dramatic animation.
- Disabled: muted opacity, keep layout stable.

## Decorative Elements

Use decoration sparingly.

- A pale green stage is the dominant visual device.
- A single yellow angled geometric shape may appear near a lower/right edge.
- Do not use gradient blobs, bokeh, glass cards, or decorative SVG clutter.
- Do not use heavy card shadows.

## Copy Patterns

Good:

- `Schedule a free immigration consultation`
- `Just provide a few details, and we'll get you started.`
- `Required fields*`
- `Upload resume or CV`
- `Max file size 10MB.`
- `Submit`

Avoid:

- Long feature explanations.
- Technical workflow descriptions on the public page.
- Admin/status language on the prospect form, such as `PENDING` or `Mark reached out`.

## Implementation Checklist

- Replace the current split card look with one pale green stage and one white form card.
- Use an Alma-like cream nav with dark green logo/actions.
- Make the public route form-first.
- Add the testimonial and stars to the left intro area.
- Use large rounded rectangular inputs with placeholders instead of visible labels where accessibility can still be handled with visually hidden labels.
- Keep form card radius at `8px`.
- Increase desktop spacing and input height.
- Keep internal admin UI quieter and denser than the public form, but reuse the same color tokens.
- Test desktop around `1440-1920px` and mobile around `390px`.
