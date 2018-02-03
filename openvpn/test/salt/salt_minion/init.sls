{%- if 'Ubuntu-16.04' ==  grains['osfinger'] %}
# salt-apt-repository-gpg:
#   cmd.run:
#     - name: "wget -O - https://repo.saltstack.com/apt/ubuntu/16.04/amd64/latest/SALTSTACK-GPG-KEY.pub | sudo apt-key add -"

salt-apt-repository:
  pkgrepo.managed:
    - humanname: Saltstack PPA
    - name: deb https://repo.saltstack.com/apt/ubuntu/16.04/amd64/2016.3 xenial main
    - gpgcheck: 1
    - key_url: https://repo.saltstack.com/apt/ubuntu/16.04/amd64/2016.3/SALTSTACK-GPG-KEY.pub

salt-apt-update:
  cmd.run:
    - name: apt update
    - require:
      - pkgrepo: salt-apt-repository
{%- endif %}

/etc/salt:
  file.directory:
    - mode: 700
    - user: root
    - group: root
    - mkdirs: True

/etc/salt/minion:
  file.managed:
    - source: salt://salt_minion/minion
    - mode: 600
    - user: root
    - group: root
    - template: jinja
    - require:
      - file: /etc/salt

python-gnupg:
  pkg.installed: []

salt-minion:
  pkg.latest:
    - require:
      - file: /etc/salt/minion
{%- if 'Ubuntu-16.04' == grains['osfinger'] %}
      - cmd: salt-apt-update
{%- endif %}
  service.running:
    - restart: True
    - watch:
      - file: /etc/salt/minion
      - pkg: salt-minion
{%- if 'Ubuntu-16.04' == grains['osfinger'] %}
      - pkgrepo: salt-apt-repository
{%- endif %}
