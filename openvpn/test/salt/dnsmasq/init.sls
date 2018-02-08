dnsmasq:
  pkg.installed: []
  service.running:
  - enable: True
  - restart: True
  - require:
    - file: /etc/dnsmasq.conf
    - file: /etc/default/dnsmasq
  - watch:
    - file: /etc/dnsmasq.conf
    - file: /etc/default/dnsmasq
/etc/default/dnsmasq:
  file.managed:
  - user: root
  - group: root
  - mode: 600
  - contents: |
      ENABLED=1
      IGNORE_RESOLVCONF=yes
/etc/dnsmasq.conf:
  file.managed:
  - source: salt://dnsmasq/dnsmasq.conf
  - user: root
  - group: root
  - mode: 600
dnsmasq-ipv4:
  iptables.append:
  - table: filter
  - family: ipv4
  - chain: INPUT
  - comment: "Allow DNS over VPN"
  - dport: 53
  - proto: udp
  - save: True
dnsmasq-ipv6:
  iptables.append:
  - table: filter
  - family: ipv6
  - chain: INPUT
  - comment: "Allow DNS over VPN"
  - dport: 53
  - proto: udp
  - save: True
enable-ping-input:
  iptables.append:
  - table: filter
  - chain: INPUT
  - icmp-type: echo-reply
  - jump: ACCEPT
  - protocol: icmp
  - save: True
enable-ping-output:
  iptables.append:
  - table: filter
  - chain: OUTPUT
  - icmp-type: echo-request
  - jump: ACCEPT
  - protocol: icmp
  - save: True
