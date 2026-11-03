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
SOURCE_DIR="${ODOO_SOURCE_DIR:-$REPO_ROOT/../runtime/odoo18}"

die() { echo "error: $*" >&2; exit 1; }

# Value of KEY from .env (empty if unset).
env_file_value() {
    [[ -f .env ]] || return 0
    grep -E "^$1=" .env | tail -n 1 | cut -d= -f2- || true
}

# Edition: "community" (the Stage 01 baseline) or "enterprise" (the confirmed
# target, Stage 01B). Set ODOO_EDITION in .env, or per command, for example
# ODOO_EDITION=community scripts/dev.sh test
EDITION="${ODOO_EDITION:-$(env_file_value ODOO_EDITION)}"
EDITION="${EDITION:-community}"
ENTERPRISE_ADDONS="${ENTERPRISE_ADDONS:-$(env_file_value ENTERPRISE_ADDONS)}"

case "$EDITION" in
    community)
        SERVICE="odoo"
        DEV_DB="azk_dev"          # development and demo database, served by the web server
        TEST_DB="azk_test"        # disposable: recreated by "test"
        CLEAN_DB="azk_clean"      # disposable: recreated by "clean-install"
        PORT_KEY="ODOO_HTTP_PORT"; PORT_DEFAULT=8069
        SETUP_MODULES="$ADDONS_ALL" ;;
    enterprise)
        SERVICE="odoo-ee"
        DEV_DB="azk_ent"
        TEST_DB="azk_ent_test"
        CLEAN_DB="azk_ent_clean"
        PORT_KEY="ODOO_EE_HTTP_PORT"; PORT_DEFAULT=8070
        # web_enterprise: the Enterprise web client. accountant: the Accounting
        # app, which brings account_accountant and, by auto-install, account_reports.
        SETUP_MODULES="web_enterprise,accountant,$ADDONS_ALL" ;;
    *) die "ODOO_EDITION must be community or enterprise, not '$EDITION'" ;;
esac
RESETTABLE_DBS=("$TEST_DB" "$CLEAN_DB")  # the only databases this script may drop

# The Enterprise service lives in the "enterprise" compose profile. Enable the
# profile whenever an Enterprise addons folder is configured, so that status and
# stop also cover that service.
if [[ -n "$ENTERPRISE_ADDONS" ]]; then export COMPOSE_PROFILES=enterprise; fi

usage() {
    cat <<'EOF'
Usage: scripts/dev.sh COMMAND [ARGS]

The edition comes from ODOO_EDITION (environment or .env): "community"
(service odoo, databases azk_dev/azk_test/azk_clean, port 8069) or
"enterprise" (service odoo-ee, databases azk_ent/azk_ent_test/azk_ent_clean,
port 8070, needs ENTERPRISE_ADDONS). Default: community.
Example: ODOO_EDITION=community scripts/dev.sh test

  setup                     create .env (random passwords) if missing, pull images,
                            start PostgreSQL and create the development database
                            (enterprise: with web_enterprise and accountant)
  start | stop | restart    start/stop the web server of the edition
  status                    show container status
  logs                      follow the web server log
  install ADDONS [DB]       install addons (comma-separated) into DB (default: dev DB)
  update ADDONS [DB]        update addons in DB (default: dev DB)
  shell [DB]                Odoo shell on DB (default: dev DB); reads piped code if
                            stdin is not a terminal
  psql [DB]                 psql as the odoo role on DB (default: dev DB)
  test [ADDONS] [TAGS]      recreate the test DB, install ADDONS (default: both addons)
                            and run their tests; TAGS defaults to /addon1,/addon2
  clean-install [ADDONS]    recreate the clean DB and install ADDONS (default: both)
  reset-db DB               drop a disposable database (test or clean DB of the
                            edition) and its filestore
  source                    copy the Odoo Community source from the pinned image to
                            ../runtime/odoo18 for reading (translations excluded)
EOF
}

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
        echo "ODOO_EDITION=community"
        echo "ENTERPRISE_ADDONS="
        echo "ODOO_EE_HTTP_PORT=8070"
    } > .env
}

# Enterprise commands need a readable Enterprise addons folder.
check_enterprise_addons() {
    [[ "$EDITION" == enterprise ]] || return 0
    [[ -n "$ENTERPRISE_ADDONS" ]] || die "ODOO_EDITION=enterprise needs ENTERPRISE_ADDONS in .env (see .env.example)"
    local dir="$ENTERPRISE_ADDONS"
    [[ "$dir" = /* || "$dir" =~ ^[A-Za-z]: ]] || dir="$REPO_ROOT/$dir"
    [[ -f "$dir/web_enterprise/__manifest__.py" ]] \
        || die "ENTERPRISE_ADDONS ($ENTERPRISE_ADDONS) has no web_enterprise module"
}

# Keep each edition on its own databases. Opening a Community database with the
# Enterprise addons path would auto-install web_enterprise into it on the next
# install, and an Enterprise database cannot load without the Enterprise addons.
check_db_edition() {
    local db="$1"
    if [[ "$EDITION" == enterprise && ! "$db" =~ ^azk_ent(_|$) ]]; then
        die "the enterprise edition only uses azk_ent* databases, not '$db'"
    elif [[ "$EDITION" == community && "$db" =~ ^azk_ent(_|$) ]]; then
        die "'$db' is an Enterprise database; use ODOO_EDITION=enterprise"
    fi
}

db_up() { compose up --detach --wait db; }

db_exists() {
    [[ "$(compose exec -T db psql --username=odoo --dbname=postgres --tuples-only --no-align \
        --command="SELECT 1 FROM pg_database WHERE datname = '$1'")" == "1" ]]
}

server_running() { [[ -n "$(compose ps --status running --quiet "$SERVICE")" ]]; }

# Run a one-off Odoo process on DB in a temporary container.
odoo_run() {
    local db="$1"; shift
    check_db_edition "$db"
    compose run --rm -T "$SERVICE" odoo --database="$db" --db-filter="^${db}\$" "$@"
}

reset_db() {
    local db="$1" allowed=0 name
    for name in "${RESETTABLE_DBS[@]}"; do [[ "$db" == "$name" ]] && allowed=1; done
    (( allowed )) || die "refusing to reset '$db'; only ${RESETTABLE_DBS[*]} can be reset ($EDITION edition)"
    db_up
    echo "Dropping database $db and its filestore, if they exist."
    compose exec -T db dropdb --username=odoo --if-exists --force "$db"
    compose run --rm --no-deps -T --entrypoint rm "$SERVICE" -rf "/var/lib/odoo/filestore/$db"
}

cmd_setup() {
    ensure_env
    check_enterprise_addons
    compose pull --quiet
    db_up
    if db_exists "$DEV_DB"; then
        echo "$DEV_DB already exists; leaving it unchanged."
    else
        echo "Creating $DEV_DB with $SETUP_MODULES (demo data included)."
        odoo_run "$DEV_DB" --init="$SETUP_MODULES" --stop-after-init
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
    echo "----- test summary ($EDITION) -----"
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
        help|-h|--help|status|stop|source) ;;
        *) echo "edition: $EDITION (service $SERVICE, database $DEV_DB)" >&2
           check_enterprise_addons ;;
    esac
    case "$cmd" in
        setup) cmd_setup ;;
        start) ensure_env; db_up; compose up --detach "$SERVICE"
               local port; port="$(env_file_value "$PORT_KEY")"
               echo "Odoo ($EDITION): http://127.0.0.1:${port:-$PORT_DEFAULT}/web/login" ;;
        stop) compose stop ;;
        restart) compose restart "$SERVICE" ;;
        status) compose ps --all ;;
        logs) compose logs --follow --tail=200 "$SERVICE" ;;
        install|update)
            local addons="${1:?addons required, comma-separated}" db="${2:-$DEV_DB}" flag
            [[ "$cmd" == install ]] && flag="--init" || flag="--update"
            check_db_edition "$db"
            db_up
            odoo_run "$db" "$flag=$addons" --stop-after-init
            if server_running; then compose restart "$SERVICE"; fi ;;
        shell)
            local db="${1:-$DEV_DB}"
            check_db_edition "$db"
            db_up
            # shellcheck disable=SC2046
            compose run --rm $(tty_flag) "$SERVICE" odoo shell --database="$db" --no-http ;;
        psql)
            local db="${1:-$DEV_DB}"
            check_db_edition "$db"
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
        help|-h|--help) usage ;;
        *) usage; die "unknown command: $cmd" ;;
    esac
}

main "$@"
