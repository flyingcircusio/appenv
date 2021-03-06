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
$ ./ducker appenv-update-lockfile
Updating lockfile
Installing packages ...

$ time ./ducker wikipedia
Installing ducker ...
./ducker wikipedia  2.91s user 0.99s system 88% cpu 4.407 total

$ time ./ducker wikpedia
./ducker wikipedia  0.22s user 0.11s system 90% cpu 0.371 total

```

## Using a specific version of Python

By default `appenv` uses the default Python 3 interpreter available in your
environment. If you want to use a specific version of Python you can 
customize the `shebang` line of your application file:

```
#!/usr/bin/env python3.5
...
```

AppEnv itself is tested against Python 3.4+.

## Learning more about appenv

```
$ ./ducker --appenv-help
usage: ducker [-h] [-u] [--appname APPNAME] [--appenvdir APPENVDIR]
              {update-lockfile,init,reset,python} ...

positional arguments:
  {update-lockfile,init,reset,python}
    update-lockfile     Update the lock file.
    init                Create a new appenv project.
    reset               Reset the environment.
    python              Spawn the embedded Python interpreter REPL

optional arguments:
  -h, --help            show this help message and exit
  -u, --unclean         Use an unclean working environment.
  --appname APPNAME
  --appenvdir APPENVDIR
```


## Advanced usage

* ``bootstrap by cloning``
