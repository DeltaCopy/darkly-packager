#!/usr/bin/env bash

dir=$1
tag=$2
repo=$3

test -z "$dir" && exit 1 && test -z "$tag" && exit 1

sha256_sum_tag=$(git -C $dir archive --format tar $tag | sha256sum | awk {'print $1'})
sha256_sum_zst=$(curl -Ls ${repo}/releases/download/${tag}/darkly-${tag#?}-x86_64.pkg.zst | sha256sum | awk {'print $1'})

test -z "$sha256_sum_tag" || test -z "$sha256_sum_zst" && exit 1 || echo "$sha256_sum_tag" && echo "$sha256_sum_zst" && exit 0

