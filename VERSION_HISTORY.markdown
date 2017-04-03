# Version History

## 0.2.9

* Updated README to include info on installing punic by homebrew
* Automatically don't stylize output on CI builds.
* Improved `punic version` subcommand.

## 0.2.8

* Ooops. Didn't update __version__.

## 0.2.7

* circleci now runs all unit tests for punic
* Handles situation where mdfind fails to find Xcode
* Lots of other fixes to enable circleci testing

## 0.2.6

* Minor bug fixes
* Fixes empty comments in Cartfiles
* Fixes problems with multiple Xcodes with same version (e.g. beta & release)

## 0.2.5

* More lax handling of semantic versions - better attempts at making non-semantic versions semantic-ish (various tickets).
* Clones and updates now update submodules correctly (which means punic now works with Realm again).
* Updated for python 3.6 (unit tests & travis scripts). Thanks @Caiopia.
* Fix handling of semantic version _with_ identifiers vs ones without (e.g. 1.0-beta vs 1.0). Thanks @leoMehlig.
* Apple TV and Apple Watch platforms added. Thanks @krbarnes and @Caiopia. (Surprised this one slid for so long!)
* xcworkspaces are now supported. Thanks @leoMehlig. (Again this one slid for longer than I expected!)
* `punic version` now reports the latest version found on the Python Cheeseshop (i.e. the version `pip install -U punic` installs)
* No longer assumes there's a 1:1 correspondance between schemes and targets/build products. Now schemes will build all sub-build products. I wish more Xcode projects were set up in this manner.
* Various code tidy-ups and minor bug fixes/improvements.
* Don't fail if a commit referred to by a Cartfile is no longer in a repo (this is usually due to deleted branches). Warn instead.

## 0.2.4

* Fixes #19 - `punic checkout` now "prepares" the project checkout in the same way `punic build` will.
* Fixes #25 - punic would be tricked into trying to build static frameworks (e.g. Facebook's Bolts framework). This would break the dSYM generation code.

## 0.2.3

* Fixes #22 - make the tag -> semantic version parsing more lenient. Previously we'd support only correct semantic versions with an optional "v" prefix. Now the prefix can be anything.
* Fixes #23 - uses lowercase comparisons for project identifiers so that the same dependency cannot be pulled in multiple times because it was specified with different case
* Fixes #24 - branches with a / in them would break `git show`. Now we revparse before git show.
* Other misc bug fixes.

## 0.2.2

* Fixes #18: don't fail `punic search` if github credentials cannot be found. Only side effect is that you cannot perform as many github apis as a non-signed in user. Should not be a problem.
* Fixes serious problem with ~> operator. Previously 1.0 ~> 1.1 would succeed. Not that will fail. Now only 1.0 ~> 1.0.1 will succeed. This was a major bug and difference with Carthage. PLease upgrade to 2.2

## 0.2.1

* Fixes #17 - failing to find projects is a warning not exception.
* In verbose mode if DUMP_CONFIG env is set - dump configuration.

## 0.2.0

* punic is now hosted on the Python Package Index http://pypi.python.org
* `punic search` - search for github repos and automatically append them to your Cartfile.
* Minor bug fixes and merged pull requests

## 0.1.21

* Better filtering of semantic versions in a projects tags. Fixes #14
* Uploaded on https://pypi.python.org/pypi

## 0.1.20

* Fixes #13 - versions with semver identifiers (e.g. `v5.0.0-beta6`) now are parsed and compared correctly.
* Added some more unit tests for non-github project identifiers.

## 0.1.19


* Minor changes to README. Otherwise identical to 0.1.18 (made to combine two branches).

## 0.1.18

* Make sub-project Build symlinks relative (fixes #11)
* `punic init` is back and still as broken as ever.
* Large logging cleanup and bug fix - upshot is `--no-color` works again
* Adds a full `punic update` to test suite.
* Fixes punic on Python 3.5 which was a little bit broken.
* Fixes #8 - show a useful error if user doesn't have graphviz and/or pydotplus installed.

## 0.1.17

* Really fixes problems with ReactiveCocoa
* And in fact everything.
* Do not use 0.1.16 :-)

## 0.1.16

* Import bug fixes.
* Most importantly fixes problems with projects such as ReactiveCocoa. See https://github.com/schwa/punic/commit/75b7372c4926f1b6911a5e0e540d1311acda33e3 for more information.
* Fixes problem with `--platform` switch. 

## 0.1.15

* Fixes bug with platform being overiden if specified in punic.yaml and not command-line.

## 0.1.14

* Minor bug fixes. Thanks to @samsonjs and @Dschee for help.

## 0.1.13

* Removes broken `punic init`. Coming back later.
* Adds more control in `punic version`
* `punic copy_frameworks` strips out Headers, PrivateHeaders and Modules when copying frameworks

## 0.1.12

* Adds `--force` switch to `punic cache publish`.
* Fixes problem with configurations passed on command line
* General bug fixes, cleanup & refactoring.

## 0.1.11

* Adds `skips` section to `punic.yaml`. See README.
* Adds `punic list` command to list all schemes, projects, etc etc.
* Fixes bug with logs directory location.

## 0.1.10

* Fixes problem with --use-ssh

## 0.1.9

* Adds `--use-submodules`.
* Adds `--use-ssh`
* General bug fixes, cleanup & refactoring.

## 0.1.8

* Adds `--dry-run` flag to `build`
* "Library" directory is now `~/Library/Application Support/io.schwa.punic/`
* Fixes problem with "strange" Xcodeproj (e.g. https://github.com/NSProgrammer/ZipUtilities's Xcodeproj)
* General bug fixes, cleanup & refactoring.

## 0.1.7

* Supports `Cartfile.private` files.
* Adds support for `--toolchain` switch.
* General bug fixes, cleanup & refactoring.

## 0.1.6

* General bug fixes, cleanup & refactoring.

## 0.1.5 & Earlier

* Development
