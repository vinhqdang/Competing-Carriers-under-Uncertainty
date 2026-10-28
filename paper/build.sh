#!/bin/sh
# usage: build.sh main|supplement
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode $1.tex >/dev/null; bibtex $1 >/dev/null; pdflatex -interaction=nonstopmode $1.tex >/dev/null; pdflatex -interaction=nonstopmode $1.tex | tail -2
grep -c '^!' $1.log; grep -i 'undefined\|multiply' $1.log | sort | uniq -c | head -20
