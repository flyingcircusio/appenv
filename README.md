# appenv

Self-contained bootstrapping/updating of Python applications deployed through shared repositories.

> The following examples use the `ducker` package to illustrate how to use
>`appenv`. `ducker` and `appenv` are not related at all.

## Bootstrapping an application / project

Use `curl -sL https://github.com/flyingcircusio/appenv/raw/master/bootstrap | sh` for bootstrapping a new project.

```
$ curl -sL https://github.com/flyingcircusio/appenv/raw/master/bootstrap | sh
Let's create a new appenv project.

What should the command be named? ducker <return>
What is the main dependency as found on PyPI? [ducker] <return>
Where should we create this? [/private/tmp/ducker] <return>

Creating appenv setup in /private/tmp/ducker ...

Done. You can now `cd ducker` and call `./ducker` to bootstrap and run it.

$ cd ducker
$ ./ducker
Running unclean installation from requirements.txt
Ensuring unclean install ...
Please initiate a query.
Ducker (? for help) q
```

## Freezing requirements for repeatable builds

Using frozen requirements makes the builds repeatable for you and your team
and also speeds up subsequent invocations:

```
$ ./appenv update-lockfile
Updating lockfile
Installing packages ...

$ time ./ducker wikipedia
Installing ducker ...
./ducker wikipedia  2.91s user 0.99s system 88% cpu 4.407 total

$ time ./ducker wikpedia
./ducker wikipedia  0.22s user 0.11s system 90% cpu 0.371 total

```

## Using a specific version of Python for your application

`appenv` tries to use the best Python version available. It bootstraps with
the Python 3 interpreter available in your PATH as `python3` and then can
either detect the newest Python or select the best python of your choice.

Two disable the automatic detection of the newest version and provide a
list of acceptable Python versions (tried in the order you list them)
add the following line to your requirements.txt file:

```
# appenv-python-preference: 3.6,3.9,3.8
```

The best version that is found on the system will be used to re-spawn appenv
and then also used to manage the virtual environments for your application.

AppEnv itself is tested against Python 3.6+.

## Learning more about appenv

```
$ ./appenv --help
usage: appenv [-h] {update-lockfile,init,reset,python,run} ...

positional arguments:
  {update-lockfile,init,reset,python,run}
    update-lockfile     Update the lock file.
    init                Create a new appenv project.
    reset               Reset the environment.
    python              Spawn the embedded Python interpreter REPL
    run                 Run a script from the bin/ directory of the virtual env.

options:
  -h, --help            show this help message and exit
```

## Testing

If you want to contribute, please install `tox` and run it.

```
$ tox

```
