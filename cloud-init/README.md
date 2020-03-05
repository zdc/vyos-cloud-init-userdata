
# Integration into the original Cloud-init package

The part-handler is compatible with the upstream Cloud-init package and can be integrated into them. With such integration possible to enter VyOS configuration directly into the User-Data field without any additional modifications.

## Integration steps

 - Place the `vyos_handler.py` file into `cloudinit/handlers/` directory of upstream package.
 - Change the `cloudinit/handlers/__init__.py` file, adding two more types into the `INCLUSION_TYPES_MAP`:
 ```
 '#vyos-config-plain': 'text/plain',
 '#vyos-config-notmulti': 'text/x-not-multipart',
 ```
 - Enable the handler by editing the `cloudinit/stages.py` file:
   - add import for the handler:
     ```
     from cloudinit.handlers.vyos_handler import VyOSConfigPartHandler
     ```
   - add the handler processing in the `_default_handlers()` function - insert after the `UpstartJobPartHandler(**opts),`:
     ```
     VyOSConfigPartHandler(**opts),
     ```

### Integration patch

The patch for integrating the part-handler into Cloud-init `20.1-5-g67c8e53c-0ubuntu1` can be found in the current directory.