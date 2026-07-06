.PHONY: install

PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin

install:
	mkdir -p "$(BINDIR)"
	ln -sf "$(CURDIR)/incr" "$(BINDIR)/incr"
	@echo "Installed incr to $(BINDIR)/incr"
	@echo "Ensure $(BINDIR) is on your PATH."
