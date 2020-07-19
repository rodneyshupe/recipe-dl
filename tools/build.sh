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
function beginswith() {
  case $2 in
    "$1"*)
      true;;
    *)
      false;;
  esac;
}

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null && cd .. > /dev/null && pwd )"

LATEST_TAG=$(git tag -l | tail -1)
if [ "${LATEST_TAG}" == "" ]; then
  LATEST_TAG="v0.0.0"
fi
LATEST_VERSION="${LATEST_TAG:1}"

echo "Latest version: ${LATEST_VERSION}"
read -p "Step 1: Enter new version: " NEW_VERSION
NEW_TAG="v${NEW_VERSION}"

echo
echo "Step 2: Update version in source files from ${LATEST_VERSION} to ${NEW_VERSION}."
proceed
sed -i "s/\/archive\/${LATEST_TAG}/\/archive\/${NEW_TAG}/g" "$ROOT_DIR/README.md"
sed -i "s/\/archive\/${LATEST_VERSION}/\/archive\/${NEW_VERSION}/g" "$ROOT_DIR/README.md"
sed -i "s/version = '${LATEST_VERSION}'/version = '${NEW_VERSION}'/g" "$ROOT_DIR/setup.py"
for file in $(find "${ROOT_DIR}" -type f -name "*.py" ); do
  if beginswith "${ROOT_DIR}/build" "${file}"; then
    : # Ignore file.
  else
    sed -i "s/__version__ = '${LATEST_VERSION}'/__version__ = '${NEW_VERSION}'/g" "$file"
  fi
done

echo
echo "Step 3: Preview changes."
proceed
git diff

echo
echo "Step 4: Push changes to repository."
proceed
git add $ROOT_DIR
git commit -m "Updating to ${NEW_VERSION}"
git push

echo
echo "Step 5: Test build."
proceed
python3 setup.py clean --all        # Clean the previous build package
python3 setup.py sdist bdist_wheel  # Create build package
pip3 install .                      # Install from local package

recipe-dl --quick-test

echo
echo "Step 6: Create new tag (${NEW_TAG}) and build."
proceed
git tag -a $NEW_TAG -m "$NEW_TAG"   # Set github tag
python3 setup.py clean --all        # Clean the previous build package
python3 setup.py sdist bdist_wheel  # Create build package

echo
echo "Step 7: Push release."
proceed
git push origin $NEW_TAG
