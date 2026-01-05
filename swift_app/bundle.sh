#!/bin/bash
set -e

APP_NAME="ActivityLogger"
BUILD_DIR=".build/arm64-apple-macosx/debug"
APP_BUNDLE="${APP_NAME}.app"
SOURCES_DIR="Sources/${APP_NAME}"

echo "Building App..."
swift build -c debug

echo "Creating App Bundle Structure..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

echo "Copying Executable..."
cp "${BUILD_DIR}/${APP_NAME}" "${APP_BUNDLE}/Contents/MacOS/"

echo "Copying Info.plist..."
# Use the Info.plist we created
cp "${SOURCES_DIR}/Info.plist" "${APP_BUNDLE}/Contents/Info.plist"

echo "Signing App (Ad-hoc)..."
codesign --force --deep -s - "${APP_BUNDLE}"

echo "✅ App Bundled: ${APP_BUNDLE}"
echo "To run: open ${APP_BUNDLE}"
