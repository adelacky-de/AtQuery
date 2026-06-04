#!/bin/bash
# Kardia Release Script
# ──────────────────────────────────────────────
# Versioning Convention:
#   testing branch   → patch bump:  X.X.+1  (e.g. 1.0.1)
#   production merge → major bump:  +1.X.X  (e.g. 2.0.0)
#   minor hotfix     → minor bump:  X.+1.X  (e.g. 2.1.0)
# ──────────────────────────────────────────────
set -e

VERSION=$1
BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh <version>"
  echo ""
  echo "Versioning convention:"
  echo "  testing branch   → patch bump:  X.X.+1  (e.g. 1.0.1)"
  echo "  production merge → major bump:  +1.X.X  (e.g. 2.0.0)"
  echo "  minor hotfix     → minor bump:  X.+1.X  (e.g. 2.1.0)"
  exit 1
fi

# Validate version format (must be vMAJOR.MINOR.PATCH)
if ! echo "$VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "❌ Invalid version format: $VERSION"
  echo "   Expected format: vMAJOR.MINOR.PATCH (e.g. v1.0.2, v2.0.0)"
  exit 1
fi

echo "📦 Releasing $VERSION from branch: $BRANCH"

if [ "$BRANCH" = "testing" ]; then
  # Patch release — merge testing into production
  git checkout production && git merge testing
elif [ "$BRANCH" = "production" ]; then
  # Major release — already on production branch, just tag
  echo "ℹ️  Already on production branch — tagging as major release"
else
  # Minor hotfix — merge current branch into production
  echo "ℹ️  Minor hotfix branch detected — merging into production"
  git checkout production && git merge "$BRANCH"
fi

git tag -a "$VERSION" -m "Release $VERSION"
git push origin production:main --tags
echo "✅ Released $VERSION to main"
