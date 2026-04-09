from discord.ext import tasks
from support.storage import astral_storage

@tasks.loop(seconds=astral_storage.get_global_int("astral", "save_interval"))
async def _autosave():
    print("[storage] saving all configs to disk")
    try:
        astral_storage.save_configs_to_disk()
        print(f"[storage] saved. waiting another {astral_storage.get_global_int('astral', 'save_interval')} seconds.")
    except Exception as e:
        print(e)


def _start():
    if not _autosave.is_running():
        _autosave.start()


def _update():
    new_seconds = astral_storage.get_global_int("astral", "save_interval")
    _autosave.change_interval(seconds=new_seconds)
    print(f"[storage] autosave interval updated to {new_seconds}s")
