#!/usr/bin/env bash
# Development helper for the local Docker setup (see docs/environment.md).
# Use Git Bash on Windows, or any bash shell on Linux/macOS.
set -euo pipefail

# Git Bash rewrites arguments that look like POSIX paths (for example
# /var/lib/odoo); docker needs them unchanged.
export MSYS_NO_PATHCONV=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ADDONS_ALL="azk_odoo_partner_monitor,azk_dynamic_trial_balance"
DEV_DB="azk_dev"      # development and demo database, served by the web server
TEST_DB="azk_test"    # disposable: recreated by "test"
CLEAN_DB="azk_clean"  # disposable: recreated by "clean-install"
RESETTABLE_DBS=("$TEST_DB" "$CLEAN_DB")  # the only databases this script may drop
SOURCE_DIR="${ODOO_SOURCE_DIR:-$REPO_ROOT/../runtime/odoo18}"

usage() {
    cat <<'EOF'
Usage: scripts/dev.sh COMMAND [ARGS]

  setup                     create .env (random passwords) if missing, pull images,
                            start PostgreSQL and create azk_dev with both addons
  start | stop | restart    start/stop the web server (http://127.0.0.1:8069)
  status                    show container status
  logs                      follow the web server log
  install ADDONS [DB]       install addons (comma-separated) into DB (default azk_dev)
  update ADDONS [DB]        update addons in DB (default azk_dev)
  shell [DB]                Odoo shell on DB (default azk_dev); reads piped code if
                            stdin is not a terminal
  psql [DB]                 psql as the odoo role on DB (default azk_dev)
  test [ADDONS] [TAGS]      recreate azk_test, install ADDONS (default: both addons)
                            and run their tests; TAGS defaults to /addon1,/addon2
  clean-install [ADDONS]    recreate azk_clean and install ADDONS (default: both)
  reset-db azk_test|azk_clean
                            drop a disposable database and its filestore
  source                    copy the Odoo source from the pinned image to
                            ../runtime/odoo18 for reading (translations excluded)
EOF
}

die() { echo "error: $*" >&2; exit 1; }

compose() { docker compose "$@"; }

# Allocate a TTY only when both stdin and stdout are terminals.
tty_flag() { if [[ -t 0 && -t 1 ]]; then echo ""; else echo "-T"; fi; }

random_secret() { head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'; }

ensure_env() {
    [[ -f .env ]] && return
    echo "Creating .env with random local passwords (ignored by Git)."
    {
        echo "POSTGRES_PASSWORD=$(random_secret)"
        echo "ODOO_DB_PASSWORD=$(random_secret)"
        echo "ODOO_HTTP_PORT=8069"
    } > .env
}

db_up() { compose up --detach --wait db; }

db_exists() {
    [[ "$(compose exec -T db psql --username=odoo --dbname=postgres --tuples-only --no-align \
        --command="SELECT 1 FROM pg_database WHERE datname = '$1'")" == "1" ]]
}

server_running() { [[ -n "$(compose ps --status running --quiet odoo)" ]]; }

# Run a one-off Odoo process on DB in a temporary container.
odoo_run() {
    local db="$1"; shift
    compose run --rm -T odoo odoo --database="$db" --db-filter="^${db}\$" "$@"
}

reset_db() {
    local db="$1" allowed=0 name
    for name in "${RESETTABLE_DBS[@]}"; do [[ "$db" == "$name" ]] && allowed=1; done
    (( allowed )) || die "refusing to reset '$db'; only ${RESETTABLE_DBS[*]} can be reset"
    db_up
    echo "Dropping database $db and its filestore, if they exist."
    compose exec -T db dropdb --username=odoo --if-exists --force "$db"
    compose run --rm --no-deps -T --entrypoint rm odoo -rf "/var/lib/odoo/filestore/$db"
}

cmd_setup() {
    ensure_env
    compose pull --quiet
    db_up
    if db_exists "$DEV_DB"; then
        echo "$DEV_DB already exists; leaving it unchanged."
    else
        echo "Creating $DEV_DB with $ADDONS_ALL (demo data included)."
        odoo_run "$DEV_DB" --init="$ADDONS_ALL" --stop-after-init
    fi
    echo "Done. Start the server with: scripts/dev.sh start"
}

cmd_test() {
    local addons="${1:-$ADDONS_ALL}" tags="${2:-}" log rc summary
    [[ -n "$tags" ]] || tags="/${addons//,/,/}"
    reset_db "$TEST_DB"
    log="$(mktemp)"
    set +e
    odoo_run "$TEST_DB" --init="$addons" --test-tags="$tags" --stop-after-init 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    echo "----- test summary -----"
    grep -E "Starting .*\.test_|post-tests in|when loading database|(ERROR|FAIL):" "$log" || true
    # Odoo exits 0 when no test matched, so check the counted tests as well.
    summary="$(grep -E "of [0-9]+ tests when loading database" "$log" | tail -n 1 || true)"
    rm -f "$log"
    echo "odoo exit code: $rc"
    if [[ -z "$summary" ]]; then
        echo "error: no test summary found in the Odoo log" >&2; return 1
    elif [[ "$summary" =~ " of 0 tests " ]]; then
        echo "error: no tests ran; check ADDONS and TAGS" >&2; return 1
    fi
    return "$rc"
}

cmd_source() {
    mkdir -p "$SOURCE_DIR"
    echo "Copying the Odoo source from the pinned image to $SOURCE_DIR (translations excluded)."
    compose run --rm --no-deps -T --entrypoint tar odoo \
        -C /usr/lib/python3/dist-packages -cf - --exclude='*/i18n' odoo \
        | tar -xf - -C "$SOURCE_DIR" \
        || echo "note: some font symlinks cannot be created on Windows; code files are unaffected."
}

main() {
    local cmd="${1:-help}"
    [[ $# -gt 0 ]] && shift
    case "$cmd" in
        setup) cmd_setup ;;
        start) ensure_env; compose up --detach --wait db; compose up --detach odoo
               echo "Odoo: http://127.0.0.1:$(grep -E '^ODOO_HTTP_PORT=' .env | cut -d= -f2)/web/login" ;;
        stop) compose stop ;;
        restart) compose restart odoo ;;
        status) compose ps --all ;;
        logs) compose logs --follow --tail=200 odoo ;;
        install|update)
            local addons="${1:?addons required, comma-separated}" db="${2:-$DEV_DB}" flag
            [[ "$cmd" == install ]] && flag="--init" || flag="--update"
            db_up
            odoo_run "$db" "$flag=$addons" --stop-after-init
            if server_running; then compose restart odoo; fi ;;
        shell)
            local db="${1:-$DEV_DB}"
            db_up
            # shellcheck disable=SC2046
            compose run --rm $(tty_flag) odoo odoo shell --database="$db" --no-http ;;
        psql)
            local db="${1:-$DEV_DB}"
            db_up
            # shellcheck disable=SC2046
            compose exec $(tty_flag) db psql --username=odoo --dbname="$db" ;;
        test) cmd_test "$@" ;;
        clean-install)
            local addons="${1:-$ADDONS_ALL}"
            reset_db "$CLEAN_DB"
            odoo_run "$CLEAN_DB" --init="$addons" --stop-after-init
            echo "Installed $addons into a fresh $CLEAN_DB." ;;
        reset-db) reset_db "${1:?database name required}" ;;
        source) cmd_source ;;
        help|-h|--help) usage ;;
        *) usage; die "unknown command: $cmd" ;;
    esac
}

main "$@"
