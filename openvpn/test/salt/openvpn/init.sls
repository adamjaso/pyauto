{%- from 'openvpn/vars.j2' import openvpn_dir -%}

include:
  - .networking
  - .servers

openvpn-defaults:
  file.managed:
  - name: /etc/default/openvpn
  - user: root
  - group: root
  - mode: 600
  - contents: |
      AUTOSTART="all"
      OPTARGS=""
      OMIT_SENDSIGS=0

openvpn:
  file.directory:
  - name: {{ openvpn_dir }}
  - user: root
  - group: root
  - mode: 700
  pkg.installed:
  - require:
    - file: {{ openvpn_dir }}

# cmd.run:
#   - name: "ufw allow OpenSSH ; ufw allow 443/tcp ; ufw disable ; echo y | ufw enable"
