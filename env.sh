#! /bin/sh

PAKKU_VERSION := 1.3.2

MC_VERSION := $(shell jq -r '.mc_versions[0]' pakku-lock.json)
FABRIC_VERSION := $(shell jq -r '.loaders.fabric' pakku-lock.json)
FABRIC_INSTALLER_VERSION := 1.1.0

SERVER_NAME := $(shell jq -r .name pakku.json)
SERVER_VERSION := $(shell jq -r .version pakku.json)