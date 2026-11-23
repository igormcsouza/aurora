#!/usr/bin/env bash
# loudnorm.sh <in> <out> [LUFS=-14] [TP=-2]   two-pass EBU R128 normalisation (measure, then apply with the measured values; video stream copied).
# Use it once on the final mix; the draft can use the same script with -16.
set -eu
in="$1"; out="$2"; I="${3:--14}"; TP="${4:--2}"; LRA=11
m=$(ffmpeg -hide_banner -nostats -i "$in" -vn -af "loudnorm=I=$I:TP=$TP:LRA=$LRA:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$m" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
ffmpeg -v error -y -i "$in" -af "loudnorm=I=$I:TP=$TP:LRA=$LRA:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true" -c:v copy -c:a aac -b:a 192k -ar 48000 "$out"
