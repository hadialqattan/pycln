# Contributing to Pycln project

A big welcome for considering contributing to make the project better! Have you read the
entire user [documentation](README.md) yet?

## Code of Conduct

Everyone participating in the **Pycln** project, and in particular in the issue tracker,
and pull requests is expected to treat other people with respect. By participating and
contributing to this project, you agree to uphold our
[Code of Conduct](CODE_OF_CONDUCT.md).

## General guidelines

Contributions are made to this repo via Issues and Pull Requests (PRs). A few general
guidelines that cover both:

- Search for existing Issues and PRs before creating your own.
- We work hard to make sure issues are handled in a timely manner but, depending on the
  impact, it could take a while to investigate the root cause. A friendly ping in the
  comment thread to the submitter or a contributor can help draw attention if your issue
  is blocking.

## Issue

**Issues** should be used to report a bug, add a new feature, or discuss potential
changes.

If you find an issue that addresses the problem you're having, please add your own
reproduction information to the existing issue rather than creating a new one. Adding a
[reaction](https://github.blog/2016-03-10-add-reactions-to-pull-requests-issues-and-comments/)
can also help us indicating that a particular problem is affecting more than just the
reporter.

**Good first issues are the issues that you can quickly solve, we recommend you take a
look:**
[Good first issues](https://github.com/hadialqattan/pycln/labels/good%20first%20issue).

## Pull Request (PR)

PRs to our project are always welcome and can be a quick way to get your fix or
improvement slated for the next release. In general, PRs should:

- Only contain changes related to a certain issue/feature.
- Add or edit our tests suite for fixed or changed functionality (if a test suite
  already exists).
- Include documentation on our [README](README.md).

_In case the problem was very clear, you can create a PR directly without opening an
issue._

## Technicalities

In general, we follow the ["fork-and-pull"](https://github.com/susam/gitpr) Git
workflow:

1. Fork the repository to your own Github account.
2. Clone the project to your machine.
3. Create a branch locally.
4. Commit changes to the branch.
5. Follow any formatting and testing guidelines specific to this repo.
6. Push changes to your fork.
7. Open a PR in our repository.

Detailed steps are demonstrated below:

### Fork Repository

[Click to fork Pycln.](https://github.com/hadialqattan/pycln/fork)

### Clone Repository

1. Clone the forked Pycln repo:
   ```bash
   $ git clone https://github.com/<USERNAME>/pycln.git
   ```
2. CD into it:
   ```bash
   $ cd pycln
   ```

### Setup Branch

Create a branch locally:

```bash
$ git checkout -b {branch_name}
```

### Install Pycln Development Requirements

- Install:
  ```bash
  $ ./scripts/dev-install.sh
  ```
- Uninstall (**optional after finishing**):
  ```bash
  $ ./scripts/dev-uninstall.sh
  ```

### Testing

After finishing, you should run the tests by the following command:

```bash
$ ./scripts/tests_runner.sh
```

_Hint: any Pytest arg can be passed directly, for example:_

```bash
$ ./scripts/tests_runner.sh -vv -k TestClassName
```

### Finally, Put Your Signature

After adding a new feature or fixing a bug please:

- Report your changes to [CHANGELOG.md](CHANGELOG.md).
- Write your name, GitHub username, and email on the [AUTHORS.md](AUTHORS.md) file.

## FAQ

### How To Update My Local Forked Repository?

1. Add the remote (the original Pycln repo) and call it `upstream`:
   ```bash
   $ git remote add upstream https://github.com/hadialqattan/pycln.git
   ```
2. Fetch the latests from the `upstream`:
   ```bash
   $ git fetch upstream  # or git fetch --all
   ```
3. Integrate your changes with the fetched data:
   ```bash
   $ git rebase upstream/master
   ```
4. Push your updates to the remote repository. You may need to force the push with
   `--force`:
   ```bash
   $ git push origin {branch_name} --force
   ```

### How Can I See My Doc Updates Locally?

Once you have [npm installed](https://www.npmjs.com/get-npm):

1. Install [docsify-cli](https://www.npmjs.com/package/docsify-cli) via
   [npm](https://www.npmjs.com/) globally:

   ```bash
   $ npm i docsify-cli -g
   ```

2. On the Pycln root directory run:

   ```bash
   $ docsify serve docs/ --open
   ```

### How Can I Run Pycln Scripts Using Windows?

- You can install [Git for Windows](https://gitforwindows.org/) to use the bash
  emulator.
- Or install
  [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/install-win10).
- Or you can perform any script manually by convering it to a Windows commands.

## License

Pycln is MIT licensed, as found in the
[LICENSE](https://github.com/hadialqattan/pycln/tree/master/LICENSE) file.
