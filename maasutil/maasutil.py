#!/usr/bin/env python2.7
# concat json or yaml files into large k8s List
# p.py file1 file2 file3
# produces all files on output wrapped by an enclosing list

import yaml, json, sys, os, argparse, logging, re
from os.path import expanduser
import argparse_config

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
    def_admin = 'maas'
    def_key = 'null'
    def_filename = '-'

    p = argparse.ArgumentParser(description="MaaS utility cli",
            formatter_class=SmartFormatter)

    # overall app related stuff
    p.add_argument('-p', '--pretty', action='store_true', dest='pretty', default=False)
    p.add_argument('-t', '--type', action='store', dest='output_type',
            default='text',
            choices=['json','yaml','text'],
            help='Output type, json, yaml or text' )

    # pick up the maas related arguments
    p.add_argument('-a', '--admin', action='store', dest='admin', default=def_admin,
            help='This is the maas admin user name, default :' + def_admin)
    p.add_argument('-u', '--url', action='store', dest='url', default=def_url,
            help='This is the maas url to connect to, default : ' + def_url)
    p.add_argument('-k', '--key', action='store', dest='key',
            help='This is the maas admin api key, default :' + def_key)

    p.add_argument('-f', '--file', action='store', dest='filename', default=def_filename,
            help='This is the jinja2 template file (- for stdin), default : ' + def_filename)

    # non application related stuff
    p.add_argument('-l', '--loglevel', action='store', dest='loglevel',
            default=loglevel,
            choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
            help='Log level (DEBUG,INFO,WARNING,ERROR,CRITICAL) default is: '+loglevel)
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

    logging.info('Program starting :%s', prog)
    logging.debug('Arg: pretty     :%s', args.pretty)
    logging.debug('Arg: type       :%s', args.output_type)
    logging.debug('Arg: loglevel   :%s', loglevel)
    logging.debug('Arg: admin      :%s', args.admin)
    logging.debug('Arg: url        :%s', args.url)
    logging.debug('Arg: filename   :%s', args.filename)
    logging.debug('Arg: save       :%s', args.save)

    # save to the defaults file if a -s specified on command line
    if args.save:
        f = open(cfn, 'w')
        apc = re.sub('\nsave\n','\n', argparse_config.generate_config(p, args, section='default'))
        f.write(apc)
        f.close()

    # rd contains the dictionary
    kp = args.key.split(':')
    response = perform_API_request(args.url, '/nodes/?op=list', 'GET', kp[1], kp[2], kp[0])
    rd = json.loads(response[1])

    # td comtains the template
    with open(args.filename, 'r') as template_file:
        template_text = template_file.read()
        logging.debug("Template file (%s): \n%s\n", args.filename, template_text)
    td = Template(template_text)
    tr = td.render(src=rd)

    print tr

    sys.exit(0)

if __name__ == '__main__':
   run()
