#!/usr/bin/env python2.7
# concat json or yaml files into large k8s List
# p.py file1 file2 file3
# produces all files on output wrapped by an enclosing list

import yaml, json, sys, os, argparse, logging, re
from os.path import expanduser
import argparse_config
from __init__ import __version__

import oauth.oauth as oauth
import httplib2
import uuid

from jinja2 import Template

#
# this routine straight from the maas documentation.
# the key, secret and consumer_key took me
# a while to figure out.  it turns out that
# MAAS keys (under account settings in gui)
# is a tuple secret:consumer_key:key, base64 with two colons marking field boundaries.
#

def perform_API_request(site, uri, method, key, secret, consumer_key):
    logging.debug('perform_API_request :%s,%s,%s', site, uri, method)
    #logging.debug('SECRET :%s,%s,%s', key, secret, consumer_key)
    resource_tok_string = "oauth_token_secret=%s&oauth_token=%s" % (
        secret, key)
    resource_token = oauth.OAuthToken.from_string(resource_tok_string)
    consumer_token = oauth.OAuthConsumer(consumer_key, "")

    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer_token, token=resource_token, http_url=site,
        parameters={'oauth_nonce': uuid.uuid4().get_hex()})
    oauth_request.sign_request(
        oauth.OAuthSignatureMethod_PLAINTEXT(), consumer_token,
        resource_token)
    headers = oauth_request.to_header()
    url = "%s%s" % (site, uri)
    http = httplib2.Http()
    return http.request(url, method, body=None, headers=headers)


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()  
        return argparse.HelpFormatter._split_lines(self, text, width)

def run():
    loglevel = "INFO"

    home = expanduser("~")
    prog = os.path.basename(__file__)
    cfn = home + '/' + '.' + os.path.splitext(prog)[0] + '.conf'
    def_url = 'http://localhost/MAAS/api/1.0'
    def_key = 'null'

    p = argparse.ArgumentParser(description="MaaS utility cli",
            formatter_class=SmartFormatter)

    # pick up the maas related arguments
    p.add_argument('-u', '--url', action='store', dest='url', default=def_url,
            help='This is the maas url to connect to, default : ' + def_url)
    p.add_argument('-k', '--key', action='store', dest='key',
            help='This is the maas admin api key, default :' + def_key)

    p.add_argument('-f', '--file', action='store', dest='filename',
            help='This is the jinja2 template file : ')
    p.add_argument('-t', '--template', action='store', dest='template',
            help='This is the template text on the command line, or use the word RAW for raw json output')

    p.add_argument('-c', '--command', action='store', dest='command',
            help='This is the maas uri, e.g. /nodes/?op=list : ')

    # non application related stuff
    p.add_argument('-v', '--version', action='store_true', dest='version',
            default=False,
            help='this switch will just return the version and exit, current version is : ' + __version__)

    p.add_argument('-l', '--loglevel', action='store', dest='loglevel',
            default=loglevel,
            choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
            help='Log level (DEBUG,INFO,WARNING,ERROR,CRITICAL) default is: '+loglevel)

    # this argument saves the current argument list
    # in a .maasutil.conf file in the current user's home
    # directory.  This does put a api key in that file, so,
    # in secure environment this shouldn't be used
    p.add_argument('-s', '--save', action='store_true', dest='save',
            default=False, help='save select command line arguments (default is never) in "'+cfn+'" file')

    # read in defaults from ~/.PROGBASENAMENOSUFFIX
    # if the file exists
    if os.path.isfile(cfn):
        argparse_config.read_config_file(p,cfn)

    # parse arguments (after reading defaults from ~/.dot file
    args = p.parse_args()
    if args.loglevel:
        loglevel = args.loglevel

    # set our logging level (from -l INFO (or whatever))
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s', loglevel)
    logging.basicConfig(level=numeric_level)

    if args.version:
        print __version__
        sys.exit(0)

    # save to the defaults file if a -s specified on command line
    if args.save:
        logging.info('Saving arguments to :%s', cfn)
        f = open(cfn, 'w')
        apc = re.sub('\nsave\n','\n',
            argparse_config.generate_config(p, args, section='default'))
        f.write(apc)
        f.close()

    #
    # this logic requires -f or -t argument, if both are specified
    # a warning is issued, if neither we exit.  Otherwise, we load
    # template_text with the template from either a file or a command line.
    #
    if not args.filename and not args.template:
        raise RuntimeError('Must supply either -f templatefile or -t templatetext')
    if args.filename and args.template:
        logging.warning('BOTH -f and -t specified, -t will override -f!!')
    template_text = ''
    if args.template:
        template_text = args.template
        logging.debug("Command line template text: \n%s\n", template_text)
    else:
        try:
            template_file = open(args.filename, 'r')
            template_text = template_file.read()
            logging.debug("Template file (%s): \n%s\n", args.filename, template_text)
        except Exception as e:
            logging.fatal('Error with template file %s:[%s]', args.filename, str(e))

    logging.info('Program starting :%s', prog)
    logging.debug('Arg: loglevel   :%s', loglevel)
    logging.debug('Arg: url        :%s', args.url)
    logging.debug('Arg: filename   :%s', args.filename)
    logging.debug('Arg: template   :%s', args.template)
    logging.debug('Arg: command    :%s', args.command)
    logging.debug('Arg: save       :%s', args.save)

    # rd contains the dictionary
    kp = args.key.split(':')
    response = perform_API_request(args.url, args.command, 'GET', kp[1], kp[2], kp[0])
    logging.debug("response header :%s", response[0])
    logging.debug("response content :%s", response[1])
    try:
        rd = json.loads(response[1])
    except:
        rd = []

    if template_text == 'RAW':
        print json.dumps(rd)
    else:
        td = Template(template_text)
        tr = td.render(src=rd)

        print tr,

    sys.exit(0)

if __name__ == '__main__':
   run()
