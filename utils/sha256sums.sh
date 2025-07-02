#!/usr/bin/env bash

version=$1
repo=$2

test -z "$repo" || test -z "$version" && exit 1

#sha256_sum_tag=$(git -C $dir archive --format tar $tag | sha256sum | awk {'print $1'})
sha256_sum_tar=$(curl -Ls ${repo}/archive/refs/tags/${version}.tar.gz | sha256sum | awk {'print $1'})
sha256_sum_zst=$(curl -Ls ${repo}/releases/download/${version}/darkly-${tag#?}-x86_64.pkg.zst | sha256sum | awk {'print $1'})

test -z "$sha256_sum_tar" || test -z "$sha256_sum_zst" && exit 1 || echo "$sha256_sum_tar" && echo "$sha256_sum_zst" && exit 0

