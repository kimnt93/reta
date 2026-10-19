SHELL := /bin/bash
HARNESS ?= codex
REA_CLIENT ?= codex
REA_VERSION ?= 6.7.0
BSK_VERSION ?= 0.3.3
TOOLS := $(CURDIR)/.tools
export PATH := $(TOOLS)/npm/node_modules/.bin:$(TOOLS)/bin:$(PATH)

.PHONY: help install install-browser install-harness install-rea \
	install-browser-skill install-skills setup-browser-skill rea-plan \
	setup-rea bootstrap check demo doctor

help:
	@printf '%s\n' \
	  'make install                 Install locked Python dependencies' \
	  'make install-browser         Install Playwright Chromium (no sudo)' \
	  'make install-harness         Reuse/install HARNESS=codex|claude|hermes' \
	  'make install-rea             Install project-local REA CLI' \
	  'make install-browser-skill   Install checksum-verified bsk CLI locally' \
	  'make install-skills          Install RETA skills for HARNESS' \
	  'make setup-browser-skill     Install upstream browser-skill guidance' \
	  'make rea-plan                Preview REA stdio MCP registration' \
	  'make setup-rea               Interactive reviewed REA registration' \
	  'make bootstrap               Install all tools + RETA skills' \
	  'make demo                    Run actual synthetic alpha recovery' \
	  'make check                   Format/lint/behavior tests' \
	  'make doctor                  Inspect tool/extension readiness'

install:
	uv sync --locked --group dev

install-browser:
	uv run playwright install chromium

install-harness:
	python3 scripts/install_tools.py harness --harness "$(HARNESS)"

install-rea:
	python3 scripts/install_tools.py rea --version "$(REA_VERSION)"

install-browser-skill:
	python3 scripts/install_tools.py browser-skill --version "$(BSK_VERSION)"

install-skills:
	uv run reta skills install --harness "$(HARNESS)"

setup-browser-skill:
	bsk install-skill --harness "$(HARNESS)" --json

rea-plan:
	rea setup --client "$(REA_CLIENT)" --dry-run --json

setup-rea:
	rea setup --client "$(REA_CLIENT)"

bootstrap: install install-harness install-rea install-browser-skill install-browser install-skills

check:
	uv run ruff format --check src tests scripts skills
	uv run ruff check src tests scripts skills
	uv run pycodestyle --max-line-length=79 src tests scripts skills
	uv run pytest

demo:
	uv run reta demo

doctor:
	uv run reta --version
	@command -v "$(HARNESS)"
	rea --version
	bsk --version
	bsk doctor
