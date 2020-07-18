#!/usr/bin/env bash
trap 'rc=$?; echo "ERR at line ${LINENO} (rc: $rc)"; exit $rc' ERR
#trap 'rc=$?; echo "EXIT (rc: $rc)"; exit $rc' EXIT
set -u

function proceed() {
  read -p "Proceed? " -n 1 -r
  echo    # (optional) move to a new line
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
      [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
  fi
}

LATEST_TAG=$(git tag -l | tail -1)
LATEST_VERSION="${LATEST_TAG:1}"

echo "Latest version: ${LATEST_VERSION}"
read -p "Enter new version: " NEW_VERSION

echo "Update version in source files from ${LATEST_VERSION} to ${NEW_VERSION}."
proceed
sed -i "s/\/recipe-dl\/archive\/v${LATEST_VERSION}/\/recipe-dl\/archive\/v${NEW_VERSION}/g" README.md
sed -i "s/version = '${LATEST_VERSION}'/version = '${NEW_VERSION}'/g" setup.py
sed -i "s/__version__ = '${LATEST_VERSION}'/__version__ = '${NEW_VERSION}'/g" recipe_dl/recipe_dl.py

echo "See changes"
proceed
git diff

echo "Push changes to repository."
proceed
git add README.md
git add setup.py
git add recipe_dl/recipe_dl.py
git commit -m "Updating to ${NEW_VERSION}"
git push

echo "Test build."
proceed
python3 setup.py clean --all        # Clean the previous build package
python3 setup.py sdist bdist_wheel  # Create build package
pip3 install .                      # Install from local package
recipe-dl --quick-test

NEW_TAG="v${NEW_VERSION}"
echo "Create new tag (${NEW_TAG}) and build."
proceed
git tag -a $NEW_TAG -m "$NEW_TAG"   # Set github tag
python3 setup.py clean --all        # Clean the previous build package
python3 setup.py sdist bdist_wheel  # Create build package

echo "Push release." 
proceed
git push origin $NEW_TAG
