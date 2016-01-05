#!/usr/bin/env python

####
# Imports
import json

####
# Code

# Main function.
def main():
    cid     = raw_input('Client ID: ')
    csecret = raw_input('Client Secret: ')
    ruri    = raw_input('Redirect URI: ')

    f = open('config.json', 'w')
    json.dump({ 'client_id': cid, 'client_secret': csecret, 'redirect_uri': ruri }, f)
    f.close()

# Primary entry point.
if __name__ == '__main__':
    main()
