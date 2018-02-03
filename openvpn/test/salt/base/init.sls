base-packages:
  pkg.installed:
    - pkgs:
      - build-essential
      - git
      - vim
      - htop
      - wget
      - unzip

security-packages:
  pkg.installed:
    - pkgs:
      - pwgen
      - openssl
      - gnupg2
      - python-gnupg
