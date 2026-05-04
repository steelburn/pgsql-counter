#!/bin/bash
# Docker Test Database Helper Script
# Manages PostgreSQL test container for migration script testing

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="test-postgres-migration"
PORT="5434"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    cat << EOF
PostgreSQL Test Database Helper

Usage: $0 <command> [options]

Commands:
  start       Start the PostgreSQL test container
  stop        Stop the test container
  restart     Restart the test container
  status      Show container status
  logs        Show container logs (tail -f)
  shell       Open psql shell to test database
  cleanup     Remove container and volumes completely
  test        Run full test suite (count + report)

Connection Details (when running):
  Host:     localhost
  Port:     $PORT
  User:     testuser
  Password: testpass
  Database: test_migration

Examples:
  $0 start          # Start container
  $0 logs           # View logs
  $0 shell          # Connect with psql
  $0 test           # Run full test
  $0 cleanup        # Remove everything

EOF
}

start_container() {
    echo -e "${YELLOW}Starting PostgreSQL test container...${NC}"
    
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}Container already running${NC}"
        return 0
    fi
    
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo "Container exists but not running, starting..."
        docker start $CONTAINER_NAME
    else
        echo "Creating new container..."
        docker run -d --name $CONTAINER_NAME \
          -e POSTGRES_USER=testuser \
          -e POSTGRES_PASSWORD=testpass \
          -e POSTGRES_DB=test_migration \
          -p $PORT:5432 \
          -v "$PROJECT_DIR/init-db.sql:/docker-entrypoint-initdb.d/01-init.sql" \
          -v "$PROJECT_DIR/test-data.sql:/docker-entrypoint-initdb.d/02-test-data.sql" \
          postgres:15-alpine
    fi
    
    echo "Waiting for database to be ready..."
    sleep 10
    
    # Check if database is ready
    for i in {1..30}; do
        if docker exec $CONTAINER_NAME psql -U testuser -d test_migration -c "SELECT 1" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Container ready${NC}"
            show_connection_info
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${RED}✗ Container failed to start${NC}"
    return 1
}

stop_container() {
    echo -e "${YELLOW}Stopping PostgreSQL test container...${NC}"
    
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "Container not running"
        return 0
    fi
    
    docker stop $CONTAINER_NAME
    echo -e "${GREEN}✓ Container stopped${NC}"
}

restart_container() {
    stop_container
    sleep 2
    start_container
}

show_status() {
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}✓ Container is running${NC}"
        docker ps | grep $CONTAINER_NAME
        show_connection_info
    elif docker ps -a | grep -q $CONTAINER_NAME; then
        echo -e "${YELLOW}○ Container exists but not running${NC}"
        docker ps -a | grep $CONTAINER_NAME
    else
        echo -e "${RED}✗ Container not found${NC}"
    fi
}

show_logs() {
    docker logs -f $CONTAINER_NAME
}

open_shell() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${RED}Container not running${NC}"
        return 1
    fi
    
    echo "Opening psql shell..."
    docker exec -it $CONTAINER_NAME psql -U testuser -d test_migration
}

show_connection_info() {
    cat << EOF

${GREEN}Connection Details:${NC}
  Host:     localhost
  Port:     $PORT
  User:     testuser
  Password: testpass
  Database: test_migration

Quick commands:
  Connect:  psql -h localhost -p $PORT -U testuser -d test_migration
  Docker:   docker exec -it $CONTAINER_NAME psql -U testuser -d test_migration
  
EOF
}

cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo "Stopping container..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        echo "Removing container..."
        docker rm $CONTAINER_NAME
    fi
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

run_full_test() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${YELLOW}Container not running, starting...${NC}"
        start_container
    fi
    
    cd "$PROJECT_DIR"
    
    echo -e "${YELLOW}Running full test suite...${NC}"
    echo ""
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}Virtual environment not found${NC}"
        return 1
    fi
    
    source venv/bin/activate
    
    mkdir -p test_reports
    
    # Pre-migration count
    echo -e "${YELLOW}1. Running pre-migration count...${NC}"
    python migration_counter.py --mode pre \
      --host localhost \
      --port $PORT \
      --user testuser \
      --password testpass \
      --database test_migration \
      --output-dir test_reports \
      --workers 10
    echo ""
    
    # Simulate changes
    echo -e "${YELLOW}2. Simulating migration data changes...${NC}"
    docker exec $CONTAINER_NAME psql -U testuser -d test_migration << 'EOSQL'
DELETE FROM public.order_items WHERE id > 800;
INSERT INTO public.notifications (user_id, type, title, message, is_read) VALUES (1, 'test', 'Changes detected', 'Data migration completed', true);
EOSQL
    echo "✓ Data changes simulated"
    echo ""
    
    # Post-migration count
    echo -e "${YELLOW}3. Running post-migration count...${NC}"
    python migration_counter.py --mode post \
      --host localhost \
      --port $PORT \
      --user testuser \
      --password testpass \
      --database test_migration \
      --output-dir test_reports
    echo ""
    
    # Generate reports
    echo -e "${YELLOW}4. Generating comparison reports...${NC}"
    python migration_reporter.py \
      --pre test_reports/pre_migration_count.json \
      --post test_reports/post_migration_count.json \
      --output both \
      --output-dir test_reports
    echo ""
    
    # Summary
    echo -e "${GREEN}✓ Test suite completed${NC}"
    echo ""
    echo "Output files:"
    ls -lh test_reports/
    echo ""
    echo -e "${YELLOW}View HTML report:${NC}"
    echo "  Open: test_reports/migration_report.html"
    echo ""
    echo -e "${YELLOW}View CSV report:${NC}"
    echo "  cat test_reports/migration_report.csv"
}

# Main logic
case "${1:-help}" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    cleanup)
        cleanup
        ;;
    test)
        run_full_test
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        print_usage
        exit 1
        ;;
esac
