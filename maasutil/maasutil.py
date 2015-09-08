#!/usr/bin/env python2.7
# concat json or yaml files into large k8s List
# p.py file1 file2 file3
# produces all files on output wrapped by an enclosing list

import yaml, json, sys, os, argparse, logging
from os.path import expanduser
import argparse_config

import oauth.oauth as oauth
import httplib2
import uuid

from jinja2 import Template

def perform_API_request(site, uri, method, key, secret, consumer_key):
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

    p = argparse.ArgumentParser(description="MaaS utility cli",
            formatter_class=SmartFormatter)

    # overall app related stuff
    p.add_argument('-p', '--pretty', action='store_true', dest='pretty', default=False)
    p.add_argument('-t', '--type', action='store', dest='output_type',
            default='text',
            choices=['json','yaml', 'text'],
            help='Output type, json or yaml' )

    # pick up the maas related arguments
    p.add_argument('-a', '--admin', action='store', dest='admin', default=def_admin,
        help='This is the maas admin user name')
    p.add_argument('-u', '--url', action='store', dest='url', default=def_url,
        help='This is the maas url to connect to')
    p.add_argument('-k', '--key', action='store', dest='key',
        help='This is the maas admin api key, it must be declared')

    # these are the command line leftovers, the files to process
    p.add_argument('files', nargs='*')

    # non application related stuff
    p.add_argument('-l', '--loglevel', action='store', dest='loglevel',
            default=loglevel,
            choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
            help='Log level (DEBUG,INFO,WARNING,ERROR,CRITICAL) default is: '+loglevel)
    p.add_argument('-s', '--save', action='store_true', dest='save',
            default=False, help='save select command line arguments (default is always) in "'+cfn+'" file')

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
    logging.debug('Arg: save       :%s', args.save)

    # save to the defaults file if a -s specified on command line
    if args.save:
        f = open(cfn, 'w')
        # remove the 'save' from the file
        f.write(re.sub('\naddminion\n', re.sub('\nsave\n','\n',argparse_config.generate_config(p, args, section='default'))))
        f.close()

    kp = args.key.split(':')
    response = perform_API_request(args.url, '/nodes/?op=list', 'GET', kp[1], kp[2], kp[0])
    rd = json.loads(response[1])
    print "response "+json.dumps(rd)

    sys.exit(0)

if __name__ == '__main__':
   run()
