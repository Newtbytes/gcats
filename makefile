# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

# Dynamically extract versions from pakku-lock.json
MC_VERSION := $(shell jq -r '.mc_versions[0]' pakku-lock.json)
FABRIC_VERSION := $(shell jq -r '.loaders.fabric' pakku-lock.json)
FABRIC_INSTALLER_VERSION := 1.1.0

# Output:
# - build/resources/GCATs-resourcepack.zip
# - build/resources/GCATs-datapack/
build-beet:
	$(BEET) --log debug

# Output:
# - build/resources/resourcepack/required/GCATs.zip
build-resourcepack: build-beet
	mkdir -p build/resources/resourcepack/required
	mv build/resources/GCATs-resourcepack.zip build/resources/resourcepack/required/GCATs.zip

# Output:
# - build/resources/datapack/required/GCATs/
build-datapack: build-beet
	mkdir -p build/resources/datapack/required
	mv build/resources/GCATs-datapack/ build/resources/datapack/required/GCATs/

# Output:
# - build/serverpack/{server name}-{version}.zip
# - build/modrinth/{server name}-{version}.mrpack
build-modpack: build-resourcepack build-datapack
	$(PAKKU) export

# Output:
# Complete server ready to run/test
# - build/server/
build-server: build-modpack build-datapack
	# move serverpack
	unzip -o build/serverpack/*.zip -d build/server

	cp -r build/resources build/server/resources

	# Download fabric-launcher
	curl -o build/server/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

build: build-server build-resourcepack

test: build-server
	echo "eula=true" > build/server/eula.txt
	cd build/server && echo "stop" | java -jar server.jar nogui

clean:
	rm -rf build

.PHONY: build-modpack build-server build-beet build-resourcepack build-datapack build test clean
.DEFAULT_GOAL := build
