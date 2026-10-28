#!/usr/bin/env bash
# polish.sh <in.mp4> <out.mp4> [--draft]   light colour grade + vignette + fine grain over a silent scene clip (Manim / Blender; the web engine is already styled).
set -eu
in="$1"; out="$2"; crf=18; [ "${3:-}" = "--draft" ] && crf=27
ffmpeg -v error -y -i "$in" -vf "eq=saturation=1.12:contrast=1.04,vignette=PI/6,noise=alls=2:allf=t" -c:v libx264 -crf "$crf" -pix_fmt yuv420p -an "$out"
