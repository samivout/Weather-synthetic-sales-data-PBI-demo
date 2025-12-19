# Synda

`Synda` is designed as a simple statistical tool for generating synthetic sales data with a focus on aggregate data on a desired timestep. The main idea is to model sales events as nonhomogenous Poisson distributed events. This is handled in two steps. Initially hourly sales are drawn from a homogenous Poisson distribution with a certain expected mean (lambda) value. The nonhomogenous part of the model is introduced via rejecting a fraction of the initially drawn sales. The rejection rate is determined as a function of desired parameters and the implementation details are left for each model class.

 `Synda` is implemented as a Python package utilizing Python version 3.11.x for maximum compatibility with Fabric and Databricks. The virtual environment is managed using Poetry. The current direct dependencies are:
- NumPy (main numerical and array functionality)
- SciPy (scientific and stats functions)
- Pandas (easily maintainbale dataframes)
- Deltalake (simple local management of delta tables)
- PyTest (testing framework)
- PyArrow (explicit backend package for Deltalake)

 Possible future dependencies are:
- PySpark (data output and interfacing with data platforms)
- PyTorch (might be worth considering for machine learning functionality)

## Package structure

The `synda` package is written to function in a class hierarchy at three levels with certain model classes.
- At the highest level is the `SyntheticDataGenerator` class, which manages the whole data generation process.
- A `SyntheticDataGenerator` class
    - manages a collection of concrete implementations of the `BaseSalesLocaleModel`.
    - enables the convenient initialization of the whole class hierarchy.
    - enables the real weather data fetching, synthetic data generation process and collecting the data on all it's subunits in one place.
    - does NOT directly hold any data, but instead is responsible for enabling the fetching of data from its managed locale models.
- A concrete implementation of the `BaseSalesLocaleModel` class
    - manages a collection of concrete implementations of the `BaseSalespersonModel` class
    - manages a single concrete implementations of the `BaseWeatherModel` class.
    - enables generating hourly sales data of the locale according to the model's rules.
    - enables the assignment of the generated sales down to the managed salespeople based on the model's rules.
    - does NOT hold any data directly, but instead is responsible for enabling the fetching of both the weather data and sales data held by its subunits.
- A concrete implementation of the `BaseWeatherModel` class
    - manages the parameters that are needed in that weather model and computes the pleasantness of the weather into a single "weather_index" parameter according to the model's rules.
    - manages the fetching of the weather data over a given timewindow for the given location.
    - holds the timestamped weather data for its location.
- A concrete implementation of the `BaseSalespersonModel` class
    - manages the availability of that salesperson
    - manages how the sales assigned to that salesperson are further assigned down to product IDs.
    - holds the timestamped sales data by product ID for that salesperson.

## The simple models

### The short version

The current set of simple models, i.e `SimpleSalesLocaleModel`, `SimpleWeatherModel` and `SimpleSalespersonModel` handle the synthetic sales generation as follows. The weather model fetches hourly weather data for the given location. The sales locale model then uses a sales_max parameter to draw the hourly baseline number of sales. A fraction of these sales is rejected to emulate a nonhomogenous Poisson process. The rejection rate is modeled as a function of time of day and the weather. The total generated sales are then assigned down to the salespeople according to availability and a performance weight.

### The long version

The salesperson model manages availability by a simple rule based on starting and ending workhours. Given a dataframe with a timestamp columns, it returns a new dataframe that contains a boolean column indicating whether they are available (TRUE) or not (FALSE). Each salesperson has a performance_weight parameter to model variable performance of salespeople. For the simple model this is a static float number with a larger value representing better performance. The model assigns the sales given to it over the given product IDs in an uniform manner.

The weather model fetches hourly weather data for the given location, focusing on an hourly average temperature (°C) and hourly average rainfall (mm). These are then used to compute a weather index ranging from 0.0 — 1.0 with 1.0 representing the ideal weather. The model drops any timestamps that have a NaN in the data fetched from the FMI API.

The sales locale model manages the open hours and days of that locale and when given a dataframe with timestamps, it prunes any timestamps that do not fall into its open times. The initial hourly sales are then drawn from a Poisson distribution with the lambda value being the sales_max parameter. Then a fraction of the sales are rejected based on the multiplicative effect determined by the weather index given by the weather model, and the day time effect, which is modeled as a simple Gaussian distribution centered over the afternoon hours. The resulting hourly sales are then assigned down to the locale's managed salespeople according to their availability at the given timestamp and normalization over the available people's performance_weight parameter.

### Limitations

The single biggest limitation of the simple models is the assumption that a single salesperson can only work at a single location. Enabling multiple locales for a single salesperson would require relatively large modifications to the current implementations.

The second biggest limitation is the generalist approach to the locales' open hours and days, as well as the working hours of a salesperson. These are managed as very simple rules determined by a start and end parameter, creating static time windows for each. An improvement over this model could easily be written by creating more complex rules for the open / working hours of locales / salespeople. Similarly, an easy improvement could be made by creating more complex performance weight rules. For example, this too could be a function of the time of day, as some people are more effective at different times of day.