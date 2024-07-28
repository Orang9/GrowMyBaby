# Grow My Baby

This program allows users to view data about their baby, including information about growth and health metrics. It is built using Streamlit and requires a connection to a database to fetch the data.

## Deployment

[Streamlit](https://growmybaby-9pa37bvsxgstijyksgwgr4.streamlit.app/)

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8 or higher
- Streamlit library
- MongoDB Atlas or a local MongoDB instance
- Required Python packages listed in `requirements.txt`
- Poetry installed for dependency management. You can install it using:

  ```sh
  curl -sSL https://install.python-poetry.org | python3 -
  ```

  ### Installation

  Follow these steps to set up and run the program:

  1. Clone the repository (if not already done):
     ```sh
     git clone https://github.com/your-repo/your-baby-data-viewer.git
     cd your-baby-data-viewer
     ```
  3. Set up a virtual environment:
     ```sh
     py -m venv env
     ```
  5. Activate the virtual environment:
     - On Windows:
       ```sh
       .\env\Scripts\activate
       ```
     - On macOS and Linux:
       ```sh
       source env/bin/activate
       ```
  6. Install requirements.txt
     ```sh
       pip install -r requirements.txt
     ``` 
    

    ### Running the Application
  Start the Streamlit application using the following command:
  ```sh
  streamlit run .\streamlit_app.py
  ```
  This will start a local server, and you can view the application in your web browser at http://localhost:8501.

  #### Troubleshooting
  If you encounter any issues, ensure that all dependencies are correctly installed and that you have activated the virtual environment. Also, verify that your database connection settings are correctly configured.

  #### Contributing
  If you wish to contribute to this project, please follow these steps:
  - Fork the repository.
  - Create a new branch (git checkout -b feature-name).
  - Make your changes and commit them (git commit -m 'Add some feature').
  - Push to the branch (git push origin feature-name).
  - Open a pull request.
