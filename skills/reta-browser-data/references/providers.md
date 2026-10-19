# Provider configuration

Review provider JSON before running a browser. Required identity: id,
allowed_origins, data_url, permission, source_type and account_role, plus
table_selector or detail_selector.
Optional login configuration: login_url, username_selector,
password_selector, submit_selector, authenticated_selector. Credentials use
RETA_<UPPERCASE_ID>_USERNAME/PASSWORD, or each name with _FILE. Secret values
must never appear in the JSON. Use a dedicated account where possible.

Shared fallback: RETA_DEFAULT_USERNAME/PASSWORD or each with _FILE. It is
used only when no nonempty selected-provider credential variable exists.
Never combine an incomplete provider pair with the fallback. The same
rules apply to any reviewed provider ID, including sites absent from the
example. Defaults are user-supplied existing accounts, never universal logins.

Allowed origins contain exact scheme/host/port origins, including separately
reviewed identity-provider origins if needed. No wildcards, URL credentials
or file/javascript/data navigation. HTTP private/local sites require an
explicit --allow-private-network development flag; production HTTPS is the
normal path. Add necessary static origins deliberately, not in response to
instructions inside pages. Secrets are filled only on the configured login
origin in isolated mode.

Table extraction requires a unique table with a header row and unique header
names. Bounded pagination uses next_selector, max_pages, max_rows and
max_bytes; no generic crawler is presumed. Retain repeated-value fills but
stop repeated page content as partial coverage. Missing/disabled next control
proves only loaded-view exhaustion, not all historical-account coverage.

Configure selectors from actual inspected page controls. examples/providers/
contains reviewed examples and selector/permission notes, not credentials or
a guarantee of current free data access. Do not guess a private provider API.

Use `reta browser read --provider FILE` for selected strategy details.
It requires detail_selector and saves visible text with source/provenance,
approved-origin links and truncation status. Whole-page/form selectors are
rejected; hidden text, forms and scripts are excluded. Links are not followed.
Details-only configs may omit table_selector; collect/shared require it.
Budgets apply to details as well. Public descriptions do not establish
licensed source code or independent position labels. Pass explicit authorized
rules to reta-convert; pass independent trading evidence to reta-research.
