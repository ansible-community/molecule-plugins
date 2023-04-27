#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import base64
import copy
import datetime
import json
import time

# Google API Client Library for Python:
# https://developers.google.com/api-client-library/python/start/get_started
import google.auth

# PyCrypto library: https://pypi.python.org/pypi/pycrypto
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes
from googleapiclient.discovery import build


def GetCompute():
    """Get a compute object for communicating with the Compute Engine API."""
    credentials, project = google.auth.default()
    compute = build("compute", "v1", credentials=credentials)
    return compute


def GetInstance(compute, instance, zone, project):
    """Get the data for a Google Compute Engine instance."""
    cmd = compute.instances().get(instance=instance, project=project, zone=zone)
    return cmd.execute()


def GetKey():
    """Get an RSA key for encryption."""
    # This uses the PyCrypto library
    key = RSA.generate(2048)
    return key


def GetModulusExponentInBase64(key):
    """Return the public modulus and exponent for the key in bas64 encoding."""
    mod = long_to_bytes(key.n)
    exp = long_to_bytes(key.e)

    modulus = base64.b64encode(mod)
    exponent = base64.b64encode(exp)

    return modulus, exponent


def GetExpirationTimeString():
    """Return an RFC3339 UTC timestamp for 5 minutes from now."""
    utc_now = datetime.datetime.utcnow()
    # These metadata entries are one-time-use, so the expiration time does
    # not need to be very far in the future. In fact, one minute would
    # generally be sufficient. Five minutes allows for minor variations
    # between the time on the client and the time on the server.
    expire_time = utc_now + datetime.timedelta(minutes=5)
    return expire_time.strftime("%Y-%m-%dT%H:%M:%SZ")


def GetJsonString(user, modulus, exponent, email):
    """Return the JSON string object that represents the windows-keys entry."""
    converted_modulus = modulus.decode("utf-8")
    converted_exponent = exponent.decode("utf-8")

    expire = GetExpirationTimeString()
    data = {
        "userName": user,
        "modulus": converted_modulus,
        "exponent": converted_exponent,
        "email": email,
        "expireOn": expire,
    }

    return json.dumps(data)


def UpdateWindowsKeys(old_metadata, metadata_entry):
    """Return updated metadata contents with the new windows-keys entry."""
    # Simply overwrites the "windows-keys" metadata entry. Production code may
    # want to append new lines to the metadata value and remove any expired
    # entries.
    new_metadata = copy.deepcopy(old_metadata)
    new_metadata["items"] = [{"key": "windows-keys", "value": metadata_entry}]
    return new_metadata


def UpdateInstanceMetadata(compute, instance, zone, project, new_metadata):
    """Update the instance metadata."""
    cmd = compute.instances().setMetadata(
        instance=instance,
        project=project,
        zone=zone,
        body=new_metadata,
    )
    return cmd.execute()


def GetSerialPortFourOutput(compute, instance, zone, project):
    """Get the output from serial port 4 from the instance."""
    # Encrypted passwords are printed to COM4 on the windows server:
    port = 4
    cmd = compute.instances().getSerialPortOutput(
        instance=instance,
        project=project,
        zone=zone,
        port=port,
    )
    output = cmd.execute()
    return output["contents"]


def GetEncryptedPasswordFromSerialPort(serial_port_output, modulus):
    """Find and return the correct encrypted password, based on the modulus."""
    # In production code, this may need to be run multiple times if the output
    # does not yet contain the correct entry.

    converted_modulus = modulus.decode("utf-8")

    output = serial_port_output.split("\n")
    for line in reversed(output):
        try:
            entry = json.loads(line)
            if converted_modulus == entry["modulus"]:
                return entry["encryptedPassword"]
        except ValueError:
            pass
    return None


def DecryptPassword(encrypted_password, key):
    """Decrypt a base64 encoded encrypted password using the provided key."""
    decoded_password = base64.b64decode(encrypted_password)
    cipher = PKCS1_OAEP.new(key)
    password = cipher.decrypt(decoded_password)
    return password


def Arguments():
    # Create the parser
    args = argparse.ArgumentParser(description="List the content of a folder")

    # Add the arguments
    args.add_argument(
        "--instance",
        metavar="instance",
        type=str,
        help="compute instance name",
    )

    args.add_argument("--zone", metavar="zone", type=str, help="compute zone")

    args.add_argument("--project", metavar="project", type=str, help="gcp project")

    args.add_argument("--username", metavar="username", type=str, help="username")

    args.add_argument("--email", metavar="email", type=str, help="email")

    return args.parse_args()


def main():
    config_args = Arguments()

    # Setup
    compute = GetCompute()
    key = GetKey()
    modulus, exponent = GetModulusExponentInBase64(key)

    # Get existing metadata
    instance_ref = GetInstance(
        compute,
        config_args.instance,
        config_args.zone,
        config_args.project,
    )
    old_metadata = instance_ref["metadata"]
    # Create and set new metadata
    metadata_entry = GetJsonString(
        config_args.username,
        modulus,
        exponent,
        config_args.email,
    )
    new_metadata = UpdateWindowsKeys(old_metadata, metadata_entry)

    # Get Serial output BEFORE the modification
    serial_port_output = GetSerialPortFourOutput(
        compute,
        config_args.instance,
        config_args.zone,
        config_args.project,
    )

    UpdateInstanceMetadata(
        compute,
        config_args.instance,
        config_args.zone,
        config_args.project,
        new_metadata,
    )

    # Get and decrypt password from serial port output
    # Monitor changes from output to get the encrypted password as soon as it's generated, will wait for 30 seconds
    i = 0
    new_serial_port_output = serial_port_output
    while i <= 20 and serial_port_output == new_serial_port_output:
        new_serial_port_output = GetSerialPortFourOutput(
            compute,
            config_args.instance,
            config_args.zone,
            config_args.project,
        )
        i += 1
        time.sleep(3)

    enc_password = GetEncryptedPasswordFromSerialPort(new_serial_port_output, modulus)

    password = DecryptPassword(enc_password, key)
    converted_password = password.decode("utf-8")

    # Display only the password
    print(format(converted_password))  # noqa: T201


if __name__ == "__main__":
    main()
