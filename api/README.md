# Amakin API Docs

# Usage

### Docker

- Copy the sample `example.env` into `.env` and start the project from the root directory using `docker compose up`

- Go to [http://localhost:4000/docs](http://localhost:4000/docs)
- Click on the *Authorize* button and set the value to the API key defined in the `.env` file (e.g., `amakin-api-key-123`)


### Standalone

- Ensure you have Python 3.8+ installed on your machine.
- Create a virtual environment and activate it:
  ```shell
  python -m venv .venv
  # On Windows use 
  .venv\Scripts\activate
  # On macOS use: 
  source .venv/bin/activate  
  ```
- Run the API server:
  ```shell
  ```

### Importing the specs into Postman

- On Postman, import the specs at `http://localhost:4000/openapi.json`
- Select the collection, go to variables and add a variable name `bearerToken` with the value of the API key set in the `.env` file (e.g., `amakin-api-key-123`)

# Project Structure

This API follows the Model-View-Controller (MVC) architectural pattern, a widely-adopted software design pattern that helps organize and structure the codebase of this RESTful API. The project is divided into the following main directories:

- `routes/`: Defines the API endpoints. They also act as the controllers, where all the logic for handling requests and responses are defined. They often perform request validation and send requests to the appropriate model.
- `models/`: Contains the representations for database tables and relationships utilizing SQLModel, which is a library for interacting with SQL databases using SQLAlchemy, the most popular ORM for Python.
- `middlewares/`: Contains functions that process requests before they reach the controllers. These functions perform checks such as validating API keys, adding HTTP headers for CORS, and other necessary pre-processing before the requests are handled by the routes.
- `databases/`: Contains database connections.
- `app.py`: The main entry point for the API.

## Code Editors/IDEs and Code Formatting

- VS Code:
  - Install the [Python extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
  - Install the [Black Formatter extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/):
  - If you're using PyCharm/IntelliJ IDEA, you should be able to use the built-in Black Formatter integration.
