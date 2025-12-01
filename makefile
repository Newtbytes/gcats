# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

# Dynamically extract versions from pakku-lock.json
MC_VERSION := $(shell jq -r '.mc_versions[0]' pakku-lock.json)
FABRIC_VERSION := $(shell jq -r '.loaders.fabric' pakku-lock.json)
FABRIC_INSTALLER_VERSION := 1.1.0

# Output:
# - build/GCATs-resourcepack.zip
# - build/GCATs-datapack/
build-resources:
	$(BEET) --log debug

# Output:
# - build/serverpack/{server name}-{version}.zip
# - build/modrinth/{server name}-{version}.mrpack
build-modpack: build-resources
	mkdir -p resources/resourcepack/required
	mkdir -p resources/datapack/required/

	cp -r build/GCATs-resourcepack.zip resources/resourcepack/required/GCATs.zip
	cp -r build/GCATs-datapack.zip resources/datapack/required/GCATs.zip

	$(PAKKU) export

	rm -rf resources

# Output:
# Complete server ready to run/test
# - build/server/
build-server: build-modpack
	# move serverpack
	unzip -o build/serverpack/*.zip -d build/server

	# Download fabric-launcher
	curl -o build/server/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

build: build-server

test: build-server
	echo "eula=true" > build/server/eula.txt
	cd build/server && echo "stop" | java -jar server.jar nogui

clean:
	rm -rf build
	rm -rf resources

.PHONY: build-modpack build-server build-resources build test clean
.DEFAULT_GOAL := build
