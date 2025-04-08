{pkgs}: {
  deps = [
    pkgs.chromium
    pkgs.playwright-driver
    pkgs.gitFull
    pkgs.postgresql
    pkgs.openssl
  ];
}
