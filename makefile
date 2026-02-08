include makefile.env

# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

BUILD_DIR = build

DATAPACK_SOURCES = $(wildcard datapack/**/*)
RESOURCEPACK_SOURCES = $(wildcard resourcepack/**/*)
RESOURCES_SOURCES = $(DATAPACK_SOURCES) $(RESOURCEPACK_SOURCES)

PAKKU_SOURCES = pakku.json pakku-lock.json $(wildcard .pakku/**/*)
MODPACK_SOURCES = $(RESOURCES_SOURCES) $(PAKKU_SOURCES)

RESOURCEPACK = $(BUILD_DIR)/${SERVER_NAME}-resourcepack.zip
DATAPACK = $(BUILD_DIR)/${SERVER_NAME}-datapack.zip
MODRINTH_MODPACK = $(BUILD_DIR)/modrinth/${SERVER_NAME}-${SERVER_VERSION}.mrpack
SERVERPACK = $(BUILD_DIR)/serverpack/${SERVER_NAME}-${SERVER_VERSION}.zip
SERVER = build/server/

resources $(RESOURCEPACK) $(DATAPACK): $(RESOURCES_SOURCES)
	$(BEET) --log debug

$(SERVERPACK) $(MODRINTH_MODPACK): $(RESOURCEPACK) $(DATAPACK) $(PAKKU_SOURCES)
	mkdir -p resources/resourcepack/required
	mkdir -p resources/datapack/required/

	cp -r $(RESOURCEPACK) resources/resourcepack/required/${SERVER_NAME}.zip
	cp -r $(DATAPACK) resources/datapack/required/${SERVER_NAME}.zip

	$(PAKKU) export

	rm -rf resources

server $(SERVER) $(SERVER)/server.jar: $(SERVERPACK)
	# move serverpack
	unzip -o build/serverpack/*.zip -d $(SERVER)

	# Download fabric-launcher
	curl -o $(SERVER)/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

all: $(SERVER) $(SERVERPACK) $(MODRINTH_MODPACK) $(RESOURCEPACK) $(DATAPACK)

run: $(SERVER)/server.jar
	cd $(SERVER) && echo "eula=true" > eula.txt
	cd $(SERVER) && java -jar server.jar nogui

update:
	$(PAKKU) update -a
	python scripts/list_mods.py pakku-lock.json README.md

test: $(SERVER)
	pytest

clean:
	rm -rf $(BUILD_DIR) resources

.PHONY: server resources build run update test clean
.DEFAULT_GOAL := all
.DELETE_ON_ERROR: