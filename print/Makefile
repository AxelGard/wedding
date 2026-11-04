# Build the printable invitation.
#
#   make          # rebuild the PDFs if anything changed (runs setup the first time)
#   make rebuild  # rebuild the PDFs even if nothing changed
#   make preview  # build, then open the PDF
#   make setup    # recreate .venv and .fonts from scratch
#   make clean    # remove the PDFs

PYTHON := .venv/bin/python
PDFS   := invitation-5x7.pdf invitation-5x7-front.pdf invitation-5x7-back.pdf
STAMP  := .venv/.setup-done

.PHONY: all rebuild preview setup clean

all: $(PDFS)

# One script writes all three PDFs; the first target stands in for the rest.
invitation-5x7.pdf: make_cards.py svgpath.py ../index.html $(STAMP)
	$(PYTHON) make_cards.py

invitation-5x7-front.pdf invitation-5x7-back.pdf: invitation-5x7.pdf

$(STAMP): setup.sh
	./setup.sh
	touch $@

setup:
	rm -f $(STAMP)
	$(MAKE) $(STAMP)

rebuild: $(STAMP)
	$(PYTHON) make_cards.py

preview: all
	open invitation-5x7.pdf

clean:
	rm -f $(PDFS)
