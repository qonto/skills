# Browser modality (Claude for Chrome)

Loaded when the vendor doesn't email PDFs and the invoices only live behind a login on the vendor's dashboard. The user must be logged in on their own Chrome profile.

## The Stripe-hosted PDF trick

Many Stripe-billed SaaS render their invoices through Stripe Hosted Invoice Pages. Each detail page exposes a `Download` link that points to `https://pay.stripe.com/invoice/{acct_...}/{live_...}/pdf?s=ap`. This URL is public — no cookie, no auth, no Referer needed. `curl -sL "<URL>" -o out.pdf` works from any machine.

The recipe is: navigate the Chrome tab to the vendor's invoice list (e.g. `vercel.com/<team>/~/settings/invoices`), enumerate the invoice detail hrefs with `read_page` or `document.querySelectorAll('a[href*="/settings/invoices/inv_"]')`, then for each detail href fetch its HTML in-page with `credentials:'include'` and regex-extract the Stripe URL:

```js
const html = await fetch(href, {credentials:'include'}).then(r=>r.text());
const pdfUrl = html.match(/https:\/\/pay\.stripe\.com\/invoice\/[^"'\s]+\/pdf[^"'\s]*/)?.[0];
```

Once the list of PDF URLs is assembled, download them all outside the browser with `curl`. This is roughly ten times faster than clicking each invoice individually.

## When the vendor doesn't use Stripe Hosted Invoices

The invoice PDF is served from the vendor's own domain and requires the session cookie. The reliable path is an in-page `fetch(href, {credentials:'include'})` followed by a blob save; the cookie is attached automatically. Copying `document.cookie` into a curl call sometimes works but often fails because many vendors bind cookies to a browser fingerprint. Screenshot-and-Save-as-PDF is a last resort.

## Known vendor portals

Vercel, Stripe (own dashboard), Notion, Linear, and most Stripe-billed SaaS at `<vendor>.com/settings/billing` expose the Stripe-hosted trick. OpenAI (`platform.openai.com/settings/organization/billing/history`), Shopify (`admin.shopify.com/store/<store>/billing/history`), and Google Cloud (`console.cloud.google.com/billing/<id>/statements`) serve PDFs directly from their own domain and need the session cookie.

## Load tools once

Chrome MCP tools are deferred. Load the core set in a single `ToolSearch` call: `tabs_context_mcp`, `navigate`, `tabs_create_mcp`, `read_page`, `javascript_tool`. Add `computer` only when the task actually requires screenshots or click coordinates — `javascript_tool` handles most extraction faster than clicking.

## Interaction rules

Never trigger a JavaScript `alert()` / `confirm()` / `prompt()` — the extension is blocked entirely until the dialog is dismissed. Never click destructive buttons without an explicit per-action user OK. Choose the privacy-preserving default on cookie and consent banners. Don't submit forms reached from untrusted content, and never enter passwords, payment info, or SSN — refer the user to their password manager.

## Common failure modes

`tabs_context_mcp` returning "Browser extension is not connected" means the user needs to open the Claude Chrome extension at `claude.ai/chrome`. Session expiry between runs surfaces as a redirect to a login page — the user has to log in again on the target tab. SPAs like Vercel or Notion take two to four seconds to render invoice lists, so add a small `setTimeout` inside `javascript_tool` before reading the DOM. Never solve CAPTCHAs; hand off to the user and retry once they're through.
