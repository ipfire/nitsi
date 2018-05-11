ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}
AM_MAKEFLAGS = --no-print-directory
AUTOMAKE_OPTIONS = color-tests

# remove target it the command fails
.DELETE_ON_ERROR:

# keep itermediate files
.SECONDARY:

pythondir  = $(pyexecdir)

CLEANFILES =
DISTCLEANFILES =
EXTRA_DIST =
INSTALL_DIRS =
noinst_DATA =


AM_V_XSLT   = $(AM_V_XSLT_$(V))
AM_V_XSLT_  = $(AM_V_XSLT_$(AM_DEFAULT_VERBOSITY))
AM_V_XSLT_0 = @echo "  XSLT    " $@;

bin_SCRIPTS = \
	nitsi

CLEANFILES += \
	nitsi

nitsi_PYTHON = \
	src/nitsi/__init__.py \
	src/nitsi/disk.py \
	src/nitsi/logger.py \
	src/nitsi/machine.py \
	src/nitsi/network.py \
	src/nitsi/recipe.py \
	src/nitsi/serial_connection.py \
	src/nitsi/test.py \
	src/nitsi/virtual_environ.py


nitsidir = $(pythondir)/nitsi

# ------------------------------------------------------------------------------

.PHONY: man
man: $(MANPAGES) $(MANPAGES_HTML)

if ENABLE_MANPAGES
MANPAGES = \
	man/nitsi.1 \
	man/nitsi.settings.1 \
	man/nitsi.recipe.1

MANPAGES_XML  = $(patsubst %.1,%.xml,$(patsubst %.5,%.xml,$(MANPAGES)))
MANPAGES_HTML = $(patsubst %.xml,%.html,$(MANPAGES_XML))

man_MANS = \
	$(MANPAGES)

noinst_DATA += \
	$(MANPAGES_HTML)

CLEANFILES += \
	$(man_MANS) \
	$(MANPAGES_HTML)

EXTRA_DIST += \
	$(MANPAGES_XML) \
	man/custom-html.xsl

XSLTPROC_FLAGS = \
	--nonet \
	--stringparam man.output.quietly 1 \
	--stringparam funcsynopsis.style ansi \
	--stringparam man.th.extra1.suppress 1 \
	--stringparam man.authors.section.enabled 1 \
	--stringparam man.copyright.section.enabled 1

XSLTPROC_COMMAND_MAN = \
	$(AM_V_XSLT)$(XSLTPROC) -o $@ $(XSLTPROC_FLAGS) \
		http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl $<

XSLTPROC_COMMAND_HTML = \
	$(AM_V_XSLT)$(XSLTPROC) -o $@ $(XSLTPROC_FLAGS) $(srcdir)/man/custom-html.xsl $<

man/%.1: man/%.xml
	$(XSLTPROC_COMMAND_MAN)

man/%.5: man/%.xml
	$(XSLTPROC_COMMAND_MAN)

man/%.html: man/%.xml man/custom-html.xsl
	$(XSLTPROC_COMMAND_HTML)

endif

# ------------------------------------------------------------------------------

substitutions = \
	'|PACKAGE_NAME=$(PACKAGE_NAME)|' \
	'|PACKAGE_VERSION=$(PACKAGE_VERSION)|'

SED_PROCESS = \
	$(AM_V_GEN)$(MKDIR_P) $(dir $@) && \
	$(SED) $(subst '|,-e 's|@,$(subst =,\@|,$(subst |',|g',$(substitutions)))) \
		< $< > $@

nitsi: nitsi.in Makefile
	$(SED_PROCESS)