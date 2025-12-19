# Power BI report

The Weather and synthetic sales data demo report utilizes the dataset output by the associated `synda` Python packgage. The package stores into delta tables all the relevant data for the model:
- Weather data from the FMI API.
- Synthetic sales data generated against the weather data based on the package's model rules and parameters.
- Location data
- Salesperson data
- Product data
- Product category data
- Product location data

The main purpose of the report is to enable the observations and analysis on sales patterns over time and over varying weather conditions. The report visuals and slicers are designed to enable relatively deep observations on the data in a user-friendly fashion. 

## Data ingestion

For the local / Power BI Service version of the report, the data is utilized in Import Mode by reading the plain `.parquet` files. The weather data and sales data are merged into a single table in the Semantic Model. Furthermore, the full datetime timestamp column is split into separate date and time columns in the Semantic Model.

The weather data is merged into the sales data table to make the model be focused on a single fact table. This causes small data duplication on the weather data due to the salesperson and product dimensions, but Vertipaq should handle the compression well enough.

## Special remarks on the report design

This section lists any special noteworthy remarks, at least through the eyes of a fresh Power BI developer, about the report design.

### Semantic model

The semantic model follows a standard star-schema with dimension tables being linked by one-to-many relationships to the main fact table. The main fact table has one special feature in that it consists of both the sales data and weather data. I elected to merge the weather data into the sales data despite the duplicate dimensions from salespeople and products for each location. I found that this resulted in easier DAX expressions and filtering than storing them to a separate table as one of the main analysis subjects in the report is how the sales are related to weather conditions.

### Calculation groups

In many measures I ran into the issue of having copy-pasted the exact same filter pattern over binned data for an underlying measure. The software developer in me wanted to find a way to centralize the definition of this recurring filter. The solution came in the form of calculation groups, which allow defining a filter pattern where the measure it is used on is left as a parameter. Then in the report a developer can call within a `CALCULATE` function the measure the need and then use the calculation group's calculation item to utilize the now reusable filter.

A concrete example follows. The measure `MeanHourOfSalesByWeatherBins` computes for each defined weather index bin a mean hour of sales, i.e. a central hour at which sales are likely to occur within a particular range of weather conditions. The regular measure is expressed as

```
MeanHourOfSalesByWeatherBins = 
VAR SelectedBins =
    SUMMARIZE (
        VALUES ( WeatherIndexBins ),
        WeatherIndexBins[BinStart],
        WeatherIndexBins[BinEnd]
    )
RETURN
CALCULATE (
    [HourOfSaleMean],
    FILTER (
        sales_data,
        -- weather index falls into ANY selected bin
        SUMX (
            SelectedBins,
            IF (
                sales_data[weather_index] > WeatherIndexBins[BinStart] &&
                sales_data[weather_index] <=  WeatherIndexBins[BinEnd],
                1,
                0
            )
        ) > 0
    )
)
```

In here the recurring pattern for filtering based on the weatehr index bins are the definition of the `SelectedBins` variable, and what is utilized inside the `FILTER` call. These recurring patterns can be separated into a calculation item as

```
WeatherIndexBinFilter = 

VAR SelectedBins =
    SUMMARIZE (
        VALUES ( WeatherIndexBins ),
        WeatherIndexBins[BinStart],
        WeatherIndexBins[BinEnd]
    )

VAR WeatherFilter =
    FILTER (
        sales_data,
        SUMX (
            SelectedBins,
            IF (
                sales_data[weather_index] > WeatherIndexBins[BinStart] &&
                sales_data[weather_index] <= WeatherIndexBins[BinEnd],
                1,
                0
            )
        ) > 0
    )

RETURN
    CALCULATE (
        SELECTEDMEASURE(),
        WeatherFilter
    )
```

Here the `SELECTEDMEASURE()` is a special DAX function that acts as a placeholder for any measure one wishes to use this filter upon. With this pattern the original measure can be reduced to

```
MeanHourOfSalesByWeatherBins = 
CALCULATE (
    [HourOfSaleMean],
    WeatherIndexFilterGroup[Calculation group column] = "WeatherIndexBinFilter"
)
```

One only need to refer to the specific calculation group (named as WeatherIndexFilterGroup in this case) and the specific calculation item in that group (named as WeatherIndexBinFilter in this case).

#### Pros
- Centralized management of a recurring expression.
- Reduced complexity of DAX expressions utilizing that calculation item expression.
- Affects all measures. This means that if one wishes to exclude measures from calculation groups, exclusion or inclusion must be done either by manual IF or SWITCH cases (I don't recommend this) or a table containing names of measures and checking whether the measure name is in there or not (the approach I'd recommend)

#### Cons

- Introducing calculation groups requires disabling implicit measures. This means that one cannot drop a data column into a visual as is and then choosing a summarization method from the format pane. (Though through the eyes of a software developer this is not a bad thing.)
- Some Power BI developers might be unfamiliar with calculation groups.

### Deneb visuals

The third-party Deneb visuals act as a tool to define visuals in JSON format using the Vega or Vega-lite languages. These languages have relatively good documentation online and there are plenty of examples at varying types and complexities.

For example the 2D histgram heatmap visual in this report was built using Vega, enabling full interactivity with Power BI and resulting in a visual that simply wouldn't have been possible via native means.

#### Pros
- Enables visuals that simply are not possible in native Power BI.
- JSON format allows for easy copy-pasting of visual definitions.

#### Cons
- Requires some learning of the Vega / Vega-lite, which is likely unfamiliar to most Power BI developers.
- Requires a third-party visual (though it is one certified by Microsoft.)
- Vega-lite specifically doesn't allow deep interactivity similar to native visuals, full Vega is required for that.