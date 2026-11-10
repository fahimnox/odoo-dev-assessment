#!/usr/bin/env bash
# Partner Monitor restart check (test plan TP-PM-15, docs/resilience.md).
#
# Stops the worker process during a batch, then restarts it, on the disposable
# test database of the matched Enterprise pair:
#   1. seed a queue (scripts/restart_check.py, phase "setup") and commit it;
#   2. run the worker job in a one-off container; batch 1 commits, batch 2
#      blocks inside a page read;
#   3. SIGKILL that container (docker kill), so the process dies mid-batch;
#   4. run the worker job again in a new container;
#   5. check the result (phase "verify").
# The SQL state is printed before the worker starts, during batch 2, after the
# kill and after the restart.
#
# Needs a fresh test database with the module installed: run
# "scripts/dev.sh test azk_odoo_partner_monitor" first. Never touches the
# development database. Usage: scripts/restart_check.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
cd "$(dirname "${BASH_SOURCE[0]}")/.."

SERVICE=odoo-ee-20241208
DB=azk_ee24_test
WORKER=azk-pm-restart-worker
SCRIPT=scripts/restart_check.py
WORK_DIR="$(mktemp -d)"
CRASH_LOG="$WORK_DIR/worker_crash.log"

die() { echo "error: $*" >&2; exit 1; }

sql() {
    docker compose exec -T db psql --username=odoo --dbname="$DB" --no-psqlrc \
        --pset=pager=off --pset=footer=off "$@"
}

phase() {  # PHASE [docker compose run options...]
    local name="$1"; shift
    docker compose run --rm -T "$@" -e PM_PHASE="$name" "$SERVICE" \
        odoo shell --database="$DB" --no-http --log-level=warn < "$SCRIPT"
}

state() {
    echo
    echo "=== SQL state: $1"
    sql -c "SELECT w.id AS unit, w.run_id AS run, w.kind, coalesce(c.name, p.name) AS target,
                   w.state, w.attempt_count AS tries, to_char(w.finished_at, 'HH24:MI:SS') AS finished
            FROM azk_odoo_partner_monitor_work_item w
            LEFT JOIN azk_odoo_partner_monitor_country c ON c.id = w.country_id
            LEFT JOIN azk_odoo_partner_monitor_partner p ON p.id = w.partner_id
            ORDER BY w.id"
    sql -c "SELECT r.id AS run, r.trigger, r.state,
                   (SELECT count(*) FROM mail_message m WHERE m.model = 'azk_odoo_partner_monitor.sync.run'
                      AND m.res_id = r.id AND m.message_type = 'comment') AS notes,
                   (SELECT count(*) FROM mail_notification n JOIN mail_message m ON m.id = n.mail_message_id
                      WHERE m.model = 'azk_odoo_partner_monitor.sync.run' AND m.res_id = r.id) AS notified,
                   (SELECT count(*) FROM azk_odoo_partner_monitor_sync_error e WHERE e.run_id = r.id) AS error_rows
            FROM azk_odoo_partner_monitor_sync_run r ORDER BY r.id"
    sql -c "SELECT p.source_id, p.name, p.active, p.current_status AS status,
                   (SELECT string_agg(h.change_type, ',' ORDER BY h.id)
                      FROM azk_odoo_partner_monitor_status_history h WHERE h.partner_id = p.id) AS history,
                   (SELECT count(*) FROM azk_odoo_partner_monitor_reference r
                      WHERE r.partner_id = p.id AND r.is_active) AS active_refs
            FROM azk_odoo_partner_monitor_partner p
            WHERE p.source_id IN (22015187, 24934006, 990201, 17207720, 32297621)
            ORDER BY p.source_id"
}

sessions() {
    echo
    echo "=== $1"
    sql -c "SELECT pid, state, to_char(xact_start, 'HH24:MI:SS') AS transaction_started
            FROM pg_stat_activity WHERE datname = '$DB' AND pid <> pg_backend_pid() ORDER BY pid"
    echo "Pending units another worker could claim right now (FOR NO KEY UPDATE SKIP LOCKED, rolled back):"
    sql -c "BEGIN" -c "SELECT id AS claimable_unit FROM azk_odoo_partner_monitor_work_item
                        WHERE state = 'pending' ORDER BY id FOR NO KEY UPDATE SKIP LOCKED" -c "ROLLBACK"
}

[[ "$(grep -E '^ODOO_EDITION=' .env 2>/dev/null | cut -d= -f2-)" == "enterprise-20241208" ]] \
    || die "this check runs on the enterprise-20241208 edition (see .env)"
[[ "$(sql --tuples-only --no-align -c "SELECT state FROM ir_module_module
                                        WHERE name = 'azk_odoo_partner_monitor'")" == "installed" ]] \
    || die "$DB has no installed azk_odoo_partner_monitor; run scripts/dev.sh test azk_odoo_partner_monitor"

docker rm --force "$WORKER" > /dev/null 2>&1 || true  # a container left by an earlier attempt

echo "=== 1. Setup (committed)"
phase setup
state "before the worker starts"

echo
echo "=== 2. Worker started in container $WORKER (batch size 2)"
phase crash --name "$WORKER" > "$CRASH_LOG" 2>&1 &
worker_job=$!
for _ in $(seq 1 180); do
    grep -q "PM-RESTART: blocked" "$CRASH_LOG" 2>/dev/null && break
    kill -0 "$worker_job" 2>/dev/null || { cat "$CRASH_LOG"; die "the worker ended before blocking"; }
    sleep 1
done
grep -q "PM-RESTART: blocked" "$CRASH_LOG" || { cat "$CRASH_LOG"; die "the worker never reached batch 2"; }
grep "PM-RESTART" "$CRASH_LOG"
state "batch 1 committed, batch 2 in progress (only committed data is visible)"
sessions "Database sessions while batch 2 runs"

echo
echo "=== 3. docker kill $WORKER (SIGKILL) at $(date -u +%H:%M:%S) UTC"
docker kill "$WORKER" > /dev/null
wait "$worker_job" || echo "worker container exit status: $? (killed)"
sessions "Database sessions after the kill"
state "after the kill, before the restart"

echo
echo "=== 4. Restart: the worker job runs again in a new container"
phase resume | grep "PM-RESTART"
state "after the restart"

echo
echo "=== 5. Checks"
phase verify | grep "PM-RESTART"
rm -rf "$WORK_DIR"
