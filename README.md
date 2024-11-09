# Transfers Project Documentation

## Overview
The "Transfers Project" is a data-driven application designed to analyze and manage player transfers, team contracts, and tactical configurations. This documentation provides an overview of the file structure, dependencies, and instructions on how to set up and run the project components.

---

## Project File Structure

### 1. **app/**

   - **Description**: Contains the code for the Streamlit web application.
   - **Dependencies**: Requires the installation of libraries specified in the `requirements.txt` file and a Python environment.
   - **How to Run**: 
     ```bash
     streamlit run app/app.py
     ```

   - **Content**:
     - `app.py`: Main application file, serving as the entry point for the Streamlit web interface.

### 2. **data/**

   - **Description**: Contains the CSV file with initial project data.
   - **Future Plans**: In future iterations, this folder will be replaced by a database connection using SQL to ensure real-time and scalable data management.

### 3. **research/**

   - **Description**: Contains Jupyter Notebook files with all the analysis conducted to build and validate the app and project. This folder serves as the research and prototyping section of the project.
   - **Content**: Includes notebooks documenting analyses, data exploration, and methodology for decision-making in the app.

### 4. `contracts.py`

   - **Description**: Handles player contract data management.
   - **Run Command**:
     ```bash
     python contracts.py <parameter>
     ```
   - **Parameters**:
     - `update`: Add new data to player contracts.
     - `populate`: Fill the player contract database from scratch.

### 5. `squads.py`

   - **Description**: Manages team squad information, including player rosters and additions of new leagues.
   - **Run Command**:
     ```bash
     python squads.py <parameter>
     ```
   - **Parameters**:
     - `update`: Add new data to squad information.
     - `populate`: Populate the squad database from scratch.
     - `new_leagues`: Adds new leagues to the squad data (exclusive to `squads.py`).

### 6. `tactics.py`

   - **Description**: Analyzes team tactical configurations, including formations and in-game strategies.
   - **Run Command**:
     ```bash
     python tactics.py <parameter>
     ```
   - **Parameters**:
     - `update`: Add new tactical data.
     - `populate`: Populate the tactics database from scratch.

### 7. `transfers.py`

   - **Description**: Manages player transfer history and data updates.
   - **Run Command**:
     ```bash
     python transfers.py <parameter>
     ```
   - **Parameters**:
     - `update`: Add new transfer data.
     - `populate`: Populate the transfer database from scratch.

---

## Dependencies

- Ensure Python is installed on your machine.
- Required libraries are listed in `requirements.txt`. Install them by running:
  ```bash
  pip install -r requirements.txt
  ```

---

## Notes
- **Data Updates**: When running `.py` files with the `update` parameter, ensure the data source is accessible and up-to-date.
- **Database Integration**: In future versions, the project will transition to SQL-based database connectivity, enhancing data access and scalability.

---
## Database Setup

For the "Transfers Project" to function with a SQL database in place of CSV files, a suitable database server must be created and configured. This database will store data related to player transfers, contracts, squads, and tactical information, allowing for efficient updates and queries.

### Options for Creating the Database
There are several options for setting up the SQL database. You may choose a local or cloud-based SQL server, depending on your requirements and budget:

1. **Paid Cloud-Based SQL Services**:
   - **Azure SQL Database**: Azure provides fully managed SQL databases with scalability and high availability. This is a paid option, ideal for production-grade applications.
   - **Amazon RDS (Relational Database Service)**: AWS offers managed SQL databases for MySQL, PostgreSQL, and other engines. It’s reliable and scalable for growing data needs.
   - **Google Cloud SQL**: Another reliable cloud database option supporting MySQL, PostgreSQL, and SQL Server.

   For these options, you will need to:
   - Set up a database instance through your chosen provider’s console.
   - Configure security settings, including network access and authentication.
   - Obtain the database connection details, including hostname, port, database name, user, and password.