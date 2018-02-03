{%- from 'openvpn/vars.j2' import primary_iface -%}
{%- from 'openvpn/vars.j2' import openvpn_cidr -%}
{%- from 'openvpn/vars.j2' import openvpn_protocol -%}
{%- from 'openvpn/vars.j2' import openvpn_port -%}

openvpn-sysctl-ip-forward:
  sysctl.present:
    - name: net.ipv4.ip_forward
    - value: 1

openvpn-open-port:
  iptables.append:
    - table: filter
    - chain: INPUT
    - i: {{ primary_iface }}
    - protocol: {{ openvpn_protocol }}
    - dport: {{ openvpn_port }}

openvpn-iptables-nat:
  iptables.append:
    - table: nat
    - chain: POSTROUTING
    - jump: MASQUERADE
    - o: {{ primary_iface }}
    - s: {{ openvpn_cidr }}
    - save: True

