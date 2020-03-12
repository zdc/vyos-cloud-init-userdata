#part-handler
# Copyright (C) 2020 Sentrium S.L.

from cloudinit import handlers
from cloudinit import log as logging
from cloudinit.settings import (PER_ALWAYS)

# VyOS specific imports
import re
import requests
from pathlib import Path
from vyos.configtree import ConfigTree

# configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class VyOSConfigPartHandler(handlers.Handler):

    # actually, these prefixes do not use, but due to an internal Cloud-init structure we need to define them here
    prefixes = ["#vyos-config-plain", "#vyos-config-notmulti"]

    def __init__(self, paths, **_kwargs):
        handlers.Handler.__init__(self, PER_ALWAYS, version=3)

    # helper: convert line to command
    def string_to_command(self, stringcmd):
        regex_filter = re.compile(r'^set (?P<cmd_path>[^\']+)( \'(?P<cmd_value>.*)\')*$')
        if regex_filter.search(stringcmd):
            # command structure
            command = {
                'cmd_path': regex_filter.search(stringcmd).group('cmd_path').split(),
                'cmd_value': regex_filter.search(stringcmd).group('cmd_value')
            }
            return command
        else:
            return None

    # get list of all tag nodes
    def get_tag_nodes(self):
        try:
            logger.debug("Searching for tag nodes in configuration templates")
            tags_nodes = []
            templates_dir = '/opt/vyatta/share/vyatta-cfg/templates/'
            tags_path = Path(templates_dir).rglob('node.tag')
            for tag_path in tags_path:
                current_tag_path = tag_path.relative_to(templates_dir).parent.parts
                tags_nodes.append(current_tag_path)
            return tags_nodes
        except Exception as err:
            logger.error("Failed to find tag nodes: {}".format(err))

    # helper: check if the node is tag or not
    def is_tag_node(self, node_path, tag_nodes):
        match = False
        for tag_node in tag_nodes:
            if len(tag_node) == len(node_path):
                for element_id in list(range(len(node_path))):
                    if not (node_path[element_id] == tag_node[element_id] or tag_node[element_id] == 'node.tag'):
                        break
                    elif (node_path[element_id] == tag_node[element_id] or tag_node[element_id] == 'node.tag') and element_id == len(node_path) - 1:
                        match = True
            if match is True:
                break
        if match is True:
            logger.debug("Node {} is a tag node".format(node_path))
            return True
        else:
            logger.debug("Node {} is not a tag node".format(node_path))
            return False

    # helper: mark nodes as tag, if this is necessary
    def mark_tag(self, config, node_path, tag_nodes):
        current_node_path = []
        for current_node in node_path:
            current_node_path.append(current_node)
            if self.is_tag_node(current_node_path, tag_nodes):
                logger.debug("Marking node as tag: \"{}\"".format(current_node_path))
                config.set_tag(current_node_path)

    # get payload from URL
    def download_payload(self, payload):
        # try to download from URL
        try:
            logger.info("Trying to fetch payload from URL: {}".format(payload))
            return requests.get(payload).text
        # return raw data if this was not URL
        except Exception as err:
            logger.error("Failed to downloads payload from URL: {}".format(err))

    # write file
    def write_file(self, file_path, content):
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info("Configuration saved to the file: {}".format(file_path))
        except Exception as err:
            logger.error("Failed to save configuration file: {}".format(err))

    # check what kind of user-data payload is - config file, commands list or URL
    def check_payload_format(self, payload):
        # prepare regex for parsing
        regex_url = re.compile(r'https?://[\w\.\:]+/.*$')
        regex_cmdlist = re.compile(r'^set ([^\']+)( \'(.*)\')*')
        regex_cmdfile = re.compile(r'^[\w-]+ {.*')

        if regex_cmdfile.search(payload.strip()):
            # try to parse as configuration file
            try:
                payload_config = ConfigTree(payload)
                logger.info("Parsing User-Data payload as VyOS configuration file")
                if payload_config:
                    return 'vyos_config_file'
            except Exception as err:
                logger.error("User-Data payload is not valid VyOS configuration file: {}".format(err))
        elif regex_cmdlist.search(payload.strip()):
            logger.info("User-Data payload is VyOS commands list")
            return 'vyos_config_commands'
        elif regex_url.search(payload.strip()):
            logger.info("User-Data payload is URL")
            return 'vyos_config_url'
        else:
            logger.error("User-Data payload format cannot be detected")

    def handle_part(self, data, ctype, filename, payload, frequency, headers):
        if ctype == "__begin__":
            logger.info("VyOS configuration handler for Cloud-init is beginning, frequency={}".format(frequency))
            return
        if ctype == "__end__":
            logger.info("VyOS configuration handler for Cloud-initis is ending, frequency={}".format(frequency))
            return

        logger.info("==== received ctype=%s filename=%s ====" % (ctype, filename))

        try:
            # detect payload format
            payload_format = self.check_payload_format(payload)
            if payload_format == 'vyos_config_url':
                # download and replace payload by content from server
                payload = self.download_payload(payload.strip())
                if payload:
                    payload_format = self.check_payload_format(payload)

            # find path for VyOS config
            cfg_file_name = '/opt/vyatta/etc/config/config.boot'
            bak_file_name = '/opt/vyatta/etc/config.boot.default'
            if not Path(cfg_file_name).exists():
                config_file_path = bak_file_name
            else:
                config_file_path = cfg_file_name

            # try to replace configuration file with new one
            if payload_format == 'vyos_config_file':
                self.write_file(config_file_path, payload)

            # apply commands to the current configuration file
            elif payload_format == 'vyos_config_commands':
                # load local configuration file
                try:
                    with open(config_file_path, 'r') as f:
                        config_file_data = f.read()
                    config = ConfigTree(config_file_data)
                    logger.info("Using configuration file: {}".format(config_file_path))
                except Exception as err:
                    logger.error("Failed to load configuration file: {}".format(err))

                try:
                    # get configuration commands
                    config_lines = payload.splitlines()
                    # get all tag nodes. We should do this here and keep the result to avoid multiple command invoking
                    tag_nodes = self.get_tag_nodes()
                    # roll through configration commands
                    for line in config_lines:
                        # convert command to format, appliable to configuration
                        command = self.string_to_command(line)
                        # if conversion is successful, apply the command
                        if command is not None:
                            logger.debug("Configuring command: \"{}\"".format(line))
                            config.set(command['cmd_path'], command['cmd_value'], replace=True)
                            # mark configured nodes as tag, if this is necessary
                            self.mark_tag(config, command['cmd_path'], tag_nodes)
                except Exception as err:
                    logger.error("Failed to configure system: {}".format(err))

                self.write_file(config_file_path, config.to_string())

            # skip configuration change
            else:
                logger.info("No valid configuration provided. Skipping configuration change")
                return

        except Exception as err:
            logger.error("User-Data payload format detection error: {}".format(err))
            return

        logger.info("==== end ctype=%s filename=%s" % (ctype, filename))


# part for using in part-handler mode
handler_version = 2


def list_types():
    # return a list of mime-types that are handled by this module
    return(["text/plain", "text/x-not-multipart"])


def handle_part(data, ctype, filename, payload, frequency):
    # pass to VyOSConfigPartHandler class
    part_handler = VyOSConfigPartHandler(None)
    part_handler.handle_part(data, ctype, filename, payload, frequency, None)
