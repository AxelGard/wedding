# Build the printable invitation.
#
#   make          # rebuild the PDFs if anything changed (runs setup the first time)
#   make rebuild  # rebuild the PDFs even if nothing changed
#   make preview  # build, then open the PDF
#   make setup    # recreate .venv and .fonts from scratch
#   make clean    # remove the PDFs

PYTHON := .venv/bin/python
PDFS   := invitation.pdf invitation-front.pdf invitation-back.pdf
STAMP  := .venv/.setup-done

.PHONY: all rebuild preview setup clean

all: $(PDFS)

# One script writes all three PDFs; the first target stands in for the rest.
invitation.pdf: make_cards.py svgpath.py ../index.html $(STAMP)
	$(PYTHON) make_cards.py

invitation-front.pdf invitation-back.pdf: invitation.pdf

$(STAMP): setup.sh
	./setup.sh
	touch $@

setup:
	rm -f $(STAMP)
	$(MAKE) $(STAMP)

rebuild: $(STAMP)
	$(PYTHON) make_cards.py

preview: all
	open invitation.pdf

clean:
	rm -f $(PDFS)
