install:
	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' Starboard.service
	@sudo cp ./Starboard.service /etc/systemd/system
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' StarboardTimeouts.service
	@sudo cp ./StarboardTimeouts.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@sudo systemctl enable Starboard.service
	@sudo systemctl enable StaroardTimeouts.service
	@echo Done. The services are ready to be started

uninstall:
	@echo Removing systemd service...
	@sudo systemctl disable Starboard.service
	@sudo systemctl disable StarboardTimeouts.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' Starboard.service
	@sudo rm /etc/systemd/system/Starboard.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' StarboardTimeouts.service
	@sudo rm /etc/systemd/system/StarboardTimeouts.service
	@sudo systemctl daemon-reload
	@echo Done.

start:
	@sudo systemctl start Starboard.service
	@sudo systemctl start StarboardTimeouts.service
	@echo Service started

stop:
	@sudo systemctl stop Starboard.service
	@sudo systemctl stop StarboardTimeouts.service
	@echo Service stopped
