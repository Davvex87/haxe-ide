import pkgutil

hiddenimports = []

try:
    import rich._unicode_data as _ud

    for _finder, _name, _ispkg in pkgutil.iter_modules(_ud.__path__):
        hiddenimports.append(f"rich._unicode_data.{_name}")
except Exception:
    pass
