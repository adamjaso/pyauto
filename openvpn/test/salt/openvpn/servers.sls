{%- from 'openvpn/vars.j2' import openvpn_dir -%}
{%- from 'openvpn/vars.j2' import openvpn_servers -%}

{%- for server in openvpn_servers -%}

{{ openvpn_dir }}/{{ server['conf_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['conf']|indent(8) }}
    - require:
      - file: {{ openvpn_dir }}

{{ openvpn_dir }}/{{ server['key_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['key']|indent(8) }}
    - require:
      - file: {{ openvpn_dir }}

{{ openvpn_dir }}/{{ server['cert_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['cert']|indent(8) }}

{{ openvpn_dir }}/{{ server['ca_cert_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['ca_cert']|indent(8) }}

{{ openvpn_dir }}/{{ server['ta_key_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['ta_key']|indent(8) }}

{{ openvpn_dir }}/{{ server['dh_params_filename'] }}:
  file.managed:
    - user: root
    - group: root
    - mode: 600
    - contents: |
        {{ server['dh_params']|indent(8) }}

openvpn-service-{{ server['id'] }}:
  service.running:
    - name: openvpn@{{ server['id'] }}
    - enable: True
    - reload: True
    - watch:
      - file: /etc/openvpn/{{ server['conf_filename'] }}
    - require:
      - file: /etc/openvpn/{{ server['conf_filename'] }}

{%- endfor -%}
