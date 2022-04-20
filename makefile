install:
	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' Starboard.service
	@sed -i 's|USER|'$(USER)'|g' Starboard.service
	@sudo cp ./Starboard.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@sudo systemctl enable Starboard.service
	@echo Done. The service is ready to be started

uninstall:
	@echo Removing systemd service...
	@sudo systemctl disable Starboard.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' Starboard.service
	@sed -i 's|'$(USER)'|USER|g' Starboard.service
	@sudo rm /etc/systemd/system/Starboard.service
	@sudo systemctl daemon-reload
	@echo Done.

start:
	@sudo systemctl start Starboard.service
	@echo Service started

stop:
	@sudo systemctl stop Starboard.service
	@echo Service stopped
