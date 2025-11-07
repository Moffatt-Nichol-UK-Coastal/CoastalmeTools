{ pkgs, ... }:

{
  packages = [
    pkgs.python3
    pkgs.python3Packages.debugpy
  ];

  languages.python = {
    enable = true;
    uv = {
      enable = true;
      sync.enable = true;
      sync.allExtras = true;
    };
    venv.enable = true;
  };

  env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.libz
    pkgs.libuv
  ];
  enterShell =
    # sh
    ''
      # . .devenv/state/venv/bin/activate
      # hello
      zsh
    '';
}
