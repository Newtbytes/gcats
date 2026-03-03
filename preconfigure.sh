#! /bin/bash

source .venv/bin/activate

if [ -f "pakku.jar" ]; then
    export PAKKU="java -jar pakku.jar"
fi