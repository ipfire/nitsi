AC_PREREQ([2.64])

AC_INIT([nitsi],
	[0.9],
	[info@ipfire.org],
	[nitsi],
	[https://git.ipfire.org/pub/git/people/jschlag/nitsi.git])

AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_AUX_DIR([build-aux])

AC_PREFIX_DEFAULT([/usr])

AM_INIT_AUTOMAKE([
	foreign
	1.11
	-Wall
	-Wno-portability
	silent-rules
	tar-pax
	subdir-objects
])
AM_SILENT_RULES([yes])

AC_PROG_LN_S
AC_PROG_MKDIR_P
AC_PROG_SED

AC_PATH_PROG([XSLTPROC], [xsltproc])

# Python
AM_PATH_PYTHON([3.5])

AX_PYTHON_MODULE([libvirt], [fatal], [python3])
AX_PYTHON_MODULE([guestfs], [fatal], [python3])
AX_PYTHON_MODULE([serial], [fatal], [python3])

save_LIBS="$LIBS"

# pkg-config
PKG_PROG_PKG_CONFIG
# This makes sure pkg.m4 is available.
m4_pattern_forbid([^_?PKG_[A-Z_]+$],[*** pkg.m4 missing, please install pkg-config])

# ------------------------------------------------------------------------------
have_manpages=no
AC_ARG_ENABLE(manpages, AS_HELP_STRING([--disable-man-pages],
	[do not install man pages]))
AS_IF([test "x$enable_manpages" != xno], [have_manpages=yes])
AM_CONDITIONAL(ENABLE_MANPAGES, [test "x$have_manpages" = "xyes"])

# ------------------------------------------------------------------------------

AC_CONFIG_FILES([
	Makefile
])

AC_OUTPUT
AC_MSG_RESULT([
	${PACKAGE_NAME} ${VERSION}

	prefix:			${prefix}
	sysconfdir:		${sysconfdir}

	Generate man-pages:	${have_manpages}
])