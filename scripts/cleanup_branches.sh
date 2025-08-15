#!/bin/bash
# cleanup_branches.sh - Automated Git branch cleanup script
# Part of chatty-commander Git hygiene policy

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=${DRY_RUN:-false}
VERBOSE=${VERBOSE:-false}
FORCE=${FORCE:-false}
DAYS_OLD=${DAYS_OLD:-30}
KEEP_BRANCHES=${KEEP_BRANCHES:-"main,master,develop,staging,production"}

# Function to print colored output
log() {
    local level=$1
    shift
    case $level in
        "INFO") echo -e "${BLUE}[INFO]${NC} $*" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $*" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $*" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $*" ;;
    esac
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Automated Git branch cleanup script for chatty-commander.

OPTIONS:
    -d, --dry-run           Show what would be deleted without actually deleting
    -v, --verbose           Show detailed output
    -f, --force             Force deletion without confirmation
    --days-old DAYS         Delete branches older than DAYS (default: 30)
    --keep BRANCHES         Comma-separated list of branches to keep (default: main,master,develop,staging,production)
    -h, --help              Show this help message

ENVIRONMENT VARIABLES:
    DRY_RUN=true           Same as --dry-run
    VERBOSE=true           Same as --verbose
    FORCE=true             Same as --force
    DAYS_OLD=N             Same as --days-old N
    KEEP_BRANCHES="..."     Same as --keep "..."

EXAMPLES:
    $0 --dry-run                    # Preview what would be cleaned
    $0 --days-old 14 --verbose      # Delete branches older than 14 days
    $0 --force                      # Clean without confirmation
    DAYS_OLD=7 $0                   # Use environment variable

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --days-old)
            DAYS_OLD="$2"
            shift 2
            ;;
        --keep)
            KEEP_BRANCHES="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log "ERROR" "Not in a Git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ -z "$CURRENT_BRANCH" ]]; then
    log "ERROR" "Unable to determine current branch (detached HEAD?)"
    exit 1
fi

log "INFO" "Current branch: $CURRENT_BRANCH"
log "INFO" "Cleanup configuration:"
log "INFO" "  - Days old threshold: $DAYS_OLD"
log "INFO" "  - Keep branches: $KEEP_BRANCHES"
log "INFO" "  - Dry run: $DRY_RUN"
log "INFO" "  - Force: $FORCE"

# Convert keep branches to array
IFS=',' read -ra KEEP_ARRAY <<< "$KEEP_BRANCHES"

# Function to check if branch should be kept
should_keep_branch() {
    local branch=$1

    # Always keep current branch
    if [[ "$branch" == "$CURRENT_BRANCH" ]]; then
        return 0
    fi

    # Check against keep list
    for keep in "${KEEP_ARRAY[@]}"; do
        if [[ "$branch" == "$keep" ]]; then
            return 0
        fi
    done

    return 1
}

# Function to get branch age in days
get_branch_age_days() {
    local branch=$1
    local last_commit_date

    last_commit_date=$(git log -1 --format="%ct" "$branch" 2>/dev/null || echo "0")
    if [[ "$last_commit_date" == "0" ]]; then
        echo "999999"  # Very old if we can't determine
        return
    fi

    local current_date
    current_date=$(date +%s)
    local age_seconds=$((current_date - last_commit_date))
    local age_days=$((age_seconds / 86400))

    echo "$age_days"
}

# Function to check if branch is merged
is_branch_merged() {
    local branch=$1
    local target_branch=${2:-"$CURRENT_BRANCH"}

    # Check if branch is merged into target
    git merge-base --is-ancestor "$branch" "$target_branch" 2>/dev/null
}

# Fetch latest changes and prune remote tracking branches
log "INFO" "Fetching latest changes and pruning remote branches..."
if [[ "$DRY_RUN" == "false" ]]; then
    git fetch --all --prune
else
    log "INFO" "[DRY RUN] Would run: git fetch --all --prune"
fi

# Clean up local branches
log "INFO" "Analyzing local branches..."
local_branches_to_delete=()
local_branches_kept=()

while IFS= read -r branch; do
    # Skip if should be kept
    if should_keep_branch "$branch"; then
        local_branches_kept+=("$branch")
        [[ "$VERBOSE" == "true" ]] && log "INFO" "Keeping branch: $branch (protected)"
        continue
    fi

    # Check age
    age_days=$(get_branch_age_days "$branch")
    if [[ "$age_days" -lt "$DAYS_OLD" ]]; then
        local_branches_kept+=("$branch")
        [[ "$VERBOSE" == "true" ]] && log "INFO" "Keeping branch: $branch (only $age_days days old)"
        continue
    fi

    # Check if merged
    if is_branch_merged "$branch"; then
        local_branches_to_delete+=("$branch:merged:$age_days")
        [[ "$VERBOSE" == "true" ]] && log "INFO" "Will delete: $branch (merged, $age_days days old)"
    else
        # Unmerged old branch - handle with care
        if [[ "$FORCE" == "true" ]]; then
            local_branches_to_delete+=("$branch:unmerged:$age_days")
            [[ "$VERBOSE" == "true" ]] && log "WARN" "Will force delete: $branch (unmerged, $age_days days old)"
        else
            local_branches_kept+=("$branch")
            [[ "$VERBOSE" == "true" ]] && log "WARN" "Keeping unmerged branch: $branch ($age_days days old) - use --force to delete"
        fi
    fi
done < <(git branch --format='%(refname:short)' | grep -v "^$CURRENT_BRANCH$")

# Clean up remote tracking branches for deleted remotes
log "INFO" "Analyzing remote tracking branches..."
remote_branches_to_delete=()

while IFS= read -r branch; do
    # Extract remote and branch name
    remote=$(echo "$branch" | cut -d'/' -f1)
    branch_name=$(echo "$branch" | cut -d'/' -f2-)

    # Skip if should be kept
    if should_keep_branch "$branch_name"; then
        [[ "$VERBOSE" == "true" ]] && log "INFO" "Keeping remote branch: $branch (protected)"
        continue
    fi

    # Check if remote branch still exists
    if ! git ls-remote --exit-code --heads "$remote" "$branch_name" >/dev/null 2>&1; then
        remote_branches_to_delete+=("$branch")
        [[ "$VERBOSE" == "true" ]] && log "INFO" "Will delete remote tracking: $branch (remote branch deleted)"
    fi
done < <(git branch -r --format='%(refname:short)' | grep -v 'HEAD')

# Show summary
log "INFO" "Cleanup summary:"
log "INFO" "  - Local branches to delete: ${#local_branches_to_delete[@]}"
log "INFO" "  - Remote tracking branches to delete: ${#remote_branches_to_delete[@]}"
log "INFO" "  - Branches kept: ${#local_branches_kept[@]}"

if [[ ${#local_branches_to_delete[@]} -eq 0 && ${#remote_branches_to_delete[@]} -eq 0 ]]; then
    log "SUCCESS" "No branches to clean up!"
    exit 0
fi

# Show what will be deleted
if [[ ${#local_branches_to_delete[@]} -gt 0 ]]; then
    log "INFO" "Local branches to delete:"
    for branch_info in "${local_branches_to_delete[@]}"; do
        IFS=':' read -r branch status age <<< "$branch_info"
        if [[ "$status" == "merged" ]]; then
            echo "  - $branch (merged, $age days old)"
        else
            echo "  - $branch (unmerged, $age days old) [FORCE]"
        fi
    done
fi

if [[ ${#remote_branches_to_delete[@]} -gt 0 ]]; then
    log "INFO" "Remote tracking branches to delete:"
    for branch in "${remote_branches_to_delete[@]}"; do
        echo "  - $branch"
    done
fi

# Confirm deletion unless dry run or force
if [[ "$DRY_RUN" == "false" && "$FORCE" == "false" ]]; then
    echo
    read -p "Proceed with deletion? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Cleanup cancelled"
        exit 0
    fi
fi

# Perform deletions
if [[ "$DRY_RUN" == "true" ]]; then
    log "INFO" "[DRY RUN] No actual deletions performed"
else
    # Delete local branches
    for branch_info in "${local_branches_to_delete[@]}"; do
        IFS=':' read -r branch status age <<< "$branch_info"
        if [[ "$status" == "merged" ]]; then
            if git branch -d "$branch" 2>/dev/null; then
                log "SUCCESS" "Deleted merged branch: $branch"
            else
                log "ERROR" "Failed to delete branch: $branch"
            fi
        else
            # Force delete unmerged branch
            if git branch -D "$branch" 2>/dev/null; then
                log "SUCCESS" "Force deleted unmerged branch: $branch"
            else
                log "ERROR" "Failed to force delete branch: $branch"
            fi
        fi
    done

    # Delete remote tracking branches
    for branch in "${remote_branches_to_delete[@]}"; do
        if git branch -dr "$branch" 2>/dev/null; then
            log "SUCCESS" "Deleted remote tracking branch: $branch"
        else
            log "ERROR" "Failed to delete remote tracking branch: $branch"
        fi
    done
fi

# Final cleanup - remove any stale worktree references
if [[ "$DRY_RUN" == "false" ]]; then
    log "INFO" "Cleaning up stale worktree references..."
    git worktree prune 2>/dev/null || true
fi

log "SUCCESS" "Branch cleanup completed!"

# Show final status
if [[ "$VERBOSE" == "true" ]]; then
    echo
    log "INFO" "Current branches:"
    git branch -vv
fi
