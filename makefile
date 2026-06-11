include makefile.env

# default pakku/beet commands
PAKKU ?= pakku
BEET ?= beet

BUILD_DIR := build
SERVER_DIR := $(BUILD_DIR)/server
SRC_DIR := src
EXTERN_DIR := extern
EXTERN_DATAPACK_DIR := $(EXTERN_DIR)/datapack

SERVER_ICON := $(SRC_DIR)/server-icon.png
DATAPACK_SOURCES := $(wildcard $(SRC_DIR)/datapack/**/*)
RESOURCEPACK_SOURCES := $(wildcard $(SRC_DIR)/resourcepack/**/*)
RESOURCES_SOURCES := $(DATAPACK_SOURCES) $(RESOURCEPACK_SOURCES) $(SRC_DIR)/beet.yml $(SERVER_ICON)
EXTERN_DATAPACK_SOURCES := $(wildcard $(EXTERN_DATAPACK_DIR)/**/*)

PAKKU_SOURCES := $(SRC_DIR)/pakku.json $(SRC_DIR)/pakku-lock.json $(wildcard $(SRC_DIR)/.pakku/**/*)
# TODO: add SERVER_ICON here if it ever is use in the modpack export
MODPACK_SOURCES := $(RESOURCES_SOURCES) $(PAKKU_SOURCES)

SCRIPTS_SOURCES := $(wildcard scripts/**/*.py) requirements.txt
TESTS_SOURCES := $(wildcard tests/**/*.py) requirements.txt

RESOURCES_DATAPACK_DIR := resources/datapack/required
RESOURCES_RESOURCEPACK_DIR := resources/resourcepack/required
RESOURCES_DATAPACK := $(RESOURCES_DATAPACK_DIR)/${SERVER_NAME}-datapack.zip
RESOURCES_RESOURCEPACK := $(RESOURCES_RESOURCEPACK_DIR)/${SERVER_NAME}-resourcepack.zip

RESOURCEPACK := $(BUILD_DIR)/${SERVER_NAME}-resourcepack.zip
DATAPACK := $(BUILD_DIR)/${SERVER_NAME}-datapack.zip
MODRINTH_MODPACK_DIR := $(BUILD_DIR)/modrinth
SERVERPACK_DIR := $(BUILD_DIR)/serverpack
MODRINTH_MODPACK := $(MODRINTH_MODPACK_DIR)/${SERVER_NAME}-${SERVER_VERSION}.mrpack
SERVERPACK := $(SERVERPACK_DIR)/${SERVER_NAME}-${SERVER_VERSION}.zip

resources $(DATAPACK) $(RESOURCEPACK): $(RESOURCES_SOURCES)
	$(BEET) --project src --set output='../build' --log debug

$(RESOURCES_DATAPACK_DIR) $(SERVER_DIR) $(SERVERPACK_DIR) $(MODRINTH_MODPACK_DIR):
	mkdir -p $@

$(RESOURCES_DATAPACK) : $(RESOURCES_DATAPACK_DIR) $(DATAPACK)
	cp $(DATAPACK) $@

$(RESOURCES_DATAPACK_DIR)/.extern: $(EXTERN_DATAPACK_SOURCES)
	cp -r $(EXTERN_DATAPACK_DIR)/*.zip $(RESOURCES_DATAPACK_DIR)
	touch $@

$(SRC_DIR)/$(SERVERPACK) $(SRC_DIR)/$(MODRINTH_MODPACK): $(PAKKU_SOURCES) | $(RESOURCES_DATAPACK) $(RESOURCES_DATAPACK_DIR)/.extern
	$(PAKKU) --working-path=src export

$(SERVERPACK) $(MODRINTH_MODPACK) : $(SRC_DIR)/$(SERVERPACK) $(SRC_DIR)/$(MODRINTH_MODPACK) $(SERVERPACK_DIR) $(MODRINTH_MODPACK_DIR)
	mv src/$@ $@

$(SERVER_DIR)/server.jar: $(SERVERPACK) | $(SERVER_DIR)
	rm -r $(SERVER_DIR)
	unzip -o $(SERVERPACK) -d $(SERVER_DIR)
	curl -o $(SERVER_DIR)/server.jar https://meta.fabricmc.net/v2/versions/loader/$(MC_VERSION)/$(FABRIC_VERSION)/$(FABRIC_INSTALLER_VERSION)/server/jar

$(SERVER_DIR)/eula.txt: | $(SERVER_DIR)
	cd $(SERVER_DIR) && echo "eula=true" > eula.txt

server: $(SERVER_DIR)/server.jar $(SERVER_DIR)/eula.txt

all: server $(SERVERPACK) $(MODRINTH_MODPACK) $(RESOURCEPACK)

run: server
	cd $(SERVER_DIR) && java -jar server.jar nogui

update: $(SCRIPTS_SOURCES) $(PAKKU_SOURCES)
	$(PAKKU) update -a
	python scripts/list_mods.py pakku-lock.json README.md

test: server $(TESTS_SOURCES)
	pytest -s

clean:
	rm -rf $(BUILD_DIR) src/$(BUILD_DIR) resources

.PHONY: resources server all run update test clean
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.INTERMEDIATE: $(RESOURCES_RESOURCEPACK) $(RESOURCES_DATAPACK)
.NOTINTERMEDIATE: $(SERVERPACK) $(MODRINTH_MODPACK) $(RESOURCEPACK)