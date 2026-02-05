include makefile.env

# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

# Output:
# - build/{SERVER_NAME}-resourcepack.zip
# - build/{SERVER_NAME}-datapack/
build-resources:
	$(BEET) --log debug

# Output:
# - build/serverpack/{SERVER_NAME}-{SERVER_VERSION}.zip
# - build/modrinth/{SERVER_NAME}-{SERVER_VERSION}.mrpack
build-modpack: build-resources env
	mkdir -p resources/resourcepack/required
	mkdir -p resources/datapack/required/

	cp -r build/${SERVER_NAME}-resourcepack.zip resources/resourcepack/required/${SERVER_NAME}.zip
	cp -r build/${SERVER_NAME}-datapack.zip resources/datapack/required/${SERVER_NAME}.zip

	$(PAKKU) export

	rm -rf resources

# Output:
# Complete server ready to run/test
# - build/server/
build-server: build-modpack env
	# move serverpack
	unzip -o build/serverpack/*.zip -d build/server

	# Download fabric-launcher
	curl -o build/server/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

build: build-server

run: build-server
	cd build/server && echo "eula=true" > eula.txt
	cd build/server && java -jar server.jar nogui

test: build-server
	echo "eula=true" > build/server/eula.txt
	cd build/server && echo "stop" | java -jar server.jar nogui

update:
	$(PAKKU) update -a
	python scripts/list_mods.py pakku-lock.json README.md

clean:
	rm -rf build
	rm -rf resources

.PHONY: env build-modpack build-server build-resources build run test clean
.DEFAULT_GOAL := build
