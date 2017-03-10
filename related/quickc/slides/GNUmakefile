PDFLATEX = pdflatex
PDFLATEXFLAGS = -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all clean

all: slides.pdf

clean:
	-rm *.aux *.bbl *.blg *.dvi *.log *.out *.toc *.nav *.ps *.pdf *.snm

%.pdf: %.tex
	$(PDFLATEX) $(PDFLATEXFLAGS) -jobname $(basename $@) -draftmode $(basename $<)
	$(PDFLATEX) $(PDFLATEXFLAGS) -jobname $(basename $@) $(basename $<)
	$(PDFLATEX) $(PDFLATEXFLAGS) -jobname $(basename $@) $(basename $<)
