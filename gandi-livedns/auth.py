#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pprint
import requests
import os
import sys
from config import *

pp = pprint.PrettyPrinter(indent=4)

acme_challenge = "_acme-challenge"

certbot_domain = os.environ.get("CERTBOT_DOMAIN")
if not certbot_domain:
    print("CERTBOT_DOMAIN environment variable is missing, exiting")
    sys.exit(1)

try:
    gandi_domain
except NameError:
    gandi_domain = os.environ.get("GANDI_DOMAIN")
    
if not gandi_domain:
    gandi_domain = certbot_domain
else:
    acme_challenge += "." + certbot_domain.replace("."+gandi_domain,"")


certbot_validation = os.environ.get("CERTBOT_VALIDATION")
if not certbot_validation:
    print("CERTBOT_VALIDATION environment variable is missing, exiting")
    sys.exit(1)

if livedns_sharing_id is None:
    sharing_param = ''
else:
    sharing_param = '?sharing_id={}'.format(livedns_sharing_id)

try:
    livedns_apikey
except NameError:
    livedns_apikey = os.environ.get("LIVEDNS_APIKEY")

if not livedns_apikey:
    print("livends_apikey not defined and LIVEDNS_APIKEY environment variable is missing, exiting")
    sys.exit(1)
        

headers = {
    'X-Api-Key': livedns_apikey,
}

response = requests.get('{}domains{}'.format(livedns_api, sharing_param),
                        headers=headers)

if (response.ok):
    domains = response.json()
else:
    response.raise_for_status()
    sys.exit(1)

domain_index = next((index for (index, d) in enumerate(domains) if d["fqdn"] == gandi_domain), None)

if domain_index is None:
    # domain not found
    print('The requested domain {} was not found in this gandi account'
          .format(gandi_domain))
    sys.exit(1)

domain_records_href = domains[domain_index]["domain_records_href"]

response = requests.get('{}/{}/TXT{}'
                        .format(domain_records_href, acme_challenge, sharing_param),
                        headers=headers)

if response.status_code == 404:
    newrecord = {
      "rrset_ttl": 300,
      "rrset_values": [certbot_validation]
    }
    response = requests.post('{}/{}/TXT{}'
                             .format(domain_records_href, acme_challenge, sharing_param),
                             headers=headers, json=newrecord)
elif response.ok:
    newrecord = {
      "rrset_ttl": 300,
      "rrset_values": response.json()['rrset_values'] + [certbot_validation]
    }
    # pp.pprint(newrecord)
    response = requests.put('{}/{}/TXT{}'
                            .format(domain_records_href, acme_challenge, sharing_param),
                            headers=headers, json=newrecord)
else:
    print("Failed to look for existing _acme-challenge record")
    response.raise_for_status()
    sys.exit(1)


if response.ok:
    print("all good, entry created")
    # pp.pprint(response.content)
else:
    print("something went wrong")
    pp.pprint(response.content)
    response.raise_for_status()
    sys.exit(1)
