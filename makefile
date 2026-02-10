include makefile.env

# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

BUILD_DIR = build
SERVER_DIR = $(BUILD_DIR)/server

DATAPACK_SOURCES := $(wildcard datapack/**/*)
RESOURCEPACK_SOURCES := $(wildcard resourcepack/**/*)
RESOURCES_SOURCES := $(DATAPACK_SOURCES) $(RESOURCEPACK_SOURCES)

PAKKU_SOURCES := pakku.json pakku-lock.json $(wildcard .pakku/**/*)
MODPACK_SOURCES := $(RESOURCES_SOURCES) $(PAKKU_SOURCES)

RESOURCES_DATAPACK_DIR := resources/datapack/required
RESOURCES_DATAPACK := $(RESOURCES_DATAPACK_DIR)/${SERVER_NAME}.zip

RESOURCEPACK := $(BUILD_DIR)/${SERVER_NAME}-resourcepack.zip
DATAPACK := $(BUILD_DIR)/${SERVER_NAME}-datapack.zip
MODRINTH_MODPACK := $(BUILD_DIR)/modrinth/${SERVER_NAME}-${SERVER_VERSION}.mrpack
SERVERPACK := $(BUILD_DIR)/serverpack/${SERVER_NAME}-${SERVER_VERSION}.zip

resources $(DATAPACK) $(RESOURCEPACK): $(RESOURCES_SOURCES)
	$(BEET) --log debug

$(RESOURCES_DATAPACK_DIR) $(SERVER_DIR):
	mkdir -p $@

$(RESOURCES_DATAPACK) : $(RESOURCES_DATAPACK_DIR) $(DATAPACK)
	cp $(DATAPACK) $@

$(SERVERPACK) $(MODRINTH_MODPACK): $(PAKKU_SOURCES) | $(RESOURCES_DATAPACK)
	$(PAKKU) export

$(SERVER_DIR)/server.jar: $(SERVERPACK) | $(SERVER_DIR)
	unzip -o $(SERVERPACK) -d $(SERVER_DIR)
	curl -o $(SERVER_DIR)/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

$(SERVER_DIR)/eula.txt: | $(SERVER_DIR)
	cd $(SERVER_DIR) && echo "eula=true" > eula.txt

server: $(SERVER_DIR)/server.jar $(SERVER_DIR)/eula.txt

all: server $(SERVERPACK) $(MODRINTH_MODPACK) $(RESOURCEPACK)

run: server
	cd $(SERVER_DIR) && java -jar server.jar nogui

update:
	$(PAKKU) update -a
	python scripts/list_mods.py pakku-lock.json README.md

test: server
	pytest

clean:
	rm -rf $(BUILD_DIR) resources

.PHONY: resources server all run update test clean
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.INTERMEDIATE: $(RESOURCES_RESOURCEPACK) $(RESOURCES_DATAPACK)
.NOTINTERMEDIATE: $(SERVERPACK) $(MODRINTH_MODPACK) $(RESOURCEPACK)