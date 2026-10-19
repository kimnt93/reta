# Provider configuration

Review provider JSON before running a browser. Required identity: id,
allowed_origins, data_url, table_selector, permission and source_type.
Optional login configuration: login_url, username_selector,
password_selector, submit_selector, authenticated_selector. Credentials use
RETA_<UPPERCASE_ID>_USERNAME/PASSWORD, or each name with _FILE. Secret values
must never appear in the JSON. Use a dedicated account where possible.

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
