#!/usr/bin/env bash
# Render.com Build Script for BarberX.info Flask App

set -o errexit

echo "🔧 BarberX.info - Render Build"
echo "Python version: $(python --version)"

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"

