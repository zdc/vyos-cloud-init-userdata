#part-handler
# vi: syntax=python ts=4
# this is an example of a version 2 part handler.
# the differences between the initial part-handler version
# and v2 is:
#  * handle_part receives a 5th argument, 'frequency'
#    frequency will be either 'always' or 'per-instance'
#  * handler_version must be set
#
# A handler declaring version 2 will be called on all instance boots, with a
# different 'frequency' argument.

handler_version = 2

# import all dependencies
import logging
from logging.handlers import SysLogHandler
from pathlib import Path
import re
from vyos.configtree import ConfigTree
import requests

# configure logging
logger = logging.getLogger(__name__)
logs_format = logging.Formatter('%(filename)s: %(message)s')
logs_handler_syslog = SysLogHandler('/dev/log')
logs_handler_syslog.setFormatter(logs_format)
logger.addHandler(logs_handler_syslog)
logger.setLevel(logging.DEBUG)

# helper: convert line to command
def string_to_command(stringcmd):
    regex_filter = re.compile('^set (?P<cmd_path>[^\']+)( \'(?P<cmd_value>.*)\')*$')
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
def get_tag_nodes():
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
def is_tag_node(node_path, tag_nodes):
    match = False
    for tag_node in tag_nodes:
        if len(tag_node) == len(node_path):
            for element_id in list(range(len(node_path))):
                if not ( node_path[element_id] == tag_node[element_id] or tag_node[element_id] == 'node.tag' ):
                    break
                elif ( node_path[element_id] == tag_node[element_id] or tag_node[element_id] == 'node.tag' ) and element_id == len(node_path)-1:
                    match = True
        if match == True:
            break
    if match == True:
        logger.debug("Node {} is a tag node".format(node_path))
        return True
    else:
        logger.debug("Node {} is not a tag node".format(node_path))
        return False

# helper: mark nodes as tag, if this is necessary
def mark_tag(config, node_path, tag_nodes):
    current_node_path = []
    for current_node in node_path:
        current_node_path.append(current_node)
        if is_tag_node(current_node_path, tag_nodes):
            logger.debug("Marking node as tag: \"{}\"".format(current_node_path))
            config.set_tag(current_node_path)

# get configuration commands
def get_config_commands(payload):
    regex_url = re.compile('https?://[\w\.\:]+/.*$')
    if regex_url.search(payload.strip()):
        # try to download commands from URL
        try:
            logger.info("Trying to fetch commands from URL: {}".format(payload))
            return requests.get(payload.strip()).text
        # return raw data if this was not URL
        except Exception as err:
            logger.error("Failed to downloads commands from URL:{}".format(err))
    else:
        logger.info("Payload is not URL, processing as commands list")
        return payload

def list_types():
    # return a list of mime-types that are handled by this module
    return(["text/plain", "text/go-cubs-go"])

def handle_part(data,ctype,filename,payload,frequency):
    # data: the cloudinit object
    # ctype: '__begin__', '__end__', or the specific mime-type of the part
    # filename: the filename for the part, or dynamically generated part if
    #           no filename is given attribute is present
    # payload: the content of the part (empty for begin or end)
    # frequency: the frequency that this cloud-init run is running for
    #            this is either 'per-instance' or 'always'.  'per-instance'
    #            will be invoked only on the first boot.  'always' will
    #            will be called on subsequent boots.

    # prepare for VyOS config
    cfg_file_name = '/opt/vyatta/etc/config/config.boot'
    bak_file_name = '/opt/vyatta/etc/config.boot.default'
    if not Path(cfg_file_name).exists():
        config_file_path = bak_file_name
    else:
        config_file_path = cfg_file_name

    try:
        with open(config_file_path, 'r') as f:
            config_file_data = f.read()
        config = ConfigTree(config_file_data)
        logger.debug("Using configuration file: {}".format(config_file_path))
    except Exception as err:
        logger.error("Failed to load configuration file: {}".format(err))

    if ctype == "__begin__":
        logger.info("VyOS configuration handler for Cloud-init is beginning, frequency={}".format(frequency))
        return
    if ctype == "__end__":
        logger.info("VyOS configuration handler for Cloud-initis is ending, frequency={}".format(frequency))
        return

    logger.info("==== received ctype=%s filename=%s ====" % (ctype,filename))
    try:
        # get configuration commands
        config_lines = get_config_commands(payload).splitlines()
        # get all tag nodes. We should do this here and keep the result to avoid multiple command invoking
        tag_nodes = get_tag_nodes()
        # roll through configration commands
        for line in config_lines:
            # convert command to format, appliable to configuration
            command = string_to_command(line)
            # if conversion is successful, apply the command
            if command != None:
                logger.debug("Configuring command: \"{}\"".format(line))
                config.set(command['cmd_path'], command['cmd_value'], replace=True)
                # mark configured nodes as tag, if this is necessary
                mark_tag(config, command['cmd_path'], tag_nodes)
    except Exception as err:
        logger.error("Failed to configure system: {}".format(err))

    try:
        with open(config_file_path, 'w') as f:
            f.write(config.to_string())
    except Exception as err:
        logger.error("Failed to save configuration file: {}".format(err))

    logger.info("==== end ctype=%s filename=%s" % (ctype, filename))
