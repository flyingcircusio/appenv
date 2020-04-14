#!/usr/bin/env python3
# appenv - a single file 'application in venv bootstrapping and updating
#          mechanism for python-based (CLI) applications

# Assumptions:
#
#	- the appenv file is placed in a repo with the name of the application
#   - the name of the application/file is an entrypoint XXX
#   - python3.X+ with ensurepip
#   - a requirements.txt file next to the appenv file

# TODO
#
# - provide a `clone` meta command to create a new project based on this one
#   maybe use an entry point to allow further initialisation of the clone.


import argparse
import ensurepip
import hashlib
import os
import os.path
import shlex
import subprocess
import sys
import venv


def cmd(c, quiet=False):
    # TODO revisit the cmd() architecture w/ python 3
    try:
        return subprocess.check_output([c], stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        if not quiet:
            print("{} returned with exit code {}".format(c, e.returncode))
            print(e.output)
        raise


def main():
    base = os.path.dirname(__file__)
    os.chdir(base)

    appname = os.path.splitext(os.path.basename(__file__))[0]
    appenvdir = f'.{appname}'

    if not os.path.exists('requirements.txt'):
        print(f'Missing `requirements.txt` - this is not a proper appenv '
               ' directory.')
        sys.exit(1)

    # clear PYTHONPATH variable to get a defined environment
    # XXX this is a bit of history. not sure whether its still needed. keeping it
    # for good measure
    if 'PYTHONPATH' in os.environ:
        del os.environ['PYTHONPATH']

    if not os.path.exists(appenvdir):
        os.makedirs(appenvdir)

    # copy used requirements.txt into the target directory so we can use that
    # to check later
    # - when to clean up old versions? keep like one or two old revisions?
    # - enumerate the revisions and just copy the requirements.txt, check
    #   for ones that are clean or rebuild if necessary
    requirements_source = open('requirements.txt', 'r', encoding='ascii').read()

    # Prepare args for us and args for the actual target program.
    meta_argv = []
    argv = []

    # Preprocess the requirements.txt
    requirements = []
    for line in requirements_source.splitlines():
        if line.startswith('# appenv:'):
            meta_argv.extend(shlex.split(line.replace('# appenv:', '')))
        else:
            requirements.append(line)
    requirements = '\n'.join(requirements)

    # Preprocess sys.arv
    for arg in sys.argv:
        if arg.startswith('--appenv-'):
            meta_argv.append(arg.replace('appenv-', ''))
        else:
            argv.append(arg)

    # Parse the appenv arguments
    meta_parser = argparse.ArgumentParser()
    meta_parser.add_argument(
        '-r', '--reset', action='store_true',
        help='Reset the whole appenv environment.')
    meta_parser.add_argument(
        '-u', '--unclean', action='store_true',
        help='Use an unclean working environment.')
    meta_args = meta_parser.parse_args(meta_argv)

    if meta_args.reset:
        print(f'Resetting ALL application environments in {appenvdir} ...')
        cmd(f'rm -rf {appenvdir}')


    if meta_args.unclean:
        print("Using an unclean working dir -- recommended for development only!")
        env_dir = os.path.join(appenvdir, 'unclean')
        if not os.path.exists(env_dir):
            print('Creating venv ...')
            venv.create(env_dir)
            print('Installing pip ...')
            cmd(f'{env_dir}/bin/python -m ensurepip')
        print("Ensuring unclean install ...")
        cmd(f'{env_dir}/bin/pip3 install -r requirements.txt --upgrade')
    else:
        env_hash = hashlib.new('sha256', requirements).hexdigest()
        env_dir = os.path.join(appenvdir, env_hash)
        if os.path.exists(env_dir):
            print('Found existing envdir')
            # check whether the existing environment is OK, it might be nice
            # to rebuild in a separate place if necessary to avoid interruptions
            # to running services, but that isn't what we're using it for at the
            # moment
            try:
                if not os.path.exists(f'{env_dir}/appenv.ready'):
                    raise Exception()
            except Exception:
                print('Existing envdir not consistent, deleting')
                cmd(f'rm -rf {env_dir}')

        if not os.path.exists(env_dir):
            print('Creating venv ...')
            venv.create(env_dir)
            print('Installing pip ...')
            cmd(f'{env_dir}/bin/python -m ensurepip')

            with open(f'{env_dir}/requirements.txt', 'wb') as f:
                f.write(requirements)

            print('Installing application ...')
            cmd(f'{env_dir}/bin/pip3 install --no-deps -r {env_dir}/requirements.txt')

            cmd(f'{env_dir}/bin/pip3 check')

            with open(os.path.join(env_dir, 'appenv.ready'), 'w') as f:
                f.write('Ready or not, here I come, you can\'t hide\n')

    os.execv(f'{env_dir}/bin/{appname}', argv)


if __name__ == '__main__':
    main()
