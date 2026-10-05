# Stage B: has the data landed

Steps 7 to 9. Coverage says a connector is there; these steps check that what it carries has landed.

## 7. Confirm every sync has finished, and recently

One `well_query_records` on `workspace_connector_sync_logs` for the connected and connecting connectors, newest first. For each connector read its latest row's `status` and `completed_at`, whether a run is still `scheduled` or `in_progress`, and the `completed_at` of its latest `success` row.

- **A sync still running** → name the connector and say it must land "before any page of the pack is measured". A reconnect re-fetches the whole history, so it is normally minutes rather than seconds. Re-read the sync logs once. Still running → stop, say how long it has been going, and offer Re-check. Do not loop reads back to back: they give the sync no time to progress.
- **Only a `success` row is a finish.** A run that closed as `error`, `interrupted`, `skipped` or `timed_out` did not land, even when it wrote some rows. A connector whose rows hold no `success` has not landed: name it and its latest status, and stop. Never read a half-finished first sync as a landed feed.
- **A connector with no sync-log row** has begun no run yet. Say it has not landed, and stop.
- **A latest `success` older than 6 hours** → name the connector and the age, offer Re-check and the reconnect link, and carry on. Stale data makes a figure old rather than wrong.
- Every connector has a `success` row and no run open → keep the timestamps for the freshness line and carry on.

This step does not offer a way past a sync that has not landed. A figure measured while its own feed is still loading is a figure nobody can check.

**Resuming.** Re-check names this step, so a run that comes back re-reads the sync logs alone and continues from here.

## 8. Confirm the window holds transactions

One `well_query_records` on `transactions` (`limit: 1`), ranging `executed_at` over the window's own interval. Read `totalCount`, not the rows.

- At least one → carry on, and keep the count.
- None → stop. A window with no transactions produces a figure of zero, and zero standing on nothing measured is not a reading. Tell apart, from step 7's findings, a feed that has delivered nothing yet from real months in which nothing moved. Offer Re-check when the feed is the likely cause, and a wider window when the months simply hold nothing.

## 9. Confirm a balance has actually landed

Call `well_list_account_balances` with `months_back` covering the window. This is the same read the cash page uses, so keep the whole result, series included, and do not call it again.

- No rows and `partial: true` → stop, and say the read was cut short. There is no cash page and no runway. Offer Re-check.
- No rows and `partial: false` → stop, and say no account has landed yet.
- Rows, but every one with a `null` balance → stop. Say which it is: an account with no history yet, or one whose balance was repudiated (`verification_rejected`).
- `unreadable_rows` above zero, with other rows readable → carry on and disclose the count. The cash may be a floor by up to that many accounts, and the runway with it.
