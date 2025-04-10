{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.chromium
    pkgs.playwright-driver
    pkgs.gitFull
    pkgs.postgresql
    pkgs.openssl
  ];
}
