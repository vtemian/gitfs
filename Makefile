PREFIX:=/usr/local
BUILD_DIR:=build
VENV_DIR?=$(BUILD_DIR)/.venv

TESTS?=tests
PYTHON?=3.11
TEST_DIR:=/tmp/gitfs-tests
MNT_DIR:=$(TEST_DIR)/$(shell bash -c 'echo $$RANDOM')_mnt
REPO_DIR:=$(TEST_DIR)/$(shell bash -c 'echo $$RANDOM')_repo
REPO_NAME:=testing_repo
BARE_REPO:=$(TEST_DIR)/$(REPO_NAME).git
export
REMOTE:=$(TEST_DIR)/$(REPO_NAME)
GITFS_PID:=$(TEST_DIR)/gitfs.pid
GIT_NAME=GitFs
GIT_EMAIL=gitfs@gitfs.com

all: $(BUILD_DIR)/gitfs

install: $(BUILD_DIR)/gitfs
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	install -m 0755 $(BUILD_DIR)/gitfs $(DESTDIR)$(PREFIX)/bin/gitfs

uninstall:
	rm -rf $(DESTDIR)$(PREFIX)/bin/gitfs

$(BUILD_DIR)/gitfs: $(BUILD_DIR) venv-dev
	uv run pex -v --disable-cache -e gitfs:mount -o $(BUILD_DIR)/gitfs .

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

venv-dev: uv.lock
	uv sync --extra dev

venv-test: uv.lock  
	uv sync --extra test

venv-docs: uv.lock
	uv sync --extra docs

uv.lock: pyproject.toml
	uv lock

testenv: venv-test
	script/testenv

test: clean testenv
	script/test

clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(TEST_DIR)
	rm -rf .venv

format: venv-dev
	uv run ruff format gitfs

lint: venv-dev
	uv run ruff format --check gitfs

verify-lint: lint
	git diff --exit-code

.PHONY: docs
docs: venv-docs
	uv run mkdocs build --clean

.PHONY: gh-pages
gh-pages: docs
	git config --global user.email "bot@presslabs.com"
	git config --global user.name "Igor Debot"
	cp docs/index.html .
	git add .
	echo -n "(autodoc) " > /tmp/COMMIT_MESSAGE ; git log -1 --pretty=%B >> /tmp/COMMIT_MESSAGE ; echo >> /tmp/COMMIT_MESSAGE ; echo "Commited-By: $$CI_BUILD_URL" >> /tmp/COMMIT_MESSAGE
	git commit -F /tmp/COMMIT_MESSAGE

.PHONY: clean test testenv venv-dev venv-test venv-docs all format lint verify-lint docs gh-pages
