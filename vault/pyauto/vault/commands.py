from . import config as vault_config


def vault_read(config, path_id):
    return config.vault.get_path(path_id).read()


def vault_download_file(config, path_id):
    return config.vault.get_path(path_id).download_file()


def vault_write(config, path_id):
    return config.vault.get_path(path_id)


def vault_upload_file(config, path_id):
    return config.vault.get_path(path_id).upload_file()
