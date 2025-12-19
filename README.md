# Weather data and synthetic sales data Power BI demo

This repository contains a demo project that utilizes Python and Power BI. The project consist of two main components:

- `synda` Python package for generating synthetic sales data with given parameters.
- `powerbi_project` is the directory containing a versioned Power BI project including the semantic model and the report based off of the synthetic data and open data from the Finnish Meteorological Institute (FMI). As a versioned Power BI it doesn't contain the data itself within the scope of this repository. A version of the report with moderate data is available in the Releases section.

Additionally, there are the

- `documentation` directory containing docs related to both the Python package and the Power BI report. Of special 
  note is `power_bi_report_pages.md`, which contains supporting documentation for the Power BI report itself. 
- `tests` directory for the PyTest tests. These are split into unit tests focusing on functionality of individual elements, integration tests focusing on collective functionality of certain systems and finally end-to-end tests that verify the functionality of the package as a whole at a high level.
- `scripts` directory contains is dedicated to any scripts to use with the project. The notebooks directory contains the Jupytext-based .py files which are used to generate their paired notebook files. The notebook files themselves are not tracked in version control.
- `dev_tools` directory contains small helpful developer utilities.
- `config` directory contains csv-formatted config files utilized in the project to enable easy setup and initialization of the models.

The main gist of the project is to use the Python components to fetch weather data from the Finnish Meteorological Institute's open data API, utilize it in synthetic data generation and finally visualize the combined real weather data and synthetic data in Power BI. The `synda` Python package acts as a staging tool and writes the data into Delta tables, while the Power BI report imports the data from the contained `.parquet` files.

## Setting up Synda

For the weather data fetching and synthetic data generation Python package you just need to clone the repository, install the dependencies and utilize the notebooks in the `\scripts` directory. Running the notebooks `run_job_generate_synthetic_data` and `run_job_write_config_to_delta` will produce the needed data files. The `.csv` files in `\config` already contain a ready-to-run setup, but they are easily modifiable the data generation process.

## Getting the report up and running

The report in this repository doesn't contain any data in itself. To get this report working on your system you can first use the included notebook `run_job_generate_synthetic_data` to generate the delta tables (and more importantly the `.parquet` files within.) These tables are created dynamically into a directory called `data`, which is created next to whatever directory this repository root is at.

Then the file sources can be updated in PowerQuery to point at your local files, or wherever they may be.

## Attributions and disclaimers

Weather data source: Finnish Meteorological Institute (FMI), CC BY 4.0, https://creativecommons.org/licenses/by/4.0/

The hourly average temperature and hourly accumulated rain data contained in the F_Sales table has been reproduced as-is based on the data obtained form FMI's Open Data Web API. The weather index value used in this report is calculated based on these values and the visualizations and computations may further process and aggregate the data. 

Other data: Excluding weather data, all data in the released report and the source repository are synthetic. Any person names, company names, product names, or sales figures are entirely fictitious and are used for demonstration purposes only. 

'Deneb: Declarative Visualizations in Power BI': This report contains some visualizations created using the third-party software by Daniel Marsh-Patrick provided under the MIT License, available on the Microsoft AppSource / Power BI Marketplace and https://github.com/deneb-viz/deneb .