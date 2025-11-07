{
  description = "CoastalmeTools Python environment on NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05"; # or pin a commit
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python311; # matches your >=3.9 requirement

        pythonEnv = python.withPackages (ps: with ps; [
          bokeh
          cfgrib
          cftime
          fiona
          geopandas
          humanize
          lxml
          matplotlib
          netcdf4
          numpy
          pandas
          pyyaml
          plotly
          pyogrio
          pyqt6
          rasterio
          scikit-image
          scipy
          shapely
          streamlit
          watchdog
          windrose
          xarray

          pytest
          pytest-cov
          pytest-mock
        ]);

        # Handle PyPI-only packages here
        mpl-tools = pkgs.python3Packages.buildPythonPackage rec {
          pname = "mpl-tools";
          version = "0.4.0";
          src = pkgs.fetchPypi {
            inherit pname version;
            sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # fill in after nix-build
          };
          doCheck = false;
        };

        pytimeparse2 = pkgs.python3Packages.buildPythonPackage rec {
          pname = "pytimeparse2";
          version = "1.7.1";
          src = pkgs.fetchPypi {
            inherit pname version;
            sha256 = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="; # fill in after nix-build
          };
          doCheck = false;
        };

      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            mpl-tools
            pytimeparse2
            pkgs.gcc
            pkgs.cmake
          ];

          shellHook = ''
            echo "🧊 Entered CoastalmeTools environment (Python: $(python --version))"
          '';
        };
      });
}

