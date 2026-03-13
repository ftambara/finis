#!/usr/bin/env just --justfile

# Display available recipes.
[default]
help:
    @just --list

# Format the codebase.
fmt:
    go tool gofumpt -w .

# Run fast static analysis checks.
lint-fast:
    @just lint --fast-only

# Run static analysis. Use `just lint-fast` for a quicker subset.
lint *flags:
    @echo "==> Running static analysis"
    @golangci-lint run {{flags}} ./...

# Build the web UI binary.
build-web:
    @go build -o bin/web ./cmd/web

# Run the web UI.
run-web *args: build-web
    @./bin/web {{args}}
