#!/usr/bin/env python

import argparse
import subprocess
import sys
import os
import shutil
import logging
import json
import time
from string import Template

conf = os.curdir + "/conf/packager.json"
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
# 10m timeout
process_timeout = 600

# create console handler and set level to debug
fh = logging.FileHandler("packager.log")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s > %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
fh.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s > %(message)s", "%Y-%m-%d %H:%M:%S"
)
# add formatter to fh
fh.setFormatter(formatter)

# add fh to logger
logger.addHandler(fh)


class TemplateHelper:
    def __init__(self, packages, dist, tag, sha256sums):
        self.packages = packages
        self.dist = dist
        self.tag = tag
        self.sha256sums = sha256sums

    # process template data
    def process_templates(self):
        try:
            if self.dist == "fedora":
                for p in self.packages:
                    # only catch if it is COPR
                    if p["type"] == "COPR":
                        tfile = p["template"]
                        self.path = p["path"]
                        
                        if not os.path.exists(os.path.dirname(self.path)):
                            self.create_output_dir()
                            
                       
                        if os.path.exists(tfile):
                            t = Template(open(tfile).read())
                            with open(self.path, mode="w") as f:
                                f.writelines(
                                    t.substitute(
                                        dict(PKGVER=self.tag.replace("v", "").strip())
                                    )
                                )
                        else:
                            logger.error("Template file {0} is missing".format(tfile))
                            return 1

            if self.dist == "arch":
                for x in self.packages:
                    # make sure to distinguish between the bin and src packages
                    if x["type"] == "AUR":
                        if "-bin" not in x["name"]:
                            sha256sum = self.sha256sums[0].strip()
                        elif "-bin" in x["name"]:
                            sha256sum = self.sha256sums[1].strip()
                        for p in x["paths"]:
                            if "pkgbuild" in p.keys():
                                self.path = p["pkgbuild"]
                                tfile = p["template"]
                                
                                if not os.path.exists(os.path.dirname(self.path)):
                                    self.create_output_dir()

                                if os.path.exists(tfile):
                                    t = Template(open(tfile).read())

                                    with open(self.path, mode="w") as f:
                                        data = {
                                            "PKGVER": self.tag.replace("v", "").strip(),
                                            "SHA256SUM": sha256sum,
                                        }

                                        f.writelines(t.safe_substitute(data))
                                else:
                                    logger.error(
                                        "Template file {0} is missing".format(tfile)
                                    )
                                    return 1
                            if "srcinfo" in p.keys():
                                srcinfofile = p["srcinfo"]
                                tfile = p["template"]

                                if os.path.exists(tfile):
                                    t = Template(open(tfile).read())
                                    with open(srcinfofile, mode="w") as f:
                                        data = {
                                            "PKGVER": self.tag.replace("v", "").strip(),
                                            "SHA256SUM": sha256sum,
                                        }

                                        f.writelines(t.safe_substitute(data))
                                else:
                                    logger.error(
                                        "Template file {0} is missing".format(tfile)
                                    )
                                    return 1

            return 0
        except Exception as e:
            logger.error("Exception raised in process_templates(): {0}".format(e))
            return 1
    
    def create_output_dir(self):
        logger.info("Creating output directory = {0}".format(os.path.dirname(self.path)))
        os.makedirs(os.path.dirname(self.path))
        


class GitHelper:
    def __init__(self, repo, dest, sha256sums_sh):
        self.repo = repo
        self.dest = dest
        self.sha256sums_sh = sha256sums_sh

    def clean_clone_dir(self):
        try:
            if os.path.exists(self.dest):
                shutil.rmtree(self.dest, ignore_errors=False)
        except Exception as e:
            logger.error("Exception raised in clean_clone_dir(): {0}".format(e))
            return 1

    # make sure the user entered a valid tag
    def validate_input_tag(self, input_tag):
        logger.info("Validating user input tag")
        self.clean_clone_dir()
        try:

            cmd = [
                "git",
                "clone",
                self.repo,
                "--depth",
                "1",
                "--branch",
                input_tag,
                self.dest,
            ]

            process = subprocess.Popen(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            process.wait(process_timeout)

            if process.returncode == 0:
                return 0
            else:
                return 1

        except Exception as e:
            logger.error("Exception raised in validate_input_tag(): {0}".format(e))
            return 1

    # run the sh script to generate the sha25sum, using the inbuilt python sha256sum method causes codec errors
    # when traversing through the cloned src code from the git repository
    def get_sha256sums(self, latest_tag):
        logger.info("Getting sha256sum")
        cmd = [self.sha256sums_sh, latest_tag[1:], self.repo]
        try:
            process = subprocess.Popen(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            process.wait(process_timeout)

            if process.returncode == 0:
                return process.stdout.readlines()
            else:
                logger.error("Failed to get sha256sums")
                return 1

        except Exception as e:
            logger.error("Exception raised in get_sha256sums(): {0}".format(e))
            sys.exit(1)

    # clone the git repository, need to generate the sha256sum
    def clone_repo(self):
        clone_cmd = ["git", "clone", "--filter", "tree:0", self.repo, self.dest]
        try:
            self.clean_clone_dir()
            logger.info("Cloning git repository = {0}".format(self.repo))
            process = subprocess.Popen(
                clone_cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            process.wait(process_timeout)

            if process.returncode == 0:
                logger.info("Git clone successful")
                return 0
            else:
                logger.error("Failed to git clone repo")
                logger.error(process.stdout)
                return 1
        except Exception as e:
            logger.error("Exception raised in clone_repo(): {0}".format(e))
            sys.exit(1)

    # get the latest release tag from the git repository
    def get_latest_tag(self):

        logger.info("Getting latest tag")
        cmd = [
            "/usr/bin/git",
            "-c",
            "versionsort.suffix=-",
            "ls-remote",
            "--exit-code",
            "--refs",
            "--sort=version:refname",
            "--tags",
            self.repo,
            "*.*",
        ]

        try:
            process = subprocess.Popen(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            latest_tag = None
            for line in process.stdout:
                latest_tag = line.strip().split("refs/tags/")[1]

            if latest_tag is not None:
                logger.info("Latest tag = {0}".format(latest_tag))
                return latest_tag
            else:
                logger.error("Failed to get latest tag")
                return 1
        except Exception as e:
            logger.error("Exception raised in get_latest_tag(): {0}".format(e))
            sys.exit(1)


def main():

    # check conf file first

    build_repo = None
    clone_dest = None
    dist = None
    sha256sum_sh = None
    template_ret = None
    packages = []

    try:
        if os.path.exists(conf):
            with open(conf, encoding="utf-8") as f:
                contents = json.load(f)

                if contents is not None:
                    build_repo = contents["packager"]["github"]
                    clone_dest = contents["packager"]["clone-dest"]
                    packages = contents["packager"]["packages"]
                    sha256sum_sh = contents["packager"]["sha256sum-sh"]
        else:
            logger.error("The configuration file {0} is missing".format(conf))
            sys.exit(1)
    except Exception as e:
        logger.error("Failed to parse configuration file")
        logger.error("Exception raised in parsing configuration file: {0}".format(e))
        sys.exit(1)

    if (
        build_repo is None
        or clone_dest is None
        or len(packages) == 0
        or sha256sum_sh is None
    ):
        logger.error("Failed to read in configuration file")
        sys.exit(1)

    if not os.path.exists(sha256sum_sh):
        logger.error("Failed to find {0}".format(sha256sum_sh))
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="packager",
        description="Package maintainer",
        epilog="Helper to maintain the Darkly application style AUR / COPR package",
    )

    parser.add_argument("--tag", type=str, help="The Git tag to use - starts with 'v'")
    parser.add_argument(
        "--dist", type=str, help="The package distribution - arch/fedora", required=True
    )

    args = parser.parse_args()

    if args.dist is not None:
        if args.dist == "fedora":
            dist = "fedora"
        elif args.dist == "arch":
            dist = "arch"
        else:
            parser.print_help()
            sys.exit(1)

    logger.info("Generating package for {0}".format(dist.capitalize()))

    git_helper = GitHelper(build_repo, clone_dest, sha256sum_sh)

    if args.tag is None and not str(args.tag).startswith("v"):
        latest_tag = git_helper.get_latest_tag()
    elif str(args.tag).startswith("v"):
        latest_tag = str(args.tag)
        if git_helper.validate_input_tag(latest_tag) == 1:
            logger.error("Invalid tag entered")
            sys.exit(1)
        else:
            logger.info("Valid tag entered")
    else:
        parser.print_help()
        sys.exit(1)

    if dist == "arch":
        if git_helper.clone_repo() == 0:
            # for the tag and precompiled zst asset generated from github actions
            sha256sums = git_helper.get_sha256sums(latest_tag)

            if (
                len(sha256sums) > 0
                and sha256sums != 1
                and "fatal: not a valid object name" not in sha256sums
            ):
                logger.info(
                    "Relase asset (tarball) = {0}/releases/download/{1}.tar.gz | {2}".format(
                        build_repo, latest_tag, sha256sums[0].strip()
                    )
                )
                
                logger.info(
                    "Relase asset (zst) = {0}/releases/download/{1}/darkly-{3}-x86_64.pkg.zst  | {2}".format(
                        build_repo, latest_tag, sha256sums[1].strip(), latest_tag[1:]
                    )
                )
            else:
                logger.error("Failed to get sha256sum of the release tag/asset")
                sys.exit(1)

            th = TemplateHelper(packages, dist, latest_tag, sha256sums)
            template_ret = th.process_templates()
        else:
            logger.error("Git clone failed due to ane error")
            sys.exit(1)
    else:
        th = TemplateHelper(packages, dist, latest_tag, None)
        template_ret = th.process_templates()

    if template_ret != None and template_ret == 0:
        logger.info("Package files updated")
        sys.exit(0)
    else:
        logger.error("Failed to update package files")
        sys.exit(1)


if __name__ == "__main__":
    main()
