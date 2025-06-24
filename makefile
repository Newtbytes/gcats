# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

# default versions
MC_VERSION ?= 1.21.5
FABRIC_VERSION ?= 0.16.14
FABRIC_INSTALLER_VERSION ?= 1.0.3

# Output:
# - build/serverpack/{server name}-{version}.zip
# - build/modrinth/{server name}-{version}.mrpack
build-modpack:
	$(PAKKU) export

# Output:
# Complete server ready to run/test
# - build/server/
build-server:
	make build-modpack
	unzip -o build/serverpack/*.zip -d build/server

	# Download fabric-launcher
	curl -o build/server/fabric-launcher.jar -OJ https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

# Output:
# - build/resourcepack/{server name}-{version}-resourcepack.zip
build-resourcepack:
	$(BEET)

build: build-server build-resourcepack

clean:
	rm -rf build
