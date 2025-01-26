# darkly-packager
Helper scripts to maintain the Archlinux and Fedora packages for the QT application style - [Darkly](https://github.com/Bali10050/Darkly)

## Overview

A Python script which generates the package files for AUR and Fedora COPR.

This script was created to save me time and effort manually updating package files.

PKGBUILD and .SRCINFO files used inside the following AUR packages:

- [darkly](https://aur.archlinux.org/packages/darkly)

- [darkly-bin](https://aur.archlinux.org/packages/darkly-bin)

Build spec used inside the following COPR:

- [darkly](https://copr.fedorainfracloud.org/coprs/deltacopy/darkly)

## Usage

<pre>
git clone https://github.com/DeltaCopy/darkly-packager.git
cd darkly-packager
</pre>

<pre>
./packager.py --help
usage: packager [-h] [--tag TAG] --dist DIST

Package maintainer

options:
  -h, --help   show this help message and exit
  --tag TAG    The Git tag to use - starts with 'v'
  --dist DIST  The package distribution - arch/fedora

Helper to maintain the Darkly application style AUR / COPR package
</pre>

> [!NOTE]
> If `--tag` is not provided then the latest release tag is used

`--dist` is required and the only accepted arguments is 'arch' or 'fedora'

An output directory is created and stores the newly generated package files.

The location can be controlled via a JSON configuration file.

### Configuration file

Inside conf directory a file called `packager.json`

Default settings shown below.

```json
{
    "packager": {
        "github": "https://github.com/Bali10050/Darkly",
        "clone-dest": "/tmp/Darkly",
        "sha256sum-sh": "utils/sha256sums.sh",
        "packages": [
            {
                "name": "darkly",
                "type": "AUR",
                "paths": [
                    {
                        "pkgbuild": "output/AUR/darkly/PKGBUILD",
                        "template": "templates/AUR/darkly/PKGBUILD.template"
                    },
                    {
                        "srcinfo": "output/AUR/darkly/.SRCINFO",
                        "template": "templates/AUR/darkly/.SRCINFO.template"
                    }
                ]
            },
            {
                "name": "darkly-bin",
                "type": "AUR",
                "paths": [
                    {
                        "pkgbuild": "output/AUR/darkly-bin/PKGBUILD",
                        "template": "templates/AUR/darkly-bin/PKGBUILD.template"
                    },
                    {
                        "srcinfo": "output/AUR/darkly-bin/.SRCINFO",
                        "template": "templates/AUR/darkly-bin/.SRCINFO.template"
                    }
                ]
            },
            {
                "name": "darkly-copr",
                "type": "COPR",
                "path": "output/COPR/specs/darkly.spec",
                "template": "templates/COPR/darkly.spec.template"
            }
        ]
    }
}
```

> [!NOTE]
> `utils/sha256sums.sh` contains a bash script which calls `sha256sum` on the cloned Darkly git repository as well as on the release .zst file asset created from GitHub actions over on https://github.com/Bali10050/Darkly/releases. This is required for the Archlinux AUR based packages.