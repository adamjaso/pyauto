from . import config as _
from pyauto.filecache import commands as _


def import_csv(config, csv_id):
    csv = config.csvdb.get_csv(csv_id)
    with csv.get_import_table() as it:
        it.import_table()
    return csv.database.filename


def get_db_file(config, csv_id):
    return config.csvdb.get_csv(csv_id).database.filename
