# Sublime Test Plier

[![Build Status](https://travis-ci.org/asfaltboy/Sublime-Test-Plier.svg?branch=develop)](https://travis-ci.org/asfaltboy/Sublime-Test-Plier)

This [Sublime Text](http://www.sublimetext.com/) plugin allows python users to run tests quickly from within a project environment.

### Preface

Unlike [other plugins for running python tests](https://packagecontrol.io/search/test%20python), which mostly use a regex pattern to find a given test to run, Sublime Test Plier parses the source [AST](test_parser.py), and locates the class/method/function whose definition contains the caret position. The found results are passed as named arguments to the test command, which can be anything (`py.test`, `nosetests`, `python manage.py` or `your-own-test-runner`).

## Usage

The simplest usage is simply running the build system; `super+shift+b` and select `Python Tests` from the build system selection drop-down, after using it once you may hit `super+b` to run the default build system. You may also run a specified test class or function by placing the caret at the desired test location prior to running test all placeholders are replaced in `cmd` by the located test and selected text.

## Configuration

By default the command we run is `py.test {filename}::{test_class}::{test_func} -k {selection} --doctest-modules -v`. Let us look at the arguments with more detail:

- `--doctest-modules - ` if no UnitTest class/method given run module unittests
- `-v                - ` verbose test output

Placeholder arguments are optional, and will be cleanly removed where possible:

- `{filename}      - ` test target file
- `{test_class}    - ` test target class
- `{test_func}     - ` test target function/method
- `-k {selection}  - ` use selected text as pattern

You may customize the command in your `project.sublime-project` settings. For example Django's test runner can be run like so:

```json
{
    "build_systems":
    [
        {
            "cmd":
            [
                "python",
                "manage.py",
                "test",
                "--noinput",
                "{filename}:{test_class}.{test_func}",
                "--settings=test_settings"
            ],
            "env":
            {
                "PYTHONPATH": "/home/user/.venvs/project/lib/python2.7/site-packages",
                "REUSE_DB": "1"
            },
            "name": "Django Test",
            "target": "run_python_tests",
            "working_dir": "${project_path}/project/"
        }
    ]
}
```

For more info on the SublimeText build-system configuration see [the unofficial documentation](http://sublime-text-unofficial-documentation.readthedocs.org/en/latest/reference/build_systems/configuration.html).

## Sublime ANSI

This plugin supports passing the command through [ANSIescape](https://github.com/aziz/SublimeANSI) to display ANSI colors in the ST output panel. This will be automatically activated if the plugin is installed.

