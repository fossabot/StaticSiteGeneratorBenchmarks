#!/bin/bash

hyperfine --min-runs 5 $build_command

echo $build_command


sleep 1000

done
