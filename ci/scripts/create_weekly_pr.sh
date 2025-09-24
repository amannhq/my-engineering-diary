#!/usr/bin/env bash
set -euo pipefail

emit_log() {
  python - "$@" <<'PY'
import datetime as dt
import json
import sys

payload = {}
event_name = "weekly_pr.log"
for arg in sys.argv[1:]:
    key, value = arg.split('=', 1)
    if key == 'event':
        event_name = value
    else:
        payload[key] = value

payload.setdefault("timestamp", dt.datetime.utcnow().isoformat() + "Z")
payload["event"] = event_name
print(json.dumps(payload))
PY
}

usage() {
  cat <<'EOF'
Usage: create_weekly_pr.sh --week-id WEEK --report-path PATH --checklist-path PATH [--partial-failures JSON]
Requires: gh CLI, GH_TOKEN
EOF
  exit 2
}

WEEK_ID=""
REPORT_PATH=""
CHECKLIST_PATH=""
PARTIAL_FAILURES="[]"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --week-id)
      WEEK_ID="$2"
      shift 2
      ;;
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    --checklist-path)
      CHECKLIST_PATH="$2"
      shift 2
      ;;
    --partial-failures)
      PARTIAL_FAILURES="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

[[ -n "$WEEK_ID" && -n "$REPORT_PATH" && -n "$CHECKLIST_PATH" ]] || usage

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "GH_TOKEN environment variable must be set" >&2
  exit 1
fi

emit_log event=weekly_pr.start week_id="$WEEK_ID"

WEEK_PART="${WEEK_ID#*-}"
if [[ "$WEEK_PART" == "$WEEK_ID" ]]; then
  WEEK_NUMBER="$WEEK_ID"
else
  WEEK_NUMBER="${WEEK_PART#W}"
fi
WEEK_NUMBER_LOWER="${WEEK_NUMBER,,}"
TITLE="chore(weekly-review): week ${WEEK_NUMBER_LOWER} insights"

PARTIAL_SUMMARY=$(python - <<'PY' "$PARTIAL_FAILURES"
import json
import sys
items = json.loads(sys.argv[1] or "[]")
lines = []
for item in items:
    issues = ", ".join(item.get("issues", [])) or "No details provided"
    lines.append(f"- {item.get('log_ref', 'unknown')}: {issues}")
print("\n".join(lines))
PY
)
PARTIAL_COUNT=$(python - <<'PY' "$PARTIAL_FAILURES"
import json
import sys
items = json.loads(sys.argv[1] or "[]")
print(len(items))
PY
)

BODY_FILE=$(mktemp)
{
  echo "# Weekly Review — ${WEEK_ID}"
  echo ""
  echo "- Report: ${REPORT_PATH}"
  echo "- Checklist: ${CHECKLIST_PATH}"
  echo "- Partial failures: ${PARTIAL_COUNT}"
  if [[ -n "$PARTIAL_SUMMARY" ]]; then
    echo ""
    echo "## Partial Failures"
    echo "$PARTIAL_SUMMARY"
  fi
  echo ""
  echo "## Checklist"
  echo "See ${CHECKLIST_PATH} for the Constitution compliance checklist."
  echo ""
  echo "## Next Steps"
  echo "- Review checklist outcomes."
  echo "- Resolve partial failures (if any)."
  echo "- Merge once satisfied with insights."
} > "$BODY_FILE"

BASE_BRANCH="${BASE_BRANCH:-${GITHUB_BASE_REF:-main}}"
HEAD_BRANCH="${GITHUB_HEAD_REF:-$(git rev-parse --abbrev-ref HEAD)}"

emit_log event=weekly_pr.body_prepared week_id="$WEEK_ID" body_file="$BODY_FILE" partial_failures="$PARTIAL_COUNT"

EXISTING_PR=$(gh pr list --state open --search "\"$TITLE\" in:title" --json number --jq '.[0].number' || true)

if [[ -n "$EXISTING_PR" ]]; then
  emit_log event=weekly_pr.update week_id="$WEEK_ID" pr_number="$EXISTING_PR"
  gh pr edit "$EXISTING_PR" --title "$TITLE" --body-file "$BODY_FILE"
else
  emit_log event=weekly_pr.create week_id="$WEEK_ID" base="$BASE_BRANCH" head="$HEAD_BRANCH"
  gh pr create --title "$TITLE" --body-file "$BODY_FILE" --base "$BASE_BRANCH" --head "$HEAD_BRANCH"
fi

emit_log event=weekly_pr.complete week_id="$WEEK_ID" partial_failures="$PARTIAL_COUNT"
