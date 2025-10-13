# Maintainer: Wilf Chun <wchun@moffattnichol.com>
pkgname=python-coastalmetools
_realname=CoastalmeTools
pkgver=0.1.0
pkgrel=1
pkgdesc="Python tools to work with CoastalME"
arch=('any')
url="https://github.com/wilfchun/CoastalmeTools"
license=('GPL3')
depends=(
    'python-bokeh'
    'python-cfgrib'
    'python-cftime'
    'python-datetime'
    'python-dearpygui'
    'python-fiona'
    'python-geopandas'
    'python-humanize'
    'python-lxml'
    'python-matplotlib'
    'python-mpl-tools'
    'python-netcdf4'
    'python-numpy<2.0.0'
    'python-pandas'
    'python-pyyaml'
    'python-plotly'
    'python-pyogrio'
    'python-pyqt6'
    'python-pytimeparse2'
    'python-rasterio'
    'python-scikit-image'
    'python-scipy'
    'python-shapely'
    'python-streamlit'
    'python-watchdog'
    'python-windrose'
    'python-xarray'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-setuptools'
    'python-wheel'
)
optdepends=(
    'python-pytest: for running the test suite'
    'python-pytest-cov: for test coverage'
    'python-pytest-mock: for mocking in tests'
)
source=("${_realname}-${pkgver}.tar.gz::https://github.com/wilfchun/${_realname}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
    cd "${srcdir}/${_realname}-${pkgver}"
    python -m build --wheel --no-isolation
}

#check() {
#    cd "${srcdir}/${_realname}-${pkgver}"
#    pytest
#}

package() {
    cd "${srcdir}/${_realname}-${pkgver}"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 LICENSE -t "$pkgdir/usr/share/licenses/$pkgname/"
}
