# Astrology RPM spec (Fedora/RHEL-compatible).
# Version is passed at build time: rpmbuild --define "oa_version X.Y.Z"
%global oa_version %{?oa_version}%{!?oa_version:1.1.59}

Name:           astrology
Version:        %{oa_version}
Release:        1%{?dist}
Summary:        Astrology (GTK 4)
License:        GPL-3.0-or-later
URL:            https://github.com/YOUR_ORG/astrology
Source0:        astrology-%{version}.tar.gz
# pysweph ships a platform-specific extension module (not pure Python).
%global pysweph_version 2.10.3.6
# pip-built extension; skip auto debuginfo/debugsource subpackages.
%global debug_package %{nil}

BuildRequires:  gcc
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  gtk4
BuildRequires:  librsvg2
BuildRequires:  librsvg2-tools
BuildRequires:  ImageMagick

Requires:       python3
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       gtk4
Requires:       librsvg2
Requires:       librsvg2-tools
Requires:       ImageMagick

%description
Astrology is a fully featured open source astrology application using
GTK 4 and Swiss Ephemeris (pysweph bundled at package build time).

%prep
%autosetup -n astrology -p1

%build
# distutils; install happens in %%install

%install
rm -rf %{buildroot}
%{__python3} setup.py install --root=%{buildroot} --prefix=/usr
%{__python3} -m pip install --no-cache-dir --upgrade \
	--root %{buildroot} \
	--prefix %{_prefix} \
	'pysweph==%{pysweph_version}'
# Record the native module path (under lib64); dist-info is listed explicitly in %%files.
find %{buildroot} \
	! -path '*/lib/debug/*' \
	-name 'swisseph*.so' \
	-printf '/%%P\n' | sort -u > %{_builddir}/astrology-pysweph.files
if ! grep -q '\.so$' %{_builddir}/astrology-pysweph.files; then
	echo "pysweph native module (swisseph*.so) not found under %{buildroot}" >&2
	exit 1
fi

%files -f %{_builddir}/astrology-pysweph.files
%license README.md
%{_bindir}/astrology
%{_bindir}/astrology-api
%{python3_sitelib}/astrologymod/
%{python3_sitelib}/astrology_app/
%{python3_sitelib}/astrology_api/
%{python3_sitelib}/run_astrology.py
%{python3_sitelib}/__pycache__/run_astrology.cpython-*.pyc*
%{python3_sitelib}/astrology-%{version}-py*.egg-info/
%{python3_sitearch}/pysweph-%{pysweph_version}.dist-info/
%{_datadir}/applications/astrology.desktop
%{_datadir}/astrology/
%{_datadir}/swisseph/

%changelog
* Tue May 26 2026 Astrology <devel@astrology> - %{oa_version}-1
- GTK 4 stack; bundle pysweph %{pysweph_version} at build time
