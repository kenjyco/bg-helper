__all__ = [
    'ssh_to_server', 'ssh_pem_files', 'ssh_private_key_files',
    'ssh_configured_hosts', 'ssh_determine_aws_user_for_server'
]

import re
import os.path
import bg_helper as bh
import fs_helper as fh
from os import walk


SSH_FAILED_OUTPUT_RX = re.compile(r'.*(Timeout|Permission denied|Connection closed by|Connection timed out).*', re.DOTALL)

AWS_SSH_USERS = [
    'ec2-user',
    'ubuntu',
    'admin',
    'centos',
    'fedora',
    'root',
]


def ssh_to_server(ip_or_hostname, user=None, pem_file=None, private_key_file=None, command='', timeout=None, verbose=False):
    """Actually SSH to a server and run a command or start interactive seesion

    - ip_or_hostname: IP address or hostname of server
    - user: remote SSH user
    - pem_file: absolute path to pem file
    - private_key_file: absolute path to private key file
    - command: an optional command to run on the remote server
        - if a command is specified, it will be run on the remote server and
          the output will be returned
        - if no command is specified, the SSH session will be interactive
    - timeout: the number of seconds to wait for a specified command to run
      on the remote server
    - verbose: if True, print the generated SSH command
        - if a command is specified, print it's result as well

    If ip_or_hostname is NOT a configured Host in the ~/.ssh/config file, you
    must specify a user and either a pem_file or private_key_file. You cannot
    specify BOTH a pem_file and a private_key_file
    """
    if ip_or_hostname in ssh_configured_hosts():
        ssh_command = 'ssh -o "StrictHostKeyChecking no" -o ConnectTimeout=2 {}'
        cmd = ssh_command.format(ip_or_hostname)
    else:
        ssh_command = 'ssh -i {} -o "StrictHostKeyChecking no" -o ConnectTimeout=2 {}@{}'
        assert user, 'Must specify user since {} is not in ~/.ssh/config'.format(ip_or_hostname)
        assert pem_file or private_key_file, 'Must specify pem_file or private_key_file'
        assert not (pem_file and private_key_file), (
            'Cannot specify pem_file and private_key_file'
        )
        if pem_file:
            cmd = ssh_command.format(pem_file, user, ip_or_hostname)
        elif private_key_file:
            cmd = ssh_command.format(private_key_file, user, ip_or_hostname)
    if command:
        cmd = cmd + ' -t {}'.format(repr(command))
    if verbose:
        print(cmd)

    result = None
    if command:
        result = bh.run_output(cmd, timeout=timeout)
        if verbose:
            print(result)
    else:
        result = bh.run(cmd)
    return result


def ssh_pem_files():
    """Find all .pem files in ~/.ssh and return a dict with absolute paths"""
    found = []
    dirname = os.path.abspath(os.path.expanduser('~/.ssh'))
    for dirpath, dirnames, filenames in walk(dirname, topdown=True):
        found.extend([os.path.join(dirpath, f) for f in filenames if f.endswith('.pem')])
    return {
        fh.strip_extension(os.path.basename(path)): path
        for path in sorted(found)
    }


def ssh_private_key_files():
    """Find all private key files in ~/.ssh and return a dict with absolute paths"""
    pub_keys_found = []
    found = []
    dirname = os.path.abspath(os.path.expanduser('~/.ssh'))
    for dirpath, dirnames, filenames in walk(dirname, topdown=True):
        pub_keys_found.extend([os.path.join(dirpath, f) for f in filenames if f.endswith('.pub')])

    for pub_key in pub_keys_found:
        private_key = fh.strip_extension(pub_key)
        if os.path.isfile(private_key):
            found.append(private_key)
    return {
        fh.strip_extension(os.path.basename(path)): path
        for path in sorted(found)
    }


def ssh_configured_hosts():
    """Return a set of Hosts from the ~/.ssh/config file"""
    results = set()
    with open(fh.abspath('~/.ssh/config'), 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            if line.startswith('Host '):
                for host in line.strip().replace('Host ', '').split(' '):
                    results.add(host)
    return results


def ssh_determine_aws_user_for_server(ip_or_hostname, pem_file, verbose=False):
    """Determine which AWS default user is setup for server

    - ip_or_hostname: IP address or hostname of server
    - pem_file: absolute path to pem file
    - verbose: if True, show info for each attempt
    """
    if verbose:
        print('\nDetermining SSH user for {}'.format(ip_or_hostname))
    for user in AWS_SSH_USERS:
        if verbose:
            print('  - trying {}'.format(user))
        output = ssh_to_server(ip_or_hostname, user=user, pem_file=pem_file, command='ls', timeout=2, verbose=verbose)
        if not SSH_FAILED_OUTPUT_RX.match(output):
            return user
